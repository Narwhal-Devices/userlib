from blacs.tab_base_classes import Worker
import labscript_utils.h5_lock, h5py
import zprocess
import time
import numpy as np
import labscript_utils.properties
from labscript_utils.connections import _ensure_str
import ndpulsegen
import queue
import portalocker
import tempfile
import os


#Temproary
import inspect

class NarwhalDevicesPulseGeneratorWorker(Worker):
    # See phil's thesis p151
    def init(self):
        # Once off device initialisation code called when the
        # worker process is first started .
        # Usually this is used to create the connection to the
        # device and/or instantiate the API from the device
        # manufacturer
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.init')
        # Connect to pulse generator and save device info
        self.pg = ndpulsegen.PulseGenerator()

        # ndpulsegen/comms.py hogs all the serial stuff when it is trying to connect. If two Pulse generators do this at the same time
        # they can block eache other. This implements a lock so only one can attempt to connect at a time.
        temp_dir = tempfile.gettempdir()
        lock_file_path = os.path.join(temp_dir, 'NDPG_serial_connection.lock')
        with portalocker.Lock(lock_file_path, timeout=10):
            self.pg.connect(self.serial_number)


        self.pg.write_echo(b'N')
        self.device_info = self.pg.msgin_queues['echo'].get()
        self.device_info['comport'] = self.pg.ser.port

        # Deliberatly don't change current settings. Will allow BLACS to crasha nd restart without affecting a running run

        # Waits and waitmonitor related stuff
        self.all_waits_finished = zprocess.Event("all_waits_finished", type="post")
        self.wait_durations_analysed = zprocess.Event(
            "wait_durations_analysed", type="post"
        )
        self.wait_completed = zprocess.Event("wait_completed", type="post")
        self.current_wait = 0
        self.wait_table = None
        self.measured_waits = None
        self.wait_timeout = None
        self.h5_file = None
        self.started = False
        self.timeout_time = None

        # Misc other stuff 
        self.cease_rapid_timer_status_checks_in_blacs_tabs = False

    def start_run(self):
        # method for starting the shot via a software trigger to the device.
        # The method name and return values should match those used in the 
        # associated BLACS GUI methods (which can be anything the developer wishes).
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.start_run')

        # I need to figure out if this is only called for the master pseudoclock. If is is not called for the slaves, then I need to set software_run_enable=True
        # at the end of the transition_to_buffered function.
        self.started = True
        self.pg.write_action(trigger_now=True)

    def get_device_info(self):
        # This is called only once by blacs_tabs.py so it can display the hardware/firmware versions etc
        return self.device_info

    def check_status(self):
        # method for checking whether the shot has completed.
        # The method name and return values should match those used in the 
        # associated BLACS GUI methods (which can be anything the developer wishes).
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.check_status')
        # I think I can return the full device status here, and I can choose what will be run in the main process (to update gui elements for example)
        # print_calling_chain()
        # but I don't know how often this will be called.
        '''But I think this is called very offen during a run. So I could just always have the "notigy on run finished" setting True, and listen
        for that (and everything else) and then return that as well as everything else'''
        state_queue = self.pg.msgin_queues['devicestate']
        powerline_state_queue = self.pg.msgin_queues['powerlinestate']
        state_extras_queue = self.pg.msgin_queues['devicestate_extras']
        #Empty the state queues incase there is old data in them
        state_queue.queue.clear()
        powerline_state_queue.queue.clear()
        state_extras_queue.queue.clear()
        #request the state
        self.pg.write_action(request_state=True, request_powerline_state=True, request_state_extras=True)
        try:
            state = state_queue.get(timeout=0.1)
        except queue.Empty as ex:
            state = None
        try:
            powerline_state = powerline_state_queue.get(timeout=0.1)
        except queue.Empty as ex:
            powerline_state = None
        try:
            state_extras = state_extras_queue.get(timeout=0.1)
        except queue.Empty as ex:
            state_extras = None
        # Check for a notification. We mainly want to know if finished=True
        # Lots of notifications might possibly be sent, and any of them may contain a Finished=True. For now, just send them all.
        notifications = []
        try:
            while True:
                notifications.append(self.pg.msgin_queues['notification'].get(block=False))
        except queue.Empty as ex:
            pass
        pg_comms_in_errors = [] 
        try:
            while True:
                pg_comms_in_errors.append(self.pg.msgin_queues['error'].get(block=False))
        except queue.Empty as ex:
            pass
        bytesdropped = [] 
        try:
            while True:
                bytesdropped.append(self.pg.msgin_queues['bytes_dropped'].get(block=False))
        except queue.Empty as ex:
            pass
        # Need a way to tell the blacs_tabs.py to stop the rapid statis checks if the main abort button is pressed.
        if self.cease_rapid_timer_status_checks_in_blacs_tabs:
            self.cease_rapid_timer_status_checks_in_blacs_tabs = False
            cease_rapid_status_checks = True
        else:
            cease_rapid_status_checks = False

        # Check notifications for addresses corresponding to waits. Yes, this is more complex than it needs to be.
        if (self.started and self.wait_table is not None and self.current_wait < len(self.wait_table)):
            for notification in notifications:
                if notification['address_notify']:
                    address = notification['address']
                    if address in self.wait_start_instructions:
                        self.wait_start_instructions[address]['run_time'] = notification['run_time']
                        self.timeout_time = time.time() + self.wait_start_instructions[address]['wait_timeout']
                        self.timeout_address = address
                    if address in self.wait_end_instructions:
                        wait_start_instruction = self.wait_start_instructions[self.wait_end_instructions[address]['start_address']]
                        wait_duration = notification['run_time'] - wait_start_instruction['run_time'] - wait_start_instruction['instruction_duration']
                        self.measured_waits[self.current_wait] = wait_duration*10E-9
                        # Inform any interested parties that a wait has completed:
                        self.wait_completed.post(self.h5_file, data=_ensure_str(self.wait_table[self.current_wait]["label"]),)
                        self.current_wait += 1
                        self.timeout_time = None

        if self.timeout_time is not None and time.time() >= self.timeout_time:
            # waiting for too long, restart the pulse generator
            self.timeout_time = None
            state = self.pg.get_state() # Try and avoid the race condition by looking at the state imeadiately before retriggering
            if state['running'] == False and state['current_address'] == self.timeout_address:
                self.pg.write_action(trigger_now=True)
                self.wait_timeout[self.current_wait] = True
            
        return state, powerline_state, state_extras, notifications, pg_comms_in_errors, bytesdropped, cease_rapid_status_checks


    def shutdown(self):
        # Once off device shutdown code called when the
        # BLACS exits
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.shutdown')
        pass
        

    def program_manual(self , front_panel_values):
        # Update the output state of each channel using the values
        # in front_panel_values ( which takes the form of a
        # dictionary keyed by the channel names specified in the
        # BLACS GUI configuration
        # return a dictionary of coerced / quantised values for each
        # channel , keyed by the channel name (or an empty dictionary )
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.program_manual')
        self.pg.write_static_state([val for val in front_panel_values.values()])
        return {}

    def transition_to_buffered(self, device_name, h5file, initial_values, fresh):
        # Access the HDF5 file specified and program the table of
        # hardware instructions for this device .
        # Place the device in a state ready to receive a hardware
        # trigger (or software trigger for the master pseudoclock )
        #
        # The current front panel state is also passed in as
        # initial_values so that the device can ensure output
        # continuity up to the trigger .
        #
        # The fresh keyword indicates whether the entire table of
        # instructions should be reprogrammed (if the device supports
        # smart programming )
        # Return a dictionary , keyed by the channel names , of the
        # final output state of the shot file . This ensures BLACS can
        # maintain output continuity when we return to manual mode
        # after the shot completes .
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.transition_to_buffered')

        self.started = False    # Shouldn't be needed,, but does no harm

        initial_channel_state = np.zeros(24, dtype=np.int8)
        for channel_label, channel_state in initial_values.items():
            channel = int(channel_label.split()[1])
            initial_channel_state[channel] = int(channel_state)
        
        # needed for saving data at the end of the run
        self.h5_file = h5file
        with h5py.File(h5file, 'r') as hdf5_file:
            # device_properties = labscript_utils.properties.get(hdf5_file, device_name, 'device_properties')
            # self.is_master_pseudoclock = device_properties['is_master_pseudoclock']
            # self.stop_time = device_properties.get('stop_time', None) # stop_time may be absent if we are not the master pseudoclock

            # Note that this get() method needs the actual open hdf5_file object, not the directory of the h5file, which is what is passed into the transition_to_buffered method
            self.device_properties = labscript_utils.properties.get(hdf5_file, device_name, "device_properties")

            group = hdf5_file[f'devices/{device_name}']
            pulse_program = group['PULSE_PROGRAM'][:]
            self.is_master_pseudoclock = self.device_properties["is_master_pseudoclock"]

            # If this device is being used as the wait monitor, set up required stuff to record waits
            waits_dset = hdf5_file["waits"]
            acquisition_device = waits_dset.attrs["wait_monitor_acquisition_device"]
            timeout_device = waits_dset.attrs["wait_monitor_timeout_device"]

            is_wait_monitor = (acquisition_device == "%s_internal_wait_monitor_outputs" % device_name 
                               and timeout_device == "%s_internal_wait_monitor_outputs" % device_name
                               and len(waits_dset) > 0)
                                    

            if is_wait_monitor:
                self.wait_table = waits_dset[:]
                self.measured_waits = np.zeros(len(self.wait_table))
                self.wait_timeout = np.zeros(len(self.wait_table), dtype=bool)
            else:
                # This device doesn't need to worry about looking at waits
                self.wait_table = (None)  
                self.measured_waits = None
                self.wait_timeout = None

            self.wait_start_instructions = {}
            self.wait_end_instructions = {}
            self.current_wait = 0


            # It is not required that all channels be assigned in the labscript file. Any that aren't, keep them at the value on the GUI
            instruction_0_channel_state = pulse_program[0]['channel_state']
            unspecified_channels_index = instruction_0_channel_state == -1
            unspecified_channels_state = initial_channel_state[unspecified_channels_index]
            
            wait_idx = 0
            instructions = []
            for instruction in pulse_program:

                #Any unasigned channels get the value on the GUI
                channel_state = instruction['channel_state']
                channel_state[unspecified_channels_index] = unspecified_channels_state

                encoded_instruction = ndpulsegen.encode_instruction(address=instruction['address'], duration=instruction['duration'], 
                                                            state=channel_state, goto_address=instruction['goto_address'], 
                                                            goto_counter=instruction['goto_counter'], stop_and_wait=instruction['stop_and_wait'], 
                                                            hardware_trig_out=instruction['hardware_trig_out'], notify_computer=instruction['notify_computer'], 
                                                            powerline_sync=instruction['powerline_sync'])
                instructions.append(encoded_instruction)

                # For stop and wait instructions, record the address of both the wait_start instruction, and the wait_end instruction (which is probably just +1)
                if is_wait_monitor and instruction['stop_and_wait']:
                    self.wait_start_instructions[instruction['address']] = {'wait_index':wait_idx, 
                                                                            'instruction_duration':instruction['duration'],
                                                                            'wait_timeout':self.wait_table[wait_idx][2] + instruction['duration']*10E-9}
                    if instruction['goto_counter'] == 0:
                        end_address = instruction['address'] + 1
                    else:
                        end_address = instruction['goto_address']
                    self.wait_end_instructions[end_address] = {'start_address':instruction['address']}
                    wait_idx +=1 
                
            final_instr = pulse_program[-1]

        # Just used to confirm the run has finished when transitioning back to manual
        self.final_instruction_address = final_instr['address'] 
        
        # blacs requires the expected final state to be returned from this function
        final_values = {}
        for channel, channel_state in enumerate(final_instr['channel_state']):
            final_values[f'channel {channel}'] = channel_state
        

        # Since the Pulse Generator could technically be running (if, for example, someone was playing around with the manual mode)
        # We reset it so it is in a known state. It does no harm to be safe.
        self.pg.write_device_options(accept_hardware_trigger='never')
        self.pg.write_action(reset_run=True)

        self.pg.write_instructions(instructions)
        self.pg.write_powerline_trigger_options(trigger_on_powerline=self.device_properties["trigger_on_powerline"], powerline_trigger_delay=int(np.round(self.device_properties["powerline_trigger_delay"]/10E-9)))

        # The main difference (so far) is that the master pseudoclock has its software_enable set to false, to enforce it waiting for a software trigger (ignore any hardware triggers it might recieve)
        # Slave pseudoclocks must be armed and ready to respond to hardware triggers
        if self.is_master_pseudoclock:
            self.pg.write_device_options(final_address=final_instr['address'], run_mode='single', accept_hardware_trigger='single_run', trigger_out_length=int(np.round(self.device_properties["trigger_out_length"]/10E-9)), trigger_out_delay=int(np.round(self.device_properties["trigger_out_delay"]/10E-9)), notify_on_main_trig_out=True, notify_when_run_finished=True, software_run_enable=False)
        else:
            self.started = True
            self.pg.write_device_options(final_address=final_instr['address'], run_mode='single', accept_hardware_trigger='single_run', trigger_out_length=int(np.round(self.device_properties["trigger_out_length"]/10E-9)), trigger_out_delay=int(np.round(self.device_properties["trigger_out_delay"]/10E-9)), notify_on_main_trig_out=True, notify_when_run_finished=True, software_run_enable=True)
        return final_values


    def transition_to_manual(self):
        """Transition the NDPG back to manual mode from buffered execution at
        the end of a shot.

        Returns:
            bool: `True` if transition to manual is successful.
        """

        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.transition_to_manual')
        self.started = False
        with h5py.File(self.h5_file, "a") as hdf5_file:
            # Save some device info while you have access to the hdf file
            NDPG_group = hdf5_file[f'/devices/{self.device_name}']
            NDPG_group.attrs['firmware_version'] = self.device_info['firmware_version']
            NDPG_group.attrs['hardware_version'] = self.device_info['hardware_version']
            NDPG_group.attrs['serial_number'] = self.device_info['serial_number']
            NDPG_group.attrs['comport'] = self.device_info['comport']

            if self.wait_table is not None:
                # Save info about any waits, and let the system know we have finished analysing waits.
                dtypes = [
                    ("label", "a256"),
                    ("time", float),
                    ("timeout", float),
                    ("duration", float),
                    ("timed_out", bool),
                ]
                data = np.empty(len(self.wait_table), dtype=dtypes)
                data["label"] = self.wait_table["label"]
                data["time"] = self.wait_table["time"]
                data["timeout"] = self.wait_table["timeout"]
                data["duration"] = self.measured_waits
                data["timed_out"] = self.wait_timeout

                hdf5_file.create_dataset("/data/waits", data=data)

                self.wait_durations_analysed.post(self.h5_file)

        state = self.pg.get_state()
        if state['running'] == False and state['current_address'] == self.final_instruction_address:
            self.pg.write_device_options(accept_hardware_trigger='never')   # Should automatically be placed back in this mode, but does no harm.
            self.pg.write_action(reset_run=True) # Should not be needed. But does no harm.
            return True
        else:
            return False

    def abort_transition_to_buffered(self):
        # Called only if transition_to_buffered succeeded and the
        # shot is aborted prior to the initial trigger
        # return True on success
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.abort_transition_to_buffered')
        self.started = False
        self.pg.write_device_options(accept_hardware_trigger='never')
        self.pg.write_action(reset_run=True) # Should not be required, unless the device was triggered by a hardware trigger before we could disallow it.
        return True

    def abort_buffered(self):
        # Called if the shot is to be abort in the middle of
        # the execution of the shot ( after the initial trigger )
        # return True on success
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.abort_buffered')
        self.started = False
        self.pg.write_device_options(accept_hardware_trigger='never')
        self.pg.write_action(reset_run=True)
        self.cease_rapid_timer_status_checks_in_blacs_tabs = True
        return True

    def check_remote_values(self):
        # Return the output state of the device in a dictionary ,
        # keyed by the channel name
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.check_remote_values')

        # It would be nice to extend this to get all the state of the device and update the GUI, but the function that calls this 
        # can only update the channel values.
        device_state = self.pg.get_state()
        if device_state is None:
            raise Exception('Pulse Generator failed to return its current state. ' 
                            'A likely cause is the host computer failing to read all the messages sent to it. '
                            'This can happen when the serial buffer overflows, likely because the Pulse Generator '
                            'is sending notifications faster than they can be read. Check that you are not sending many notifications.')
        remote_values = {}
        for channel, channel_state in enumerate(device_state['state']):
            remote_values[f'channel {channel}'] = channel_state
        return remote_values

    ########################### From here down, it is all things I wrote
    def set_disable_after_current_run(self):
        #I need to check the FPGA code to see if this does anything when running is not true, and when run_mode is single.
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.set_disable_after_current_run')
        self.pg.write_action(disable_after_current_run=True)

    def set_run_enable_software(self, enabled):
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.set_run_enable_software')
        self.pg.write_device_options(software_run_enable=enabled)

    def set_runmode(self, runmode):
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.set_runmode')
        self.pg.write_device_options(run_mode=runmode)

    def set_accept_hardware_trigger(self, accept_hardware_trigger):
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.set_accept_hardware_trigger')
        self.pg.write_device_options(accept_hardware_trigger=accept_hardware_trigger)

    def set_waitforpowerline(self, waitforpowerline):
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.set_waitforpowerline')
        self.pg.write_powerline_trigger_options(trigger_on_powerline=waitforpowerline)

    def set_powerlinedelay(self, powerlinedelay):
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.set_powerlinedelay')
        self.pg.write_powerline_trigger_options(powerline_trigger_delay=powerlinedelay)

    def set_triggerduration(self, triggerduration):
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.set_triggerduration')
        self.pg.write_device_options(trigger_out_length=triggerduration)

    def set_triggerdelay(self, triggerdelay):
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.set_triggerdelay')
        self.pg.write_device_options(trigger_out_delay=triggerdelay)

    def set_notifyfinished(self, notifyfinished):
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.set_notifyfinished')
        self.pg.write_device_options(notify_when_run_finished=notifyfinished)

    def set_notifytrigout(self, notifytrigout):
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.set_notifytrigout')
        self.pg.write_device_options(notify_on_main_trig_out=notifytrigout)

def print_calling_chain():
    current_frame = inspect.currentframe()
    while current_frame:
        frame_info = inspect.getframeinfo(current_frame)
        print(f"Function: {frame_info.function} | File: {frame_info.filename} | Line number: {frame_info.lineno}")
        current_frame = current_frame.f_back

    # core_clock_freq = 100
    # def init(self):
    #     exec('from spinapi import *', globals())
    #     global h5py; import labscript_utils.h5_lock, h5py
    #     global zprocess; import zprocess
        


    #     self.smart_cache = {'pulse_program':None,'ready_to_go':False,
    #                         'initial_values':None}
                            
    #     # An event for checking when all waits (if any) have completed, so that
    #     # we can tell the difference between a wait and the end of an experiment.
    #     # The wait monitor device is expected to post such events, which we'll wait on:
    #     self.all_waits_finished = zprocess.Event('all_waits_finished')
    #     self.waits_pending = False
    

    # def program_manual(self,values):
    #     # I think this is set static state
    #     return {}
        
    # def start_run(self):
    #     #Some kind of equivalent of trigger. The two options pulsebalster programming_scheme might allow for a difference between hardware and softwate trigger
    #     pass
            
    # def transition_to_buffered(self,device_name,h5file,initial_values,fresh):
    #     self.h5file = h5file
    #     pass
            
    # def check_status(self):
    #     if self.waits_pending:
    #         try:
    #             self.all_waits_finished.wait(self.h5file, timeout=0)
    #             self.waits_pending = False
    #         except zprocess.TimeoutError:
    #             pass
    #     if self.time_based_shot_end_time is not None:
    #         import time
    #         time_based_shot_over = time.time() > self.time_based_shot_end_time
    #     else:
    #         time_based_shot_over = None
    #     return pb_read_status(), self.waits_pending, time_based_shot_over
        
    # def transition_to_manual(self):
    #     pass
     
    # def abort_buffered(self):
    #     # Stop the execution
    #     self.pb_stop()
    #     # Reset to the beginning of the pulse sequence
    #     self.pb_reset()
                
    #     # abort_buffered in the GUI process queues up a program_device state
    #     # which will reprogram the device and call pb_start()
    #     # This ensures the device isn't accidentally retriggered by another device
    #     # while it is running it's abort function
    #     return True
        
    # def abort_transition_to_buffered(self):
    #     return True
        
    # def shutdown(self):
    #     pass





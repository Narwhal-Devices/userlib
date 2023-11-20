from blacs.tab_base_classes import Worker
import labscript_utils.h5_lock
import h5py
import numpy as np
import labscript_utils.properties
import ndpulsegen
import queue

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
        self.pg = ndpulsegen.PulseGenerator()
        self.pg.connect(self.serial_number)

        self.pg.write_echo(b'N')
        self.device_info = self.pg.msgin_queues['echo'].get()
        self.device_info['comport'] = self.pg.ser.port

        # Waits and waitmonitor related stuff
        self.current_wait = 0
        self.wait_table = None
        self.measured_waits = None
        self.wait_timeout = None

        # print(self.trigger_type)
        print(self.trigger_device)
        print(self.connection_table_properties)

        # print(self.device_properties["trigger_out_length"])
        # print(self.max_instructions)
        # I need to see how and where the settings are supposed to be set/passed in. Most are probably set in the connection table and stored in the self.settings['connection_table'].find_by_name(self.device_name) or something 
        self.pg.write_device_options(run_mode='single', accept_hardware_trigger='never', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=True, software_run_enable=True)
        # Need to write all settings, as they may have been changed in manual mode. Most are specified by sensible options to run in buffered mode
        #  
        # trigger_on_powerline
        # powerline_trigger_delay
        # trigger_out_length
        # trigger_out_delay
        # Maybe accept_hardware_trigger
        # Dont need to set final_address 
        # self.pg.write_powerline_trigger_options(trigger_on_powerline=None, powerline_trigger_delay=None)
        # self.pg.write_device_options(, run_mode='single', accept_hardware_trigger='always', trigger_out_length=None, trigger_out_delay=None, notify_on_main_trig_out=True, notify_when_run_finished=True, software_run_enable=True)
        self.cease_rapid_timer_status_checks_in_blacs_tabs = False

    def start_run(self):
        # method for starting the shot via a software trigger to the device.
        # The method name and return values should match those used in the 
        # associated BLACS GUI methods (which can be anything the developer wishes).
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.start_run')

        # I need to figure out if this is only called for the master pseudoclock. If is is not called for the slaves, then I need to set software_run_enable=True
        # at the end of the transition_to_buffered function.
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

        '''I cant add the firmware number, to the device_folder attributes. The file is read only here.
        I think I am just giving up on chaning the connection_table_properties for the device. or the device attributes.
        '''

        print(initial_values)
        initial_channel_state = np.zeros(24, dtype=np.int64)
        for channel_label, channel_state in initial_values.items():
            channel = int(channel_label.split()[1])
            initial_channel_state[channel] = int(channel_state)


        with h5py.File(h5file, 'r') as hdf5_file:
            # device_properties = labscript_utils.properties.get(hdf5_file, device_name, 'device_properties')
            # self.is_master_pseudoclock = device_properties['is_master_pseudoclock']
            # self.stop_time = device_properties.get('stop_time', None) # stop_time may be absent if we are not the master pseudoclock

            # Note that this get() method needs the actual open hdf5_file object, not the directory of the h5file, which is what is passed into the transition_to_buffered method
            self.device_properties = labscript_utils.properties.get(hdf5_file, device_name, "device_properties")
            print(self.device_properties)
            group = hdf5_file[f'devices/{device_name}']
            pulse_program = group['PULSE_PROGRAM'][:]
            self.is_master_pseudoclock = self.device_properties["is_master_pseudoclock"]

            # Get details of waits to check if any are mains AC sync waits
            waits_dset = hdf5_file["waits"]
            acquisition_device = waits_dset.attrs["wait_monitor_acquisition_device"]
            timeout_device = waits_dset.attrs["wait_monitor_timeout_device"]
            # if (
            #     len(waits_dset) > 0
            #     and acquisition_device
            #     == "%s_internal_wait_monitor_outputs" % device_name
            #     and timeout_device == "%s_internal_wait_monitor_outputs" % device_name
            # ):
            if len(waits_dset) > 0: # just keep it simple for now
                self.wait_table = waits_dset[:]
                self.measured_waits = np.zeros(len(self.wait_table))
                self.wait_timeout = np.zeros(len(self.wait_table), dtype=bool)
            else:
                self.wait_table = (
                    None  # This device doesn't need to worry about looking at waits
                )
                self.measured_waits = None
                self.wait_timeout = None



            # for now, don't worry which device is the wait monitor, just make it work with AC mains
            # waits_acquisition_device = waits_dset.attrs["wait_monitor_acquisition_device"]

            # Not all channels must be assigned in the labscript file. Any that aren't, keep them at the value on the GUI
            instruction_0_channel_state = pulse_program[0]['channel_state']
            unspecified_channels_index = instruction_0_channel_state == -1
            unspecified_channels_state = initial_channel_state[unspecified_channels_index]
            
            instructions = []
            for instruction in pulse_program:
                # print(instruction)
                # Not all channels must be assigned in the labscript file. Any that aren't, keep them at the value on the GUI
                channel_state = instruction['channel_state']
                channel_state[unspecified_channels_index] = unspecified_channels_state
                print(instruction)
                print()
                encoded_instruction = ndpulsegen.encode_instruction(address=instruction['address'], duration=instruction['duration'], 
                                                            state=channel_state, goto_address=instruction['goto_address'], 
                                                            goto_counter=instruction['goto_counter'], stop_and_wait=instruction['stop_and_wait'], 
                                                            hardware_trig_out=instruction['hardware_trig_out'], notify_computer=instruction['notify_computer'], 
                                                            powerline_sync=instruction['powerline_sync'])
                instructions.append(encoded_instruction)
                
            final_instr = pulse_program[-1]

        self.final_instruction_address = final_instr['address'] # hack to determine run finished without enabling hardware re-triggering
        final_values = {}
        for channel, channel_state in enumerate(final_instr['channel_state']):
            final_values[f'channel {channel}'] = channel_state
        
        print('boop')
        [print(key,':',value) for key, value in self.pg.get_state().items()]
        print('doop')
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
            self.pg.write_device_options(final_address=final_instr['address'], run_mode='single', accept_hardware_trigger='single_run', trigger_out_length=int(np.round(self.device_properties["trigger_out_length"]/10E-9)), trigger_out_delay=int(np.round(self.device_properties["trigger_out_delay"]/10E-9)), notify_on_main_trig_out=True, notify_when_run_finished=True, software_run_enable=True)
        print('floop')
        [print(key,':',value) for key, value in self.pg.get_state().items()]
        print('droop')
        return final_values


    def transition_to_manual(self):
        # Called when the shot has finished , the device should
        # be placed back into manual mode
        # return True on success
        '''Note. You only need all these checks if you WANT the system to tell you if something unexpected happened.
        You can ALWAYS, just reset the run (and disallow hardware triggers).'''
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.transition_to_manual')
        state, powerline_state, state_extras, notifications, pg_comms_in_errors, bytesdropped_error, cease_rapid_status_checks = self.check_status()
        [print(key,':',value) for key, value in state.items()]
        if state['running'] == False and state['current_address'] == self.final_instruction_address:
            # It is back in manual mode.
            # Neither of the next two commands should be necessary. But they don't take long and do no harm. 
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
        self.pg.write_device_options(accept_hardware_trigger='never')
        self.pg.write_action(reset_run=True) # Should not be required, unless the device was triggered by a hardware trigger before we could disallow it.
        return True

    def abort_buffered(self):
        # Called if the shot is to be abort in the middle of
        # the execution of the shot ( after the initial trigger )
        # return True on success
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.abort_buffered')
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





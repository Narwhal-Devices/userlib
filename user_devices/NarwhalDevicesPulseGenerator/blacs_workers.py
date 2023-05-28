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

        # print(self.trigger_type)
        print(self.trigger_device)
        print(self.connection_table_properties)

        # print(self.device_properties["trigger_out_length"])
        # print(self.max_instructions)
        # I need to see how and where the settings are supposed to be set/passed in. Most are probably set in the connection table and stored in the self.settings['connection_table'].find_by_name(self.device_name) or something 
        self.pg.write_device_options(run_mode='single', trigger_source='software', trigger_out_length=1, trigger_out_delay=0, notify_on_main_trig_out=False, notify_when_run_finished=True, software_run_enable=True)
        # Need to write all settings, as they may have been changed in manual mode. Most are specified by sensible options to run in buffered mode
        #  
        # trigger_on_powerline
        # powerline_trigger_delay
        # trigger_out_length
        # trigger_out_delay
        # Maybe trigger_source
        # Dont need to set final_ram_address 
        # self.pg.write_powerline_trigger_options(trigger_on_powerline=None, powerline_trigger_delay=None)
        # self.pg.write_device_options(, run_mode='single', trigger_source='either', trigger_out_length=None, trigger_out_delay=None, notify_on_main_trig_out=True, notify_when_run_finished=True, software_run_enable=True)

    def start_run(self):
        # method for starting the shot via a software trigger to the device.
        # The method name and return values should match those used in the 
        # associated BLACS GUI methods (which can be anything the developer wishes).
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.start_run')
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
        #Empty the state queues incase there is old data in them
        state_queue.queue.clear()
        powerline_state_queue.queue.clear()
        #request the state
        self.pg.write_action(request_state=True, request_powerline_state=True)
        # wait for the state to be sent
        # state = state_queue.get(timeout=0.1)
        # powerline_state = powerline_state_queue.get(timeout=0.1)
        state = state_queue.get()
        powerline_state = powerline_state_queue.get()
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
        return state, powerline_state, notifications, pg_comms_in_errors, bytesdropped


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


        '''So here is where I should add the firmware number, and I must add it to the
        device_folder attributes.
        I think I am just giving up on chaning the connection_table_properties for the device.
        '''

        with h5py.File(h5file, 'r') as hdf5_file:
            # device_properties = labscript_utils.properties.get(hdf5_file, device_name, 'device_properties')
            # self.is_master_pseudoclock = device_properties['is_master_pseudoclock']
            # self.stop_time = device_properties.get('stop_time', None) # stop_time may be absent if we are not the master pseudoclock

            # Note that this get() method needs the actual open hdf5_file object, not the directory of the h5file, which is what is passed into the transition_to_buffered method
            self.device_properties = labscript_utils.properties.get(hdf5_file, device_name, "device_properties")
            print(self.device_properties)

            group = hdf5_file[f'devices/{device_name}']
            pulse_program = group['PULSE_PROGRAM'][:]


            instructions = []
            for vals in pulse_program:
                instruction = ndpulsegen.encode_instruction(address=vals['address'], duration=vals['duration'], 
                                                            state=vals['channel_state'], goto_address=vals['goto_address'], 
                                                            goto_counter=vals['goto_counter'], stop_and_wait=vals['stop_and_wait'], 
                                                            hardware_trig_out=vals['hardware_trig_out'], notify_computer=vals['notify_computer'], 
                                                            powerline_sync=vals['powerline_sync'])
                instructions.append(instruction)
            final_instr = pulse_program[-1]

        final_values = {}
        for channel, channel_state in enumerate(final_instr['channel_state']):
            final_values[f'channel {channel}'] = channel_state

        self.pg.write_instructions(instructions)
        # Need to write all settings, as they may have been changed in manual mode. Most are specified by sensible options to run in buffered mode
        #  
        # trigger_on_powerline
        # powerline_trigger_delay
        # trigger_out_length
        # trigger_out_delay
        # Maybe trigger_source
        self.pg.write_powerline_trigger_options(trigger_on_powerline=None, powerline_trigger_delay=None)
        self.pg.write_device_options(final_ram_address=final_instr['address'], run_mode='single', trigger_source='either', trigger_out_length=None, trigger_out_delay=None, notify_on_main_trig_out=True, notify_when_run_finished=True, software_run_enable=True)
        return final_values


    def transition_to_manual(self):
        # Called when the shot has finished , the device should
        # be placed back into manual mode
        # return True on success
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.transition_to_manual')
        state, powerline_state, notifications, pg_comms_in_errors, bytesdropped_error = self.check_status()
        if not state['running'] and state['current_address'] == 0:
            # If it is back in manual mode, make it ignore hardware triggers 
            self.pg.write_device_options(trigger_source='software')
            return True
        else:
            return False

    def abort_transition_to_buffered(self):
        # Called only if transition_to_buffered succeeded and the
        # shot is aborted prior to the initial trigger
        # return True on success
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.abort_transition_to_buffered')
        return True

    def abort_buffered(self):
        # Called if the shot is to be abort in the middle of
        # the execution of the shot ( after the initial trigger )
        # return True on success
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.abort_buffered')
        self.pg.write_action(reset_run=True)
        return True

    def check_remote_values(self):
        # Return the output state of the device in a dictionary ,
        # keyed by the channel name
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.check_remote_values')

        # It would be nice to extend this to get all the state of the device and update the GUI, but the function that calls this 
        # can only update the channel values.
        state_queue = self.pg.msgin_queues['devicestate']
        state_queue.queue.clear()
        self.pg.write_action(request_state=True)
        device_state = state_queue.get()
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

    def set_triggersource(self, triggersource):
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.set_triggersource')
        self.pg.write_device_options(trigger_source=triggersource)

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





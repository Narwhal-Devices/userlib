from blacs.tab_base_classes import Worker
import ndpulsegen

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


    def start_run(self):
        # method for starting the shot via a software trigger to the device.
        # The method name and return values should match those used in the 
        # associated BLACS GUI methods (which can be anything the developer wishes).
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.start_run')
        pass

    def check_status(self):
        # method for checking whether the shot has completed.
        # The method name and return values should match those used in the 
        # associated BLACS GUI methods (which can be anything the developer wishes).
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.check_status')
        pass


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

    def transition_to_buffered(self , device_name, h5file, initial_values, fresh):
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
        return final_values

    def transition_to_manual(self):
        # Called when the shot has finished , the device should
        # be placed back into manual mode
        # return True on success
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.transition_to_manual')
        return True

    def abort_transition_to_buffered(self):
        # Called only if transition_to_buffered succeeded and the
        # shot if aborted prior to the initial trigger
        # return True on success
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.abort_transition_to_buffered')
        return True

    def abort_buffered(self):
        # Called if the shot is to be abort in the middle of
        # the execution of the shot ( after the initial trigger )
        # return True on success
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.abort_buffered')
        return True

    def check_remote_values(self):
        # Return the output state of the device in a dictionary ,
        # keyed by the channel name
        print('called blacs_workers.NarwhalDevicesPulseGeneratorWorker.check_remote_values')

        # It would be nice to extend this to get all the state of the device and update the GUI, but the function that calls this 
        # can only update the channel values.

        state = self.pg.get_state()
        remote_values = {}
        for idx, value in enumerate(state['state']):
            remote_values[f'channel {idx}'] = value
        return remote_values




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



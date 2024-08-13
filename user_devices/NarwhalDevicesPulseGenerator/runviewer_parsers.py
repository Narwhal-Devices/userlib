#####################################################################
#                                                                   #
# /labscript_devices/PrawnBlaster/runviewer_parsers.py              #
#                                                                   #
# Copyright 2021, Philip Starkey                                    #
#                                                                   #
# This file is part of labscript_devices, in the labscript suite    #
# (see http://labscriptsuite.org), and is licensed under the        #
# Simplified BSD License. See the license.txt file in the root of   #
# the project for the full license.                                 #
#                                                                   #
#####################################################################

import labscript_utils.h5_lock  # noqa: F401
import h5py
import numpy as np

import labscript_utils.properties as properties


class NarwhalDevicesPulseGeneratorParser(object):
    """Runviewer parser for the PrawnBlaster Pseudoclocks."""
    def __init__(self, path, device):
        """
        Args:
            path (str): path to h5 shot file
            device (str): labscript name of PrawnBlaster device
        """
        self.path = path
        self.name = device.name
        self.device = device

    def get_traces(self, add_trace, clock=None):
        """Reads the shot file and extracts hardware instructions to produce
        runviewer traces.

        Args:
            add_trace (func): function handle that adds traces to runviewer
            clock (tuple, optional): clock times from timing device, if not
                the primary pseudoclock

        Returns:
            dict: Dictionary of clocklines and triggers derived from instructions
        """

        '''clock variable is provided as a 2-tuple of NumPy arrays (themselves 1D arrays of equal length) 
        which contain the times and state changes of the external trigger 
        
        The method signature for add_trace is add_trace(name, trace, parent_device_name, connection), 
        where name is a string containing the display name for the output, trace is the 2-tuple, 
        and parent_device_name and connection are strings specifying the relationship between the
        trace and the device. 
        '''
        print('here is the clock variable')
        print(clock)

        # If not the master pseudoclock, then I need to handle the case of getting
        # possibly multiple triggers. Ignore for now though.

        # get the instructions
        with h5py.File(self.path, "r") as file:
            # Get the device properties
            device_props = properties.get(file, self.name, "device_properties")
            conn_props = properties.get(file, self.name, "connection_table_properties")

            self.clock_resolution = device_props["clock_resolution"]
            self.trigger_delay = device_props["trigger_delay"]
            self.wait_delay = device_props["wait_delay"]

            print(device_props)
            print(conn_props)

            instructions = file[f"devices/{self.name}/PULSE_PROGRAM"][:]

        # [print(x) for x in instructions]

        # It is assumed that the final ram address is the last address in the list (of sorted dictionary instructions)
        final_address = len(instructions)-1
        channel_states = []
        durations = []
        stop_and_wait = []
        powerline_sync = []
        # addresses = []
        # instruction_address = []
        # goto_counter = []
        # goto_counter_original = []
        # hard_trig_out = []
        # notify_computer = []


        instructions_goto_counter_original = instructions['goto_counter'].copy()
        address = 0
        while True:
            instruction = instructions[:][address]
            # Save all the required infor from this instruction

            channel_states.append(instruction['channel_state'])
            durations.append(instruction['duration'])
            stop_and_wait.append(instruction['stop_and_wait'])
            powerline_sync.append(instruction['powerline_sync'])

            # instruction_address.append(address)
            # goto_counter.append(instruction['goto_counter'])
            # goto_counter_original.append(instructions_goto_counter_original[address])
            # hard_trig_out.append(instruction['hardware_trig_out'])
            # notify_computer.append(instruction['notify_computer'])

            if instruction['goto_counter'] == 0:
                instruction['goto_counter'] = instructions_goto_counter_original[address]
                if address == final_address:
                    break
                address += 1
            else:
                instruction['goto_counter'] -= 1
                address = instruction['goto_address']
        
        durations.insert(0, 0)  # we want time to start at zero
        channel_states.insert(0, channel_states[-1]) # The outputs will ususally begin in same state that they end in
        stop_and_wait.insert(0, False)
        powerline_sync.insert(0, False)
        # I need to do more than this.
        # I need to make sure that at every change there is a data poiny on both sides
        # otherwise the graph will go up at an angle


        channel_states = np.array(channel_states)
        durations = np.array(durations) * self.clock_resolution
        stop_and_wait = np.array(stop_and_wait)
        powerline_sync = np.array(powerline_sync)


        times = np.cumsum(durations)
        # I need to do more than this.
        # I need to make sure that at every change there is a data poiny on both sides
        # otherwise the graph will go up at an angle

        # goto_counter = []
        # goto_counter_original = []
        # hard_trig_out = np.array(hard_trig_out)
        # notify_computer = np.array(notify_computer)


        print(durations)
        print(times)
        print(channel_states)
        print(channel_states.shape)
        print(stop_and_wait)
        print(powerline_sync)


        # Start by getting all the direct output devices, but then need to do any additional clocklines
        name = self.device.name
        pseudoclock = self.device.child_list[f'{name}_pseudoclock']

        # Do direcet output device
        direct_output_device = pseudoclock.child_list[f'{name}_direct_output_clock_line'].child_list[f'{name}_direct_output_device']
        
        for direct_output_name, direct_output in direct_output_device.child_list.items():
            direct_output_channel = int(direct_output.parent_port.split()[1])
            print(direct_output_name)
            print(direct_output_channel)
            add_trace(direct_output_name, (times, channel_states[:, direct_output_channel]), self.device.name, direct_output.parent_port)

        # now do additional clocklines


        print('self.device')
        print(self.device.name)
        print(vars(self.device))


        print('self.device.child_list')
        print(self.device.child_list) # A dictionary of pseudoclocks (the actual speudoclock and the dummy waitmonitor one)

        connection_NDPG0_pseudoclock = self.device.child_list['NDPG0_pseudoclock']

        print('connection_NDPG0_pseudoclock')       
        print(connection_NDPG0_pseudoclock)        
        print(vars(connection_NDPG0_pseudoclock))
        
        NDPG0_direct_output_clock_line = connection_NDPG0_pseudoclock.child_list['NDPG0_direct_output_clock_line']

        print('NDPG0_direct_output_clock_line')        
        print(NDPG0_direct_output_clock_line)        
        print(vars(NDPG0_direct_output_clock_line))
        
        NDPG0_direct_output_device = NDPG0_direct_output_clock_line.child_list['NDPG0_direct_output_device']
        
        print('NDPG0_direct_output_device')
        print(NDPG0_direct_output_device)
        print(vars(NDPG0_direct_output_device))

        NDPG0_DO0 = NDPG0_direct_output_device.child_list['NDPG0_DO0']
        
        print('NDPG0_DO0')
        print(NDPG0_DO0)
        print(vars(NDPG0_DO0))

        physical_connection = NDPG0_DO0.parent_port
        print('hoop')
        print(physical_connection)

        # add_trace(name, trace, parent_device_name, connection)
        
        clocklines_and_triggers = {}
        # return np.array(durations, dtype=int), np.array(states, dtype=int), np.array(instruction_address, dtype=int), np.array(goto_counter, dtype=int), np.array(goto_counter_original, dtype=int), np.array(stop_and_wait, dtype=bool), np.array(hard_trig_out, dtype=bool), np.array(notify_computer, dtype=bool), np.array(powerline_sync, dtype=bool)


        return clocklines_and_triggers

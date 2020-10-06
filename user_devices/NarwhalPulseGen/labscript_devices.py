
# This file represents a dummy labscript device for purposes of testing BLACS
# and labscript. The device is a PseudoclockDevice, and can be the sole device
# in a connection table or experiment.


from labscript import PseudoclockDevice, Pseudoclock, ClockLine, IntermediateDevice, DigitalOut, config, LabscriptError, set_passed_properties
import numpy as np


class NarwhalPulseGenPseudoclock(Pseudoclock):  
    description = 'Narwhal Devices Pulse Generator - Pseudoclock'  
    def add_device(self, device):
        if isinstance(device, ClockLine):
            Pseudoclock.add_device(self, device)
        else:
            raise LabscriptError('You have connected %s to %s (the Pseudoclock of %s), but %s only supports children that are ClockLines. Please connect your device to %s.clockline instead.'%(device.name, self.name, self.parent_device.name, self.name, self.parent_device.name))

class NarwhalPulseGen(PseudoclockDevice):
    description = 'Narwhal Devices Pulse Generator - PseudoclockDevice'
    cycle_period = 10e-9
    clock_limit = 1/cycle_period
    clock_resolution = cycle_period
    trigger_delay = 2*cycle_period
    wait_delay = trigger_delay
    allowed_children = [NarwhalPulseGenPseudoclock]
    max_instructions = 8192
    n_channels = 24

    @set_passed_properties(property_names = {
        'connection_table_properties': ['usbport'],
        'device_properties': ['pulse_width']}
        )  
    def __init__(self, name='narwhal_pulsegen', usbport='autodetect', pulse_width='symmetric', **kwargs):
        self.BLACS_connection = usbport
        self.pulse_width = pulse_width
        PseudoclockDevice.__init__(self, name, None, None, **kwargs)
        # Create the internal pseudoclock
        self._pseudoclock = NarwhalPulseGenPseudoclock(
            name=f'{name}_pseudoclock',
            pseudoclock_device=self,
            connection='pseudoclock',
        )
        # Create the internal direct output clock_line
        self._direct_output_clock_line = ClockLine(
            name=f'{name}_direct_output_clock_line',
            pseudoclock=self.pseudoclock,
            connection='internal',
            ramping_allowed = False,
        )
        # Create the internal intermediate device connected to the above clock line
        # This will have the direct DigitalOuts of the NarwhalPulseGen connected to it
        self._direct_output_device = NarwhalPulseGenDirectOutputs(
            name=f'{name}_direct_output_device',
            parent_device=self._direct_output_clock_line)

    @property
    def pseudoclock(self):
        return self._pseudoclock
        
    @property
    def direct_outputs(self):
        return self._direct_output_device
    
    def add_device(self, device):
        if not self.child_devices and isinstance(device, Pseudoclock):
            PseudoclockDevice.add_device(self, device)
        elif isinstance(device, Pseudoclock):
            raise LabscriptError(f'The {self.name} PseudoclockDevice only supports a single Pseudoclock, so it automatically creates one.' +
                                 f'Instead of instantiating your own Pseudoclock object, please use the internal one stored in {self.name}.pseudoclock')
        elif isinstance(device, DigitalOut):
            raise LabscriptError(f'You have connected {device.name} directly to {self.name}, which is not allowed. You should instead specify ' + 
                                 f'the parent_device of {device.name} as {self.name}.direct_outputs')
        elif isinstance(device, ClockLine):
            raise LabscriptError(f'You have connected {device.name} directly to {self.name}, which is not allowed. You should instead specify ' + 
                                 f'the parent_device of {device.name} as {self.name}.pseudoclock')
        else:
            raise LabscriptError(f'You have connected {device.name} (class {device.__class__}) to {self.name}, but {self.name} does not support children with that class.')

    def generate_code(self, hdf5_file):
        # Generate the hardware instructions
        hdf5_file.create_group('/devices/' + self.name)
        PseudoclockDevice.generate_code(self, hdf5_file)
        npg_inst = self.pseudo_inst_to_npg_inst()
        self.write_npg_inst_to_h5(npg_inst, hdf5_file)

    def sec_to_cyc(self, object_in_seconds):
        if isinstance(object_in_seconds, list):
            return [int(round(element/self.cycle_period)) for element in object_in_seconds]
        elif isinstance(object_in_seconds, tuple):  
            return (int(round(element/self.cycle_period)) for element in object_in_seconds)
        return int(round(object_in_seconds/self.cycle_period))

    def pseudo_inst_to_npg_inst(self):
        dig_outputs = self.direct_outputs.get_all_outputs()
        # for attr in dir(dig_outputs[0]):
        #     print('obj.%s = %r'%(attr, getattr(dig_outputs[0], attr)))

        # for attr in dir(self._direct_output_clock_line):
        #     print('obj.%s = %r'%(attr, getattr(self._direct_output_clock_line, attr)))

        npg_inst = []
        
        # index to keep track of where in output.raw_output the
        # pulseblaster channels are coming from
        # starts at -1 because the internal flag should always tick on the first instruction and be 
        # incremented (to 0) before it is used to index any arrays
        raw_output_idx = -1 

        # flagstring = '0'*self.n_flags # So that this variable is still defined if the for loop has no iterations
        channels = [2]*self.n_channels # 2 will specify that the flag should take the value from blacs at runtime
        for k, instruction in enumerate(self.pseudoclock.clock):
            print(instruction)
            if instruction == 'WAIT':
                # This is a wait pseudoinstruction. For the narwhal pulsegen, any instuction can contain a wait tag. Just add
                # a wait tag to the last instruction. That instuction is executed, and then the clock pauses just before the next instruction. 
                if len(npg_inst) > 0:
                    npg_inst[-1]['stop_and_wait'] = True
                else:
                    raise LabscriptError(f'You tried to make \"WAIT\" at the very start of execution time')
                continue
            # This flag indicates whether we need a full clock tick, or are just updating an internal output
            only_internal = True
            # find out which clock flags are ticking during this instruction
            for clock_line in instruction['enabled_clocks']:
                if clock_line == self._direct_output_clock_line: 
                    # advance raw_output_idx (the index keeping track of internal clockline output)
                    raw_output_idx += 1
                else:
                    channel_index = int(clock_line.connection.split()[1]) 
                    channels[channel_index] = 1
                    # We are not just using the internal clock line
                    only_internal = False
            
            # Set all the digital outputs to their value specified by raw_outputs
            for output in dig_outputs:
                channel_index = int(output.connection.split()[1])
                channels[channel_index] = int(output.raw_output[raw_output_idx])
            
            if only_internal:
                # Just flipping any direct_outputs that need flipping, and holding that state for the required step time
                npg_inst.append({'channels': channels.copy(), 'duration':self.sec_to_cyc(instruction['step']), 'goto_address':0, 'goto_counter':0,
                                'stop_and_wait':False, 'hardware_trig_out':False, 'notify_computer':False, 'powerline_sync':False})
            else:
                # the pseudoinstruction calls for us to make a pulse. So on the required channels, you need to go high, then low, and loop back to high for the required number of repetitions
                if self.pulse_width == 'symmetric':
                    high_time = self.sec_to_cyc(instruction['step']/2)
                else:
                    high_time = self.sec_to_cyc(self.pulse_width)

                # Tick high
                print(channels)
                npg_inst.append({'channels': channels.copy(), 'duration':high_time, 'goto_address':0, 'goto_counter':0,
                                'stop_and_wait':False, 'hardware_trig_out':False, 'notify_computer':False, 'powerline_sync':False})

                # Low time is whatever is left:
                low_time = self.sec_to_cyc(instruction['step']) - high_time

                # Any enabled clocklines (that are not _direct_output_clockline) now needs to go low, so set these channels to 0
                for clock_line in instruction['enabled_clocks']:
                    if clock_line != self._direct_output_clock_line:
                        channel_index = int(clock_line.connection.split()[1])
                        channels[channel_index] = 0

                # Tock low
                goto_address = len(npg_inst)-1 #loop back to the last instruction (this is ignored by hardware is goto_counter==0)
                npg_inst.append({'channels': channels.copy(), 'duration':low_time, 'goto_address':goto_address, 'goto_counter':instruction['reps']-1,
                                'stop_and_wait':False, 'hardware_trig_out':False, 'notify_computer':False, 'powerline_sync':False})
        return npg_inst

    def write_npg_inst_to_h5(self, npg_inst, hdf5_file):
        # OK now we squeeze the instructions into a numpy array ready for writing to hdf5:
        npg_dtype = [('duration', np.int64), ('goto_address', np.int64), ('goto_counter', np.int64),
                     ('stop_and_wait', np.bool), ('hardware_trig_out', np.bool), ('notify_computer', np.bool), ('powerline_sync', np.bool)]
        npg_dtype.extend([('channel {}'.format(ch), np.int8) for ch in range(self.n_channels)])
        npg_inst_table = np.empty(len(npg_inst),dtype = npg_dtype)

        
        for i, inst in enumerate(npg_inst):
            flat_instr = [inst['duration'], inst['goto_address'], inst['goto_counter'], 
                          inst['stop_and_wait'], inst['hardware_trig_out'], inst['notify_computer'], inst['powerline_sync']]  
            flat_instr.extend(inst['channels'])
            print(flat_instr)
            npg_inst_table[i] = tuple(flat_instr)
                                
        # Okay now write it to the file: 
        group = hdf5_file['/devices/'+self.name]  
        group.create_dataset('PULSE_PROGRAM', compression=config.compression,data = npg_inst_table)   
        self.set_property('stop_time', self.stop_time, location='device_properties')


class NarwhalPulseGenDirectOutputs(IntermediateDevice):
    description = 'Narwhal Devices Pulse Generator - IntermediateDevice. The parent of any direct DigitalOut devices'
    clock_limit = NarwhalPulseGen.clock_limit  
    def add_device(self, device):
        if isinstance(device, DigitalOut):
            IntermediateDevice.add_device(self, device)
        else:
            raise LabscriptError(f'You have connected {device.name} to {self.name} (the IntermediateDevice '+
                                 f'embedded in {self.parent_device.parent_device.name}), but {self.name} only ' + 
                                 f'supports DigitalOut children.')
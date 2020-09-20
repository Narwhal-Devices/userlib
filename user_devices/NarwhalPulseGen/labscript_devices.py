
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

    @set_passed_properties(property_names = {
        'connection_table_properties': ['usbport']}
        )  
    def __init__(self, name='narwhal_pulsegen', usbport='autodetect', **kwargs):
        self.BLACS_connection = usbport
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
        dig_outputs = self.direct_outputs.get_all_outputs()
        npg_inst = self.convert_to_npg_inst(dig_outputs)
        self.write_npg_inst_to_h5(npg_inst, hdf5_file)

    def convert_to_npg_inst(self, dig_outputs):
        '''
        The format of the instructions will be a list of dictionaries, each dictioaty will be an instruction
        Its index in the list will be its address.
        The instruction dictionary will have the format:
        instr = {'state'=array(24 ints), 'duration'=1, 'goto_address'=0, 'goto_counter'=0, 'stop_and_wait'=False, 'hardware_trig_out'=False, 'notify_computer'=False, 'powerline_sync'=False}
        in the state array, the index corresponds to the main output number.
        the values can be 0=low, 1=high, 2=set_by_blacs (usually for channels that aren't switching)
        '''

        '''
        What would I do:
        Get a pen and paper and write it out.

        
        '''





        print(dig_outputs)
        for attr in dir(dig_outputs[0]):
            print('obj.%s = %r'%(attr, getattr(dig_outputs[0], attr)))
        print(dig_outputs[0].__dict__)
        npg_instr = []
        for k, instruction in enumerate(self.pseudoclock.clock):
            # print(k, instruction)
            # print(instruction['enabled_clocks'])
            print([clockline.name for clockline in instruction['enabled_clocks']])
            print(instruction)
            print()
        i=0
        for k, instruction in enumerate(self.pseudoclock.clock):
            # This flag indicates whether we need a full clock tick, or are just updating an internal output
            only_internal = True
            # find out which clock flags are ticking during this instruction
            for clock_line in instruction['enabled_clocks']:
                if clock_line == self._direct_output_clock_line: 
                    # advance i (the index keeping track of internal clockline output)
                    i += 1
                else:
                    flag_index = int(clock_line.connection.split()[-1])
                    # flags[flag_index] = 1
                    # We are not just using the internal clock line
                    only_internal = False
            
            # for output in dig_outputs:
            #     flagindex = int(output.connection.split()[1])
            #     flags[flagindex] = int(output.raw_output[i])


        return npg_instr

    def write_npg_inst_to_h5(self, pb_inst, hdf5_file):
        pb_inst_table = np.empty(len(pb_inst),dtype = np.int)
        for i,inst in enumerate(pb_inst):
            pb_inst_table[i] = ((0, 0, 0, 0))
        # Okay now write it to the file: 
        group = hdf5_file['/devices/'+self.name]  
        group.create_dataset('PULSE_PROGRAM', compression=config.compression,data = pb_inst_table)   
        self.set_property('stop_time', 696969, location='device_properties')

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
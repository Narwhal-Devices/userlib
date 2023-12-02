from labscript_utils import dedent

from labscript import (
    PseudoclockDevice,
    Pseudoclock,
    ClockLine,
    IntermediateDevice,
    DigitalOut,
    WaitMonitor,
    config,
    LabscriptError,
    set_passed_properties,
    compiler,
)
import numpy as np
import time

# This is taken straight from the PrawnBlaster. So who knows if it will work...
# Define dummy pseudoclock/clockline/intermediatedevice to trick wait monitor
# since everything is handled internally in this device
#
class _NDPGDummyPseudoclock(Pseudoclock):
    """Dummy Pseudoclock labscript device used internally to allow 
    :class:`~labscript.WaitMonitor` to work internally to the Narwhal Devices Pulse Generator."""
    def add_device(self, device):
        if isinstance(device, _NDPGDummyClockLine):
            if self.child_devices:
                raise LabscriptError(
                    f"You are trying to access the special, dummy, PseudoClock of the Narwhal Devices Pulse Generator {self.pseudoclock_device.name}. This is for internal use only."
                )
            Pseudoclock.add_device(self, device)
        else:
            raise LabscriptError(
                f"You are trying to access the special, dummy, PseudoClock of the Narwhal Devices Pulse Generator {self.pseudoclock_device.name}. This is for internal use only."
            )

    # do nothing, this is a dummy class!
    def generate_code(self, *args, **kwargs):
        pass


class _NDPGDummyClockLine(ClockLine):
    """Dummy Clockline labscript device used internally to allow 
    :class:`~labscript.WaitMonitor` to work internally to the Narwhal Devices Pulse Generator."""
    def add_device(self, device):
        if isinstance(device, _NDPGDummyIntermediateDevice):
            if self.child_devices:
                raise LabscriptError(
                    f"You are trying to access the special, dummy, ClockLine of the Narwhal Devices Pulse Generator {self.pseudoclock_device.name}. This is for internal use only."
                )
            ClockLine.add_device(self, device)
        else:
            raise LabscriptError(
                f"You are trying to access the special, dummy, ClockLine of the Narwhal Devices Pulse Generator {self.pseudoclock_device.name}. This is for internal use only."
            )

    # do nothing, this is a dummy class!
    def generate_code(self, *args, **kwargs):
        pass


class _NDPGDummyIntermediateDevice(IntermediateDevice):
    """Dummy intermediate labscript device used internally to attach 
    :class:`~labscript.WaitMonitor` objects to the Narwhal Devices Pulse Generator."""

    def add_device(self, device):
        if isinstance(device, WaitMonitor):
            IntermediateDevice.add_device(self, device)
        else:
            raise LabscriptError(
                "You can only connect an instance of WaitMonitor to the device %s.internal_wait_monitor_outputs"
                % (self.pseudoclock_device.name)
            )

    # do nothing, this is a dummy class!
    def generate_code(self, *args, **kwargs):
        pass


class NarwhalDevicesPulseGenerator(PseudoclockDevice):

    ############### Attributes required by superclasses ################  
    description = 'Narwhal Devices Pulse Generator'

    clock_limit = 100E6 #hertz
    '''The clock_limit specifies the minimum instruction duration. ie min_instruction_length=1/clock_limit'''

    clock_resolution = 10E-9 #seconds
    '''The clock_resolution specifies the increment that can be added to the min_instruction_length.
    for some devices, min_instruction_length > clock_resolution. But the Narwhal Devices Pulse Generator
    is super awesome, so min_instruction_length=clock_resolution.'''

    trigger_edge_type = 'rising'
    '''The edge of the input hardware trigger signal that the device responds to.'''

    trigger_minimum_duration = 10E-9 #seconds
    '''Minimum required duration of an input hardware trigger to guarantee that it will be registered'''
    
    minimum_recovery_time = 20E-9 #seconds
    '''Minimum time between the rising edges of two input hardware trigger so that they will both be registered'''

    trigger_delay = 40E-9 #seconds
    '''The time between an input hardware trigger arriving at the Pulse Generator, and the voltage of the channel outputs
    updating. This is able to be longer than the minimum_recovery_time because the FPGA pipelines some signals. ie, 
     it can start doing the next thing before it has finished doing the current thing.'''

    wait_delay = 0 #seconds
    '''How long after the start of a WAIT instruction the device is actually capable of resuming'''

    allowed_children = [Pseudoclock]
    '''This device can only have Pseudoclock children. Clockline(s), DigitalOut(s), and Trigger(s) are connected to 
    internally created children.'''

    ############### Attributes required only by this class ################  
    max_instructions = 8192
    '''The maximum number of device instructions that the Narwhal Devices Pulse Generator can store. This is
    not the same as the number of pseudoinstructions that labscript could generate, as some pseudoinstructions
    may require more than one device instruction.'''

    n_channels = 24
    '''The total number of output channels.'''

    '''May or may not need to rethink which properties go in "connection_table_properties", and which
    do in "device_properties". "device_properties" can only be accessed from the hdf file so are sort of a "per
    shot" type setting. They can be accessed in the "transition_to_buffered" method of the worker, 
    becase a referece to the hdf file is passed in. this is maybe ok. When I initialize the worker, 
    I can set it with sensible defaults. The settings are then changed to the required "device_properties"
    only when a shot is about to be run. Which is fine.'''
    
    @set_passed_properties(
        property_names={
            "connection_table_properties": [
                "trigger_device",       #It is possible this MUST go in "device properties"
                "trigger_connection"   #It is possible this MUST go in "device properties" NON OF THESE ARE BEING SAVED
            ],
            "device_properties": [
                "trigger_out_length",
                "trigger_out_delay",
                "trigger_on_powerline",
                "powerline_trigger_delay",
                "max_instructions"
            ],
        }
    )
    def __init__(
        self,
        name,
        serial_number=None,
        trigger_device=None,
        trigger_connection=None,
        trigger_out_length=10E-9,
        trigger_out_delay=0,
        trigger_on_powerline=False,
        powerline_trigger_delay=0,
        use_wait_monitor=True,
    ):
        """Narwhal Devices Pulse Generator.

        This labscript device creates a single Pseudoclock, and can be used to produce
        Clockline(s), DigitalOut(s), and Trigger(s). 

        Args:
            name (str): python variable name to assign to the Narwhal Devices Pulse 
                Generator (NDPG). Used by labscript base classes to determine instructions.
            serial_number (int, optional): The serial number of the NDPG that you want
                to connect to. Defaults to 'None' where connection will be made to the 
                first available NDPG.
            trigger_device (:class:`~labscript.IntermediateDevice`, optional): Device
                that will send the hardware start trigger when using the NDPG as a secondary 
                Pseudoclock. Used by labscript base classes to determine instructions.
            trigger_connection (str, optional): The name of the output of the `trigger_device`
                that is connected to the NDPG hardware trigger input. Used by labscript base 
                classes to determine instructions.
            trigger_out_length (float, optional): ∈ [0, 2.55E-6] seconds. The duration of the pulses 
                output from the Trigger Out physical port on the NDPG.
                See also: ndpulsegen.transcode.encode_device_options
            trigger_out_delay (float, optional): ∈ [0, 720575940.3792794] seconds. The delay 
                between the update of the channels when a run has started, and the pulse 
                that is output on Trigger Out physical port on the NDPG.
                See also: ndpulsegen.transcode.encode_device_options
            trigger_on_powerline (bool, optional): If True, all software and hardware triggers 
                will not immediately start or restart a run. Instead, any trigger recieved 
                will put the run in state where it immediately restarts on the next 
                powerline_trigger.
                See also: ndpulsegen.transcode.encode_powerline_trigger_options
            powerline_trigger_delay (float, optional): ∈ [0, 41.94303E-3] seconds. The delay 
                between the mains AC line crossing 0 volts in a positive direction, and the 
                emission of a powerline_trigger.
                See also: ndpulsegen.transcode.encode_powerline_trigger_options
            use_wait_monitor (bool, optional): Configure the Pulse Generator to
                perform its own wait monitoring.
        """


        # Instantiate the base class
        PseudoclockDevice.__init__(self, name, trigger_device, trigger_connection)

        # Set the BLACS connections
        self.BLACS_connection = serial_number

        # Wait monitor can only be used if this is the master pseudoclock
        self.use_wait_monitor = use_wait_monitor and self.is_master_pseudoclock

        # This works
        # self.set_property('mynewpropname', 'I set this frim labscript_devices.py', 'connection_table_properties')
        # self.set_property('mynewdevicepropname', 'I set this frim labscript_devices.py', 'device_properties')

        # This is the minimum duration of a NDPG instruction. We save this now
        # because clock_limit will be modified to reflect child device limitations and
        # other things, but this remains the minimum instruction delay regardless of all
        # that.

        '''This is a sort of copy from the pulseblaster code, but I don't really know what i need, so leave it to alter'''
        # self.min_delay = 0.5 / self.clock_limit

        # #Things needed to make it run, but I may well delete again
        # pulse_width = 'minimum'


        # if pulse_width == 'minimum':
        #     pulse_width = 0.5/self.clock_limit # the shortest possible
        # elif pulse_width != 'symmetric':
        #     if not isinstance(pulse_width, (float, int, np.integer)):
        #         msg = ("pulse_width must be 'symmetric', 'minimum', or a number " +
        #                "specifying a fixed pulse width to be used for clocking signals")
        #         raise ValueError(msg)

        #     if pulse_width < 0.5/self.clock_limit:
        #         message = ('pulse_width cannot be less than 0.5/%s.clock_limit '%self.__class__.__name__ +
        #                    '( = %s seconds)'%str(0.5/self.clock_limit))
        #         raise LabscriptError(message)
        #     # Round pulse width up to the nearest multiple of clock resolution:
        #     quantised_pulse_width = 2*pulse_width/self.clock_resolution
        #     quantised_pulse_width = int(quantised_pulse_width) + 1 # ceil(quantised_pulse_width)
        #     # This will be used as the high time of clock ticks:
        #     pulse_width = quantised_pulse_width*self.clock_resolution/2
        #     # This pulse width, if larger than the minimum, may limit how fast we can tick.
        #     # Update self.clock_limit accordingly.
        #     minimum_low_time = 0.5/self.clock_limit
        #     if pulse_width > minimum_low_time:
        #         self.clock_limit = 1/(pulse_width + minimum_low_time)
        # self.pulse_width = pulse_width
        
        #For now, just use symmetric pulses
        self.pulse_width = 'symmetric'

        # Create the internal pseudoclock
        self._pseudoclock = Pseudoclock('%s_pseudoclock'%name, self, 'clock') # possibly a better connection name than 'clock'?
        # Create the internal direct output clock_line
        self._direct_output_clock_line = ClockLine('%s_direct_output_clock_line'%name, self.pseudoclock, 'internal', ramping_allowed = False)
        # Create the internal intermediate device connected to the above clock line
        # This will have the direct DigitalOuts of the NDPG connected to it
        self._direct_output_device = NarwhalDevicesPulseGeneratorDirectOutputs('%s_direct_output_device'%name, self._direct_output_clock_line)

        if self.use_wait_monitor:
            # Create internal devices for connecting to a wait monitor
            self.__wait_monitor_dummy_pseudoclock = _NDPGDummyPseudoclock(
                "%s__dummy_wait_pseudoclock" % name, self, "_"
            )
            self.__wait_monitor_dummy_clock_line = _NDPGDummyClockLine(
                "%s__dummy_wait_clock_line" % name,
                self.__wait_monitor_dummy_pseudoclock,
                "_",
            )
            self.__wait_monitor_intermediate_device = (
                _NDPGDummyIntermediateDevice(
                    "%s_internal_wait_monitor_outputs" % name,
                    self.__wait_monitor_dummy_clock_line,
                )
            )

            # Create the wait monitor
            WaitMonitor(
                "%s__wait_monitor" % name,
                self.internal_wait_monitor_outputs,
                "internal",
                self.internal_wait_monitor_outputs,
                "internal",
                self.internal_wait_monitor_outputs,
                "internal",
            )    

    @property
    def internal_wait_monitor_outputs(self):
        return self.__wait_monitor_intermediate_device

    @property
    def pseudoclock(self):
        return self._pseudoclock
        
    @property
    def direct_outputs(self):
        return self._direct_output_device

    def add_device(self, device):
        if len(self.child_devices) <= 2 and isinstance(device, Pseudoclock):
            PseudoclockDevice.add_device(self, device)
        elif isinstance(device, Pseudoclock):
            raise LabscriptError(f'The {self.name} PseudoclockDevice only supports a single Pseudoclock, so it automatically creates one.' +
                                 f'Instead of instantiating your own Pseudoclock object, please use the internal one stored in {self.name}.pseudoclock' +
                                 f'A DummyPseudoclock is also created internally to support the internal WaitMonitor, but it is also added automatically.')
        elif isinstance(device, DigitalOut):
            raise LabscriptError(f'You have connected {device.name} directly to {self.name}, which is not allowed. You should instead specify ' + 
                                 f'the parent_device of {device.name} as {self.name}.direct_outputs')
        elif isinstance(device, ClockLine):
            raise LabscriptError(f'You have connected {device.name} directly to {self.name}, which is not allowed. You should instead specify ' + 
                                 f'the parent_device of {device.name} as {self.name}.pseudoclock')
        else:
            raise LabscriptError(f'You have connected {device.name} (class {device.__class__}) to {self.name}, but {self.name} does not support children with that class.')
                        
    def channel_valid(self, channel):
        if -1 < channel < self.n_channels:
            return True
        return False     
        
    def channel_is_clock(self, channel):
        for clock_line in self.pseudoclock.child_devices:
            if clock_line.connection == 'internal': #ignore internal clockline
                continue
            if channel == self.get_channel_number(clock_line.connection):
                return True
        return False
            
    def get_channel_number(self, connection):
        # TODO: Error checking
        prefix, connection = connection.split()
        return int(connection)
    
    def get_direct_outputs(self):
        """Finds out which outputs are directly attached to the PulseBlaster"""
        dig_outputs = []
        for output in self.direct_outputs.get_all_outputs():
            if isinstance(output, DigitalOut):
                # get connection number and prefix
                try:
                    prefix, connection = output.connection.split()
                    assert prefix == 'channel'# or prefix == 'dds'
                    connection = int(connection)
                except:
                    raise LabscriptError('%s %s has invalid connection string: \'%s\'. '%(output.description,output.name,str(output.connection)) + 
                                         'Format must be \'channel n\' with n an integer less than %d.'%self.n_channels)
                # run checks on the connection string to make sure it is valid
                # TODO: Most of this should be done in add_device() No?
                if prefix == 'channel' and not self.channel_valid(connection):
                    raise LabscriptError('%s is set as connected to flag %d of %s. '%(output.name, connection, self.name) +
                                         'Output flag number must be a integer from 0 to %d.'%(self.n_channels-1))
                if prefix == 'channel' and self.channel_is_clock(connection): 
                    raise LabscriptError('%s is set as connected to channel %d of %s.'%(output.name, connection, self.name) +
                                         ' This channel is already in use as one of the Pulse Generator\'s clock channels.')                         
                
                # Check that the connection string doesn't conflict with another output
                for other_output in dig_outputs:# + dds_outputs:
                    if output.connection == other_output.connection:
                        raise LabscriptError('%s and %s are both set as connected to %s of %s.'%(output.name, other_output.name, output.connection, self.name))
                
                # store a reference to the output
                if isinstance(output, DigitalOut):
                    dig_outputs.append(output)
                # elif isinstance(output, DDS) or isinstance(output, PulseBlasterDDS):
                #     dds_outputs.append(output) 
                
        return dig_outputs

  
    def generate_code(self, hdf5_file):
        # Generate the hardware instructions
        self.init_device_group(hdf5_file)
        PseudoclockDevice.generate_code(self, hdf5_file)

        ndpg_inst = self.pseudo_inst_to_ndpg_inst()
        self.write_ndpg_inst_to_h5(ndpg_inst, hdf5_file)
        
        # I might need this in the blacs_workers bit for a couple of reasons:
        # 1. If I am the master, then
        self.set_property("is_master_pseudoclock", self.is_master_pseudoclock, location="device_properties",)

    def sec_to_cyc(self, object_in_seconds):
        cycle_period = 10E-9
        if isinstance(object_in_seconds, list):
            return [int(round(element/cycle_period)) for element in object_in_seconds]
        elif isinstance(object_in_seconds, tuple):  
            return (int(round(element/cycle_period)) for element in object_in_seconds)
        return int(round(object_in_seconds/cycle_period))

    def pseudo_inst_to_ndpg_inst(self):
        ''' I think there are some large errors in here at the moment, but I on't want to deal with them yet. The 
        instructions that get generated seem to have way more shit in them than they should. but I'll deal with it another time.'''

        dig_outputs = self.direct_outputs.get_all_outputs()
        # for attr in dir(dig_outputs[0]):
        #     print('obj.%s = %r'%(attr, getattr(dig_outputs[0], attr)))

        # for attr in dir(self._direct_output_clock_line):
        #     print('obj.%s = %r'%(attr, getattr(self._direct_output_clock_line, attr)))

        print(compiler.wait_table)
        print(type(compiler.wait_table))
        # the wait table keys are the times in floats. Sort them so we can access them by index.
        # Note, this will break if 
        wait_table = [compiler.wait_table[key] for key in sorted(compiler.wait_table)]

        print(type(self.pseudoclock.clock))
        assert len(wait_table) == self.pseudoclock.clock.count('WAIT')
        print('goop')
        print(wait_table)

        channel_state = np.ones(24, dtype=np.int64)*-1 #-1 indicates that no value has been specified in the labscript experiment, so keep whatever value is set in the blacs GUI.
        # raw_output_idx = 0
        raw_output_idx = -1
        address = 0
        ndpg_inst = []
        ACsync = False
        next_instruction_notify = False
        wait_idx = 0
        for instruction in self.pseudoclock.clock:
            # print('############################################################################################################')
            # print(instruction)
            # print()

            if instruction == 'WAIT':                
                ACsync = wait_table[wait_idx][0].startswith('ACsync')   # this is temproarily saved and reset to False after it is put in an instruction.
                wait_idx += 1
                print('ACsync ', ACsync)

                # Change the previous instruction to have a stop_and_wait=True
                # If this is the first instruction, add it to the start
                # it it is an ACsync wait, you have to add two instructions. The first instruction of the pulse generator must not be a powerline_sync instruction, as
                # it will respond the moment it is loaded into memory.

                # Things to fix!!!!!!!! There is some bug in the powerline delay gui spinbox that make you not be able to make a 1 ms. you can make 1.0 ms. look into it.
                # Need to set the powerline delay at the end of programming in blacs_worker.

                if len(ndpg_inst) == 0:
                    if ACsync:
                        # The first instruction can't be a powerline_sync instruction, so you actually have to add TWO instructions.
                        ndpg_inst.append({'address':address,
                                        'duration':1,
                                        'channel_state':channel_state.copy(),
                                        'goto_address':0,
                                        'goto_counter':0,
                                        'stop_and_wait':True,
                                        'hardware_trig_out':False,
                                        'notify_computer':True,
                                        'powerline_sync':False})
                        address += 1   
                        ndpg_inst.append({'address':address,
                                    'duration':1,
                                    'channel_state':channel_state.copy(),
                                    'goto_address':0,
                                    'goto_counter':0,
                                    'stop_and_wait':False,
                                    'hardware_trig_out':False,
                                    'notify_computer':True,
                                    'powerline_sync':True})
                        address += 1  
                    else:                
                        ndpg_inst.append({'address':address,
                                        'duration':1,
                                        'channel_state':channel_state.copy(),
                                        'goto_address':0,
                                        'goto_counter':0,
                                        'stop_and_wait':True,
                                        'hardware_trig_out':False,
                                        'notify_computer':True,
                                        'powerline_sync':False})
                        address += 1
                        next_instruction_notify = True
                    ACsync = False
                else:
                    ndpg_inst[-1]['stop_and_wait'] = True
                    ndpg_inst[-1]['notify_computer'] = True
                    next_instruction_notify = True
                continue

            # This flag indicates whether we need a full clock tick, or are just updating an internal output
            only_internal = True
            for clock_line in instruction['enabled_clocks']:
                if clock_line == self._direct_output_clock_line: 
                    # advance i (the index keeping track of internal clockline output)
                    raw_output_idx += 1
                else:
                    # This is the upwards tick of a clock line. 
                    channel = int(clock_line.connection.split()[1]) #The channel that the clockline is associated with
                    channel_state[channel] = 1 #upwards tick means it must be 1.
                    # print(f'raw_output_idx={raw_output_idx}, clock_line.connection={clock_line.connection}')

                    # We are also using other clocklines to clock external devices
                    only_internal = False

            # Set the output state for each channel specified
            for output in dig_outputs:
                channel = int(output.connection.split()[1])
                channel_state[channel] = output.raw_output[raw_output_idx]


            if only_internal:
                print('only internal address:', address)
                # We only need to update a direct output, so no need to tick the clocks.
                duration = int(np.round((instruction['step']/self.clock_resolution)))
                ndpg_inst.append({'address':address,
                                'duration':duration,
                                'channel_state':channel_state.copy(),
                                'goto_address':0,
                                'goto_counter':0,
                                'stop_and_wait':False,
                                'hardware_trig_out':False,
                                'notify_computer':next_instruction_notify,
                                'powerline_sync':ACsync})
                ACsync = False
                next_instruction_notify = False
                # raw_output_idx += 1
                address +=1   
            else:
                print('external:', address)
                # We are also using other clocklines to clock external devices
                if self.pulse_width == 'symmetric':
                    high_time = instruction['step']/2
                else:
                    high_time = self.pulse_width
                low_time = instruction['step'] - high_time

                # create the rising edge instruction
                duration = int(np.round((high_time/self.clock_resolution)))
                ndpg_inst.append({'address':address,
                                'duration':duration,
                                'channel_state':channel_state.copy(),
                                'goto_address':0,
                                'goto_counter':0,
                                'stop_and_wait':False,
                                'hardware_trig_out':False,
                                'notify_computer':next_instruction_notify,
                                'powerline_sync':ACsync})
                ACsync = False
                next_instruction_notify = False
                loop_start_address = address
                address += 1

                # For all clocklines that this seudo-psudoclock instruction relates to, get
                #its channel, and set it to 0, since this is were it transitions to low.
                for clock_line in instruction['enabled_clocks']:
                    if clock_line != self._direct_output_clock_line: #ignore the direct outputs, you have already set those states
                        channel = int(clock_line.connection.split()[1]) #The channel that the clockline is associated with
                        channel_state[channel] = 0
                
                # goto_counter on NDPG operates slightly differently to instruction['reps']
                if instruction['reps'] == 0:
                    goto_counter = 0
                else:
                    goto_counter = instruction['reps'] - 1
                duration = int(np.round((low_time/self.clock_resolution)))
                ndpg_inst.append({'address':address,
                                'duration':duration,
                                'channel_state':channel_state.copy(),
                                'goto_address':loop_start_address,
                                'goto_counter':goto_counter,
                                'stop_and_wait':False,
                                'hardware_trig_out':False,
                                'notify_computer':False,
                                'powerline_sync':False})
                address += 1

        return ndpg_inst


    def write_ndpg_inst_to_h5(self, ndpg_inst, hdf5_file):
        # OK now we squeeze the instructions into a numpy array ready for writing to hdf5:
        inst_table_dtype = [('address', np.int64), ('duration', np.int64), ('goto_address', np.int64), ('goto_counter', np.int64),
                     ('stop_and_wait', np.bool), ('hardware_trig_out', np.bool), ('notify_computer', np.bool), ('powerline_sync', np.bool),
                     ('channel_state', np.int64, (24))]
        inst_table = np.empty(len(ndpg_inst),dtype = inst_table_dtype)
        for i, inst in enumerate(ndpg_inst):
            inst_table[i] = (inst['address'], inst['duration'], inst['goto_address'], inst['goto_counter'], 
                          inst['stop_and_wait'], inst['hardware_trig_out'], inst['notify_computer'], inst['powerline_sync'], inst['channel_state'])


        # Okay now write it to the file: 
        group = hdf5_file['/devices/'+self.name]  
        group.create_dataset('PULSE_PROGRAM', compression=config.compression,data = inst_table)   
        self.set_property('stop_time', self.stop_time, location='device_properties')


class NarwhalDevicesPulseGeneratorDirectOutputs(IntermediateDevice):
    allowed_children = [DigitalOut]
    clock_limit = NarwhalDevicesPulseGenerator.clock_limit
    description = 'Narwhal Devices Pulse Generator Direct Outputs'
  
    def add_device(self, device):
        IntermediateDevice.add_device(self, device)




    '''Required Properties:

    These can be set as attributes of the class, since all instances of this class must have these properties
    description
    
    DONE clock_limit.   is equal to 1/minimum pulse width. See line 822.
                    VERDICT: REQUIRED. SET TO 100MHz. add to device_properties.

    NOT NEEDED. minimum_clock_high_time. For Intermediate device is it : minimum_clock_high_time=1/self.clock_limit/2 (which if the clock_limit is 100MHz the minimum_clock_high_time=5ns.
                                            But maybe this is a hack so that Internal intermediated devices CAN output at the full clock limit, because it is AS THOUGH it can 
                                            respond to 5ns high sichnals (which would have a 10ns period.)
                                For ClockLine it is retrieved from its parent device (which is a psudoclock).
                                In Psudoclock, it is used to calculate the 
                                think this is always derived from clock limit, so I don't need to set it directly. It may be derived in a different way for each different class,
                            so you might have to check which one is applicable.
                                VERDITCT: DONT SET DIRECTLY.


    DONE clock_resolution    used to quantise the instruction timing. # quantise the times to the pseudoclock clock resolution
                        times = (times/self.pseudoclock_device.clock_resolution).round()*self.pseudoclock_device.clock_resolution
                        Not exactly sure how this differes from the inverse of clock_limit. Probably in the case where devices have a different
                        minimum pulse width to their resolution. But it is a bit of a funny way to specify it. 
                        VERDICT: REQUIRED. SET TO 10ns. add to device_properties. All pseudoclock devices need this set.

    
    DONE trigger_delay : # How long after a trigger the next instruction is actually output: line 1266.
                    Does not actually get called from device_properties (it gets defined in PseudoclockDevice(TriggerableDevice)
                    and then you just overwrite it), but add it anyway for the record. (Thechnicly only required when the
                    psudoclock in the psudoclock_device is not the master pseudoclock)
                    VERDICT: REQUIRED. Set to 40ns. 

    DONE.trigger_minimum_duration: # How long a trigger line must remain high/low in order to be detected.
                                Same as Trigger Delay. Does not actually get called from device_properties (it gets defined in PseudoclockDevice(TriggerableDevice)
                                and then you just overwrite it), but add it anyway for the record.
                                VERDICT: REQUIRED. Set to 10ns. 

    DONE. minimum_recovery_time: Again, not strictly required since defaults are always specified, but good to make explicit.
                            VERDICT: REQUIRED. set to 20ns.

    DONE wait_delay: Not as sure what this is. but confident it is 0ns for me. Same as trgger_delay and trigger_minimu_duration.
                VERDICT: REQUIRED. set to 0.


    DONE. trigger_edge_type = 'rising' : Not technically required, since all base classes already define this,
                        but I should put it in becase it is good to make it explicit. (does putting it in overwrite
                        the properties in the base class: yes)

    DONE. max_instructions: self explanatory, but NOT used by any base class, since they don't know how how you
                        will turn pseudoclock instructions into device instructions.
                        VERDICT: NOT REQUIRED, BUT ADD FOR USEFUL INFO.

    
    ###################################################
    These are passes in as arguments, since depending on the setup, they may change, so should be stored in 
    either connection_table_properties or  device_properties

    trigger_device: Pass to init of PseudoClockDecice. Dont need to save in device properties
                    VERDICT: REQUIRED (use Args description for prawnblaster). connection_table_properties
    
    trigger_connection: Pass to init of PseudoClockDecice. Dont need to save in device properties
                    VERDICT: REQUIRED (use Args description for prawnblaster). connection_table_properties

                    
    accept_hardware_trigger: pass in?? If master, needs software for start, but maybe hardware for restart.
                    if secondary, only need hardware. So, pass in with default as 'either'. connection_table_properties
                    
    trigger_on_powerline: pass in. device_properties

    powerline_trigger_delay: pass in. device_properties

    trigger_out_length: pass in. device_properties

    serial_number: connection_table_properties

    firmware: See if I can pass this back up the ladder from the BLACS worker. might be a little tricky? device_properties
             
'''
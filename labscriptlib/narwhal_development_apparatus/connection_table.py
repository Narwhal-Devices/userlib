from labscript import start, stop, add_time_marker, AnalogOut, DigitalOut, ClockLine, wait, Trigger
from user_devices.NarwhalDevicesPulseGenerator.labscript_devices import NarwhalDevicesPulseGenerator

from labscript_devices.DummyIntermediateDevice import DummyIntermediateDevice

NarwhalDevicesPulseGenerator(name='Narwhal_Devices_Pulse_Generator', serial_number='12582915')

#Connect DigitalOut to things like RF switches powering AOMs. This allows you to turn the AOM on or OFF at given times
DigitalOut(name='digital_out1', parent_device=Narwhal_Devices_Pulse_Generator.direct_outputs, connection='channel 0')
DigitalOut(name='digital_out2', parent_device=Narwhal_Devices_Pulse_Generator.direct_outputs, connection='channel 1')

#Connect Triggers to things like camera shutters, or other Pulse Generators (or pseudoclocks). Triggers are the same 
# as DigitalOut, except there are a couple of convenience features. eg. You just specitfy an output time, and duration. 
# You donh have to explicitly call it to go high at one time, and low at another.
Trigger(name='camera_trigger', parent_device=Narwhal_Devices_Pulse_Generator.direct_outputs, connection='channel 2')

#Connect ClockLines to things like NI cards, where each rising (or falling) edge makes the NI card output its next value
ClockLine(name='narwhalpulsegen_clock1', pseudoclock=Narwhal_Devices_Pulse_Generator.pseudoclock, connection='channel 3')
ClockLine(name='narwhalpulsegen_clock2', pseudoclock=Narwhal_Devices_Pulse_Generator.pseudoclock, connection='channel 4')

# I don't know if this will work, but I need to make a device that will accecpt ramps and stuff so I can figure out how
# to deal with reay clocklines rather than just direct digital outputs
# I think this is how it is supposed to be assigned a parent. See Phil's thesis P86 Fig 5.6
DummyIntermediateDevice(name='dummy_device', parent_device=narwhalpulsegen_clock1)
DigitalOut(name='do1',parent_device=dummy_device, connection='dummy_do1')
AnalogOut(name='analog_out', parent_device=dummy_device, connection='ao0')

if __name__ == '__main__':
    # Begin issuing labscript primitives
    # start() elicits the commencement of the shot
    start()

    # Stop the experiment shot with stop()
    stop(1.0)
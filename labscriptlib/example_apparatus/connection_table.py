from labscript import start, stop, add_time_marker, AnalogOut, DigitalOut, ClockLine
from labscript_devices.DummyIntermediateDevice import DummyIntermediateDevice

from user_devices.NarwhalPulseGen.labscript_devices import NarwhalPulseGen

NarwhalPulseGen(name='narwhal_pulsegen', usbport='autodetect')

DigitalOut(name='digital_out1', parent_device=narwhal_pulsegen.direct_outputs, connection='channel 1')
DigitalOut(name='digital_out2', parent_device=narwhal_pulsegen.direct_outputs, connection='channel 2')

ClockLine(name='narwhalpulsegen_clock1', pseudoclock=narwhal_pulsegen.pseudoclock, connection='channel 0')

DummyIntermediateDevice(name='intermediate_device', parent_device=narwhalpulsegen_clock1)
AnalogOut(name='analog_out', parent_device=intermediate_device, connection='ao0')


if __name__ == '__main__':
    # Begin issuing labscript primitives
    # start() elicits the commencement of the shot
    start()

    # Stop the experiment shot with stop()
    stop(1.0)
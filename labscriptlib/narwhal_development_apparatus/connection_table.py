from labscript import start, stop, add_time_marker, AnalogOut, DigitalOut, ClockLine, wait
from user_devices.NarwhalPulseGenPulseblasterTemplate.labscript_devices import PulseBlasterUSB

PulseBlasterUSB(name='my_test_pulseblaster')

ClockLine(name='narwhalpulsegen_clock1', pseudoclock=my_test_pulseblaster.pseudoclock, connection='flag 0')

'''Im not sure if this is allowed. I think a Pulseblaster is only allowed to have pseudoclock children
To create digital outs, I might have to make a PulseBlasterDirectOutputs device (which is an IntermediateDevice),
and then make DigitalOut with PulseBlasterDirectOutputs as a parent.
OR...
It is possible that when I call DigitalOut with a my_test_pulseblaster.direct_outputs parent, that the IntermediateDevice
gets automatically created. (This would make sence, and be convenient, but what magic makes this happen I dont know.)

ANSWER:
The my_test_pulseblaster.direct_outputs IS AN INTEMEDIATE DEVICE
look at the labscript_devices.py file. direct_outputs is a property that returns self._direct_output_device, 
which is just an instance of PulseBlasterDirectOutputs, which itself is just a subclass of IntermediateDevice, with a 
couple of extra things thrown in.

'''
DigitalOut(name='digital_out1', parent_device=my_test_pulseblaster.direct_outputs, connection='flag 1')
DigitalOut(name='digital_out2', parent_device=my_test_pulseblaster.direct_outputs, connection='flag 2')



if __name__ == '__main__':
    # Begin issuing labscript primitives
    # start() elicits the commencement of the shot
    start()

    # Stop the experiment shot with stop()
    stop(1.0)
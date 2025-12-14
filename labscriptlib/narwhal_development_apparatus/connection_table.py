from labscript import start, stop, add_time_marker, wait, AnalogOut, DigitalOut, ClockLine, Trigger
from user_devices.NarwhalDevicesPulseGenerator.labscript_devices import NarwhalDevicesPulseGenerator

NarwhalDevicesPulseGenerator(name='master', serial_number='12582915')
DigitalOut(name='master_DO0', parent_device=master.direct_outputs, connection='channel 0')
DigitalOut(name='master_DO1', parent_device=master.direct_outputs, connection='channel 1')
Trigger(name='master_test_trigger', parent_device=master.direct_outputs, connection='channel 2')


NarwhalDevicesPulseGenerator(name='slave', serial_number='12582917', trigger_device=master.direct_outputs, trigger_connection='channel 16')
DigitalOut(name='slave_DO0', parent_device=slave.direct_outputs, connection='channel 0')



# to do: mahe the status check in blacs only depen on if the running is true. will delay by max 1swconf but is very simple and dependable

if __name__ == '__main__':
    # Begin issuing labscript primitives
    # start() elicits the commencement of the shot
    start()

    # Stop the experiment shot with stop()
    stop(1.0)
from labscript import start, stop, add_time_marker, wait, AnalogOut, DigitalOut, ClockLine, Trigger
from user_devices.NarwhalDevicesPulseGenerator.labscript_devices import NarwhalDevicesPulseGenerator

NarwhalDevicesPulseGenerator(name='NDPG0', serial_number='12582915')
DigitalOut(name='NDPG0_DO0', parent_device=NDPG0.direct_outputs, connection='channel 0')


NarwhalDevicesPulseGenerator(name='NDPG1', serial_number='12582917', trigger_device=NDPG0.direct_outputs, trigger_connection='channel 23')
DigitalOut(name='NDPG1_DO0', parent_device=NDPG1.direct_outputs, connection='channel 0')


if __name__ == '__main__':
    # Begin issuing labscript primitives
    # start() elicits the commencement of the shot
    start()

    # Stop the experiment shot with stop()
    stop(1.0)
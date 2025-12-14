from labscript import start, stop, add_time_marker, wait, AnalogOut, DigitalOut, ClockLine, Trigger
from user_devices.NarwhalDevicesPulseGenerator.labscript_devices import NarwhalDevicesPulseGenerator

NarwhalDevicesPulseGenerator(name='NDPG0', serial_number='12582915')
DigitalOut(name='NDPG0_DO0', parent_device=NDPG0.direct_outputs, connection='channel 0')
DigitalOut(name='NDPG0_DO1', parent_device=NDPG0.direct_outputs, connection='channel 1')

Trigger(name='test_trigger', parent_device=NDPG0.direct_outputs, connection='channel 2')


if __name__ == '__main__':

    # Wait simple manual digital out only. (Comment out clockline and intermediate device stuff)
    t = 0
    start()
    NDPG0_DO0.go_high(t)
    NDPG0_DO1.go_high(t)
    t += 1.5
    
    NDPG0_DO0.go_low(t)
    t += 0.5

    NDPG0_DO0.go_high(t)
    t += 1

    test_trigger.trigger(t, 15E-3)
    t += 0.25

    # t += wait('ACsync_my_test_wait', t, timeout = 2)

    NDPG0_DO0.go_low(t)
    NDPG0_DO1.go_low(t)
    
    # t += wait('hardware_trig_test', t, timeout = 2)
    # NDPG0_DO0.go_high(t) 
    # NDPG1_DO0.go_high(t)
    # t += 1.0E-6
    # NDPG0_DO0.go_low(t)
    # NDPG1_DO0.go_low(t)

    stop(t)

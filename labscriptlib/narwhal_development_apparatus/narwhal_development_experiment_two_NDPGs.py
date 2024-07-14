from labscript import start, stop, add_time_marker, wait, AnalogOut, DigitalOut, ClockLine, Trigger
from user_devices.NarwhalDevicesPulseGenerator.labscript_devices import NarwhalDevicesPulseGenerator

NarwhalDevicesPulseGenerator(name='NDPG0', serial_number='12582915')
DigitalOut(name='NDPG0_DO0', parent_device=NDPG0.direct_outputs, connection='channel 0')


NarwhalDevicesPulseGenerator(name='NDPG1', serial_number='12582917', trigger_device=NDPG0.direct_outputs, trigger_connection='channel 16')
DigitalOut(name='NDPG1_DO0', parent_device=NDPG1.direct_outputs, connection='channel 0')


if __name__ == '__main__':

    # t = 0
    # start()
    # NDPG0_DO0.go_high(t)
    # t += 400E-9 
    # NDPG1_DO0.go_high(t)

    # t += 1
    # NDPG0_DO0.go_low(t)
    # NDPG1_DO0.go_low(t)

    # t += 1
    # NDPG0_DO0.go_high(t)
    # NDPG1_DO0.go_high(t)

    # t += 1
    # NDPG0_DO0.go_low(t)
    # NDPG1_DO0.go_low(t)

    # Wait simple manual digital out only. (Comment out clockline and intermediate device stuff)
    t = 0
    start()
    NDPG0_DO0.go_high(t)
    t += 40E-9 
    NDPG1_DO0.go_high(t)


    t += 1.5E-6
    t += 3
    # t += wait('ACsync_my_test_wait', t, timeout = 2)
    NDPG0_DO0.go_low(t)
    NDPG1_DO0.go_low(t)
    # t+= 1.0
    
    # t += wait('hardware_trig_test', t, timeout = 2)
    # NDPG0_DO0.go_high(t) 
    # NDPG1_DO0.go_high(t)
    # t += 1.0E-6
    # NDPG0_DO0.go_low(t)
    # NDPG1_DO0.go_low(t)

    stop(t)

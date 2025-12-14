from labscript import start, stop, add_time_marker, wait, AnalogOut, DigitalOut, ClockLine, Trigger
from user_devices.NarwhalDevicesPulseGenerator.labscript_devices import NarwhalDevicesPulseGenerator

NarwhalDevicesPulseGenerator(name='master', serial_number='12582915')
DigitalOut(name='master_DO0', parent_device=master.direct_outputs, connection='channel 0')
DigitalOut(name='master_DO1', parent_device=master.direct_outputs, connection='channel 1')
Trigger(name='master_test_trigger', parent_device=master.direct_outputs, connection='channel 2')


NarwhalDevicesPulseGenerator(name='slave', serial_number='12582917', trigger_device=master.direct_outputs, trigger_connection='channel 16')
DigitalOut(name='slave_DO0', parent_device=slave.direct_outputs, connection='channel 0')


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
    master_DO0.go_high(t)
    t += 1E-6 
    
    slave_DO0.go_high(t)
    t += 3E-6

    # master_test_trigger.trigger(t, 20E-6)
    # t += 30E-6
    
    # t += wait('ACsync_my_test_wait', t, timeout = 2)
    master_DO0.go_low(t)
    slave_DO0.go_low(t)
    # t+= 1.0
    
    # t += wait('hardware_trig_test', t, timeout = 2)
    # NDPG0_DO0.go_high(t) 
    # NDPG1_DO0.go_high(t)
    # t += 1.0E-6
    # NDPG0_DO0.go_low(t)
    # NDPG1_DO0.go_low(t)

    stop(t)

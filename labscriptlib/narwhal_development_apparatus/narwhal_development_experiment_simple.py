from labscript import start, stop, add_time_marker, wait, AnalogOut, DigitalOut, ClockLine, Trigger
from user_devices.NarwhalDevicesPulseGenerator.labscript_devices import NarwhalDevicesPulseGenerator

NarwhalDevicesPulseGenerator(name='NDPG0', serial_number='12582915')
DigitalOut(name='NDPG0_DO0', parent_device=NDPG0.direct_outputs, connection='channel 0')



if __name__ == '__main__':

    # Wait simple manual digital out only. (Comment out clockline and intermediate device stuff)
    t = 0
    start()
    NDPG0_DO0.go_high(t)
    t += 40E-9
    t += 4

    # I THINK THERE IS A BUG IN THE FPGA CODE THAT RESETS THE RUN TIME TO ZERO AT THE END OF THE RUN, BUT THEN KEEPS IT COUNTING?
    # THE IS WHAT IT LOOKS LIKE FROM BLLOKNG AT THE BLACS TAB AT THE END OF THE RUN. IT RESETS TO ZERO THEN KEEPS COUNTING.

    # t += wait('ACsync_my_test_wait', t, timeout = 2)
    NDPG0_DO0.go_low(t)

    
    # t += wait('hardware_trig_test', t, timeout = 2)
    # NDPG0_DO0.go_high(t) 
    # NDPG1_DO0.go_high(t)
    # t += 1.0E-6
    # NDPG0_DO0.go_low(t)
    # NDPG1_DO0.go_low(t)

    stop(t)

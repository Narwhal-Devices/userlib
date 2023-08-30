from labscript import start, stop, add_time_marker, AnalogOut, DigitalOut, ClockLine, wait, Trigger
from user_devices.NarwhalDevicesPulseGenerator.labscript_devices import NarwhalDevicesPulseGenerator

from labscript_devices.DummyIntermediateDevice import DummyIntermediateDevice

NarwhalDevicesPulseGenerator(name='Narwhal_Devices_Pulse_Generator', serial_number='12582915')

#Connect DigitalOut to things like RF switches powering AOMs. This allows you to turn the AOM on or OFF at given times
DigitalOut(name='digital_out1', parent_device=Narwhal_Devices_Pulse_Generator.direct_outputs, connection='channel 0')
DigitalOut(name='digital_out2', parent_device=Narwhal_Devices_Pulse_Generator.direct_outputs, connection='channel 1')

# #Connect Triggers to things like camera shutters, or other Pulse Generators (or pseudoclocks). Triggers are the same 
# # as DigitalOut, except there are a couple of convenience features. eg. You just specitfy an output time, and duration. 
# # You donh have to explicitly call it to go high at one time, and low at another.
Trigger(name='camera_trigger', parent_device=Narwhal_Devices_Pulse_Generator.direct_outputs, connection='channel 2')

#Connect ClockLines to things like NI cards, where each rising (or falling) edge makes the NI card output its next value
# ClockLine(name='narwhalpulsegen_clock1', pseudoclock=Narwhal_Devices_Pulse_Generator.pseudoclock, connection='channel 3')
# DummyIntermediateDevice(name='dummy_device', parent_device=narwhalpulsegen_clock1)
# AnalogOut(name='analog_out', parent_device=dummy_device, connection='ao0')
# DigitalOut(name='do1',parent_device=dummy_device, connection='dummy_do1')

# ClockLine(name='narwhalpulsegen_clock2', pseudoclock=Narwhal_Devices_Pulse_Generator.pseudoclock, connection='channel 4')


if __name__ == '__main__':

    # Wait simple manual digital out only. (Comment out clockline and intermediate device stuff)
    t = 0
    start()
    digital_out1.go_high(t)
    t += 10E-9
    digital_out1.go_low(t)
    t += 20E-9
    t += wait ('my_test_wait', t , timeout = 2 )
    # t += 20E-9
    digital_out1.go_high(t)
    t += 30E-9
    digital_out1.go_low(t)
    stop(t)


    # # simple manual digital out only. (Comment out clockline and intermediate device stuff)
    # t = 0
    # start()
    # digital_out1.go_high(t)
    # t += 10E-9
    # digital_out1.go_low(t)
    # t += 20E-9
    # digital_out1.go_high(t)
    # t += 30E-9
    # digital_out1.go_low(t)
    # stop(t)

    # # simple ramp.
    # t = 0
    # start()
    # t += analog_out.ramp(t=t, initial=0.0, final=1.0, duration=10E-6, samplerate=1e6)
    # stop(t)

    # # simple ramp and direct outputs
    # t = 0
    # start()
    # t += analog_out.ramp(t=t, initial=0.0, final=1.0, duration=10E-6, samplerate=1e6)
    # digital_out1.go_high(4.88E-6)
    # digital_out1.go_low(6.0E-6)
    # t = 10E-6
    # stop(t)

    # # more complex digital out only. (Comment out clockline and intermediate device stuff)
    # t = 0
    # start()
    # digital_out1.go_high(t)
    # digital_out2.go_high(t)
    # t += 10E-9
    # digital_out1.go_low(t)
    # camera_trigger.trigger(t, 30E-9) # 30E-9 and 60E-9 don't work. But it is allowing 5E-9 
    # t += 20E-9
    # digital_out1.go_high(t)
    # digital_out2.go_low(t)
    # t += 30E-9
    # digital_out1.go_low(t)
    # stop(t)

    # Begin issuing labscript primitives
    # A timing variable t is used for convenience
    # start() elicits the commencement of the shot
    # t = 0
    # add_time_marker(t, "Start", verbose=True)
    # start()

    # # Wait for 20 nanosecond with all devices in their default state
    # t += 20E-9

    # # Change the state of digital_out, and denote this using a time marker
    # add_time_marker(t, "Toggle digital_out (high)", verbose=True)
    # digital_out1.go_high(t)

    # # Wait for 10 nanoseconds
    # t += 10E-9

    # # # Ramp analog_out from 0.0 V to 1.0 V over 0.25 s with a 1 kS/s sample rate
    # # t += analog_out.ramp(t=t, initial=0.0, final=1.0, duration=0.25, samplerate=1e3)

    # # Change the state of digital_out, and denote this using a time marker
    # add_time_marker(t, "Toggle digital_out (low)", verbose=True)
    # digital_out1.go_low(t)

    # # Wait for 2 seconds
    # t += 3

    # # Stop the experiment shot with stop()
    # stop(t)


    #############################################################################
    # Examples that expose labscript bugs.
    # I am pretty sure this is not a problem with my implementation of the labscript
    # device, but with the pseudoinscruction in labscript itself



    # The check to see if the change times are too close to each other can fail because subtracting large, 
    # similar numbers. Not actually sure if it errors with these numbers, but test a few and you will find
    # some. (I don't anymore because I modified my labscript.py)

    # t = 0
    # start()
    # # digital_out1.go_high(5.0E-6)
    # # digital_out1.go_low(5.01E-6)
    # stop(t)


    # File "C:\Users\rorys\anaconda3\lib\site-packages\labscript\labscript.py", line 1063, in expand_change_times
    # clock.append({'start': ticks[-1], 'reps': 1, 'step': all_change_times[i+1] - ticks[-1], 'enabled_clocks':enabled_clocks if n_ticks == 1 else enabled_looping_clocks})
    # IndexError: index -1 is out of bounds for axis 0 with size 0
    # Compilation aborted.

    # t = 0
    # start()
    # t += analog_out.ramp(t=t, initial=0.0, final=1.0, duration=10E-6, samplerate=1e6)
    
    # # Fine
    # # digital_out1.go_high(0.0E-6)
    # # digital_out1.go_low(1.0E-6)    

    # # Fine
    # # digital_out1.go_high(1.0E-6)
    # # digital_out1.go_low(2.0E-6)    
    
    # # Fine
    # # digital_out1.go_high(2.0E-6)
    # # digital_out1.go_low(3.0E-6)

    # # Error
    # digital_out1.go_high(3.0E-6)
    # digital_out1.go_low(4.0E-6)

    # # Fine
    # # digital_out1.go_high(3.0E-6)
    # # digital_out1.go_low(4.01E-6)

    # # Error
    # # digital_out1.go_high(5.0E-6)
    # # digital_out1.go_low(6.0E-6)

    # # Error
    # # digital_out1.go_high(6.0E-6)
    # # digital_out1.go_low(7.0E-6)

    # # Error
    # # digital_out1.go_high(7.0E-6)
    # # digital_out1.go_low(8.0E-6)

    # # Fine
    # # digital_out1.go_high(8.0E-6)
    # # digital_out1.go_low(9.0E-6)

    # # Fine
    # # digital_out1.go_high(9.0E-6)
    # # digital_out1.go_low(10.0E-6)
    # stop(t)


    # simple ramp and direct outputs. Compiles and runs, but changing between
    # 4.86E-6, 4.87E-6, 4.88E-6 doesn't happen correctly. Jumps straight from 6 to 8.
    # t = 0
    # start()
    # t += analog_out.ramp(t=t, initial=0.0, final=1.0, duration=10E-6, samplerate=1e6)
    # digital_out1.go_high(4.88E-6)
    # digital_out1.go_low(6.0E-6)
    # t = 10E-6
    # stop(t)
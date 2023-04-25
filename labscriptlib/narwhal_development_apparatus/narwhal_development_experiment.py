from labscript import start, stop, add_time_marker, AnalogOut, DigitalOut, ClockLine, wait, Trigger
from user_devices.NarwhalDevicesPulseGenerator.labscript_devices import NarwhalDevicesPulseGenerator

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


if __name__ == '__main__':
    # Begin issuing labscript primitives
    # A timing variable t is used for convenience
    # start() elicits the commencement of the shot
    t = 0
    add_time_marker(t, "Start", verbose=True)
    start()

    # Wait for 20 nanosecond with all devices in their default state
    t += 20E-9

    # Change the state of digital_out, and denote this using a time marker
    add_time_marker(t, "Toggle digital_out (high)", verbose=True)
    digital_out1.go_high(t)

    # Wait for 10 nanoseconds
    t += 10E-9

    # # Ramp analog_out from 0.0 V to 1.0 V over 0.25 s with a 1 kS/s sample rate
    # t += analog_out.ramp(t=t, initial=0.0, final=1.0, duration=0.25, samplerate=1e3)

    # Change the state of digital_out, and denote this using a time marker
    add_time_marker(t, "Toggle digital_out (low)", verbose=True)
    digital_out1.go_low(t)

    # Wait for 2 seconds
    t += 50E-9

    # Stop the experiment shot with stop()
    stop(t)
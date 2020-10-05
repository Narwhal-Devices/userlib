from labscript import start, stop, add_time_marker
import labscript_utils

labscript_utils.import_or_reload('labscriptlib.example_apparatus.connection_table')

# Begin issuing labscript primitives
# A timing variable t is used for convenience
# start() elicits the commencement of the shot
t = 0
add_time_marker(t, "Start", verbose=True)
start()
# Wait for 1 second with all devices in their default state
t += 1

# Change the state of digital_out, and denote this using a time marker
add_time_marker(t, "Toggle digital_out (high)", verbose=True)
digital_out1.go_high(t)
digital_out2.go_high(t)
# Wait for 0.5 seconds
t += 0.5
digital_out2.go_low(t)

# Ramp analog_out from 0.0 V to 1.0 V over 0.25 s with a 1 kS/s sample rate
t += analog_out.ramp(t=t, initial=0.0, final=1.0, duration=0.25, samplerate=1e3)

# Change the state of digital_out, and denote this using a time marker
add_time_marker(t, "Toggle digital_out (low)", verbose=True)
digital_out1.go_high(t)

# Wait for 0.5 seconds
t += 0.5

# Stop the experiment shot with stop()
stop(t)
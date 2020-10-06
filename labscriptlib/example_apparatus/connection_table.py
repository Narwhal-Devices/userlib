from labscript import start, stop, add_time_marker, AnalogOut, DigitalOut, ClockLine, wait
from labscript_devices.DummyIntermediateDevice import DummyIntermediateDevice
# from labscript_devices.DummyIntermediateDevice import NI_PCIe_6363, 

from user_devices.NarwhalPulseGen.labscript_devices import NarwhalPulseGen

NarwhalPulseGen(name='narwhal_pulsegen', usbport='autodetect')

DigitalOut(name='digital_out1', parent_device=narwhal_pulsegen.direct_outputs, connection='channel 1')
DigitalOut(name='digital_out2', parent_device=narwhal_pulsegen.direct_outputs, connection='channel 2')

ClockLine(name='narwhalpulsegen_clock1', pseudoclock=narwhal_pulsegen.pseudoclock, connection='channel 0')

DummyIntermediateDevice(name='intermediate_device', parent_device=narwhalpulsegen_clock1)
AnalogOut(name='analog_out', parent_device=intermediate_device, connection='ao0')


# NI_PCIe_6363 ( name =’ ni_pcie_6363_0 ’,
# parent_device = pineblaster0 . clockline ,
# clock_terminal =’/ ni_pcie_6363_0 / PFI0 ’,
# MAX_name =’ ni_pcie_6363_0 ’,
# acquisition_rate =1e3)
# WaitMonitor (’ wait_monitor ’,
# # flag that pulses after a wait
# ni_pcie_6363_0 , ’port0 / line0 ’,
# # counter that monitors the times the above flag goes high
# ni_pcie_6363_0 , ’ctr0 ’,
# # software timed output that retriggers the master
# # pseudoclock if the wait hits the timeout
# ni_pcie_6363_0 , ’PFI1 ’)

if __name__ == '__main__':
    # Begin issuing labscript primitives
    # start() elicits the commencement of the shot
    start()

    # Stop the experiment shot with stop()
    stop(1.0)
from labscript import start, stop, add_time_marker, wait, AnalogOut, DigitalOut, ClockLine, Trigger
from user_devices.NarwhalDevicesPulseGenerator.labscript_devices import NarwhalDevicesPulseGenerator

from labscript_devices.PulseBlaster import PulseBlaster
from labscript_devices.NI_PCIe_6363 import NI_PCIe_6363


PulseBlaster(name='pulseblaster_0', board_number=1)
ClockLine(name='pulseblaster_0_ni_clock', pseudoclock=pulseblaster_0.pseudoclock, connection='flag 0')

NI_PCIe_6363(name='ni_pcie_6363_0',parent_device=pulseblaster_0_ni_clock, clock_terminal='/ni_pcie_6363_0/PFI0', MAX_name='ni_pcie_6363_0',acquisition_rate=1e3)
DigitalOut( name='ni_pcie_6363_0_do', parent_device=ni_pcie_6363_0, connection="port0/line21")

PulseBlaster(name='pulseblaster_1', board_number=0, trigger_device=ni_pcie_6363_0,trigger_connection="port0/line22")
DigitalOut( name='test_out', parent_device=pulseblaster_1.direct_outputs, connection='flag 11')


if __name__ == '__main__':
    # Begin issuing labscript primitives
    # start() elicits the commencement of the shot
    start()

    # Stop the experiment shot with stop()
    stop(1.0)
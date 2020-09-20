import labscript_devices

labscript_device_name = 'NarwhalPulseGen'
blacs_tab = 'user_devices.NarwhalPulseGen.blacs_tabs.NarwhalPulseGenTab'
parser = 'user_devices.NarwhalPulseGen.runviewer_parsers.NarwhalPulseGenParser'
# Important! If changing from user_devices to labscript_devices, you must also change this in blacs_tabs.py -> NarwhalPulseGenTab -> initialise_workers

labscript_devices.register_classes(
    labscript_device_name=labscript_device_name,
    BLACS_tab=blacs_tab,
    runviewer_parser=parser,
)

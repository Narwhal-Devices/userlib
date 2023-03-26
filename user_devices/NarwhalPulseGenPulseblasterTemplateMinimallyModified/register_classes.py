import labscript_devices

labscript_device_name = 'PulseBlasterUSBLabscriptBaseClassesOnly'
blacs_tab = 'user_devices.NarwhalPulseGenPulseblasterTemplateMinimallyModified.blacs_tabs.PulseblasterUSBTab'
parser = 'user_devices.NarwhalPulseGenPulseblasterTemplateMinimallyModified.runviewer_parsers.PulseBlasterUSBParser'
# Important! If changing from user_devices to labscript_devices, you must also change this in blacs_tabs.py -> NarwhalPulseGenTab -> initialise_workers

labscript_devices.register_classes(
    labscript_device_name=labscript_device_name,
    BLACS_tab=blacs_tab,
    runviewer_parser=parser,
)

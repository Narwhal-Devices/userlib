#####################################################################
#                                                                   #
# /labscript_devices/PrawnBlaster/runviewer_parsers.py              #
#                                                                   #
# Copyright 2021, Philip Starkey                                    #
#                                                                   #
# This file is part of labscript_devices, in the labscript suite    #
# (see http://labscriptsuite.org), and is licensed under the        #
# Simplified BSD License. See the license.txt file in the root of   #
# the project for the full license.                                 #
#                                                                   #
#####################################################################

import labscript_utils.h5_lock  # noqa: F401
import h5py
import numpy as np

import labscript_utils.properties as properties


class NarwhalDevicesPulseGeneratorParser(object):
    """Runviewer parser for the PrawnBlaster Pseudoclocks."""
    def __init__(self, path, device):
        """
        Args:
            path (str): path to h5 shot file
            device (str): labscript name of PrawnBlaster device
        """
        self.path = path
        self.name = device.name
        self.device = device

    def get_traces(self, add_trace, clock=None):
        """Reads the shot file and extracts hardware instructions to produce
        runviewer traces.

        Args:
            add_trace (func): function handle that adds traces to runviewer
            clock (tuple, optional): clock times from timing device, if not
                the primary pseudoclock

        Returns:
            dict: Dictionary of clocklines and triggers derived from instructions
        """

        # If not the master pseudoclock, then I need to handle the case of getting
        # possibly multiple triggers. Ignore for now though.

        # get the pulse program
        pulse_programs = []
        with h5py.File(self.path, "r") as f:
            # Get the device properties
            device_props = properties.get(f, self.name, "device_properties")
            conn_props = properties.get(f, self.name, "connection_table_properties")

            print(device_props)
            print(conn_props)

            try:
                self.clock_resolution = device_props["clock_resolution"]
                self.trigger_delay = device_props["trigger_delay"]
                self.wait_delay = device_props["wait_delay"]
                print(self.clock_resolution, self.trigger_delay, self.wait_delay)
            except Exception as ex:
                print(ex)

        return clocklines_and_triggers

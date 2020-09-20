import time
import labscript_utils.h5_lock
import h5py
from blacs.tab_base_classes import Worker
import labscript_utils.properties as properties

import serial
import serial.tools.list_ports
import numpy as np
from . import transcode
import time as systime
import struct

class NarwhalPulseGenWorker(Worker):
    '''See p151 of Phils thesis for full explanation'''
    def init(self):
        print(self.usbport)
        self.ser = serial.Serial()
        self.ser.baudrate = 12000000
        self.ser.port = self.usbport
        self.ser.timeout = 0            #non blocking read
        self.ser.writeTimeout = 2     #timeout for write
        self.connect()
        self._confirm_communications()

    def connect(self):
        comports = list(serial.tools.list_ports.comports())
        portdevices = [comport.device for comport in comports]
        port_found = False
        if self.ser.port not in portdevices:
            print('Port: {} does not exist.'.format(self.ser.port))
            print('Available ports:')
            for comport in comports:
                print('    {}'.format(comport.description))
                if 'USB Serial Port' in comport.description:
                    au_port = comport.device
                    port_found = True
            if port_found:
                self.ser.port = au_port
                print('Narwhal PulseGen found at port: {}. Using this port.'.format(comport.device))
            else:
                print('Narwhal PulseGen not found in port list.')
        try:
            self.ser.open()
        except Exception as e:
            print("Error opening serial port: " + str(e))
            print("Check if another program is has an open connection to the Narwhal PulseGen")
            print("Exiting...")
            exit()
        if self.ser.isOpen():
            try:
                self.ser.flushInput() #flush input buffer, discarding all its contents
                self.ser.flushOutput()#flush output buffer, aborting current output
                print('Serial port connected to Narwhal PulseGen...')
            except Exception as e1:
                print('Error communicating...: ' + str(e1))
        else:
            print('Cannot open serial port.')


    def _confirm_communications(self):
        authantication_byte = np.random.bytes(1)
        self.write_echo(authantication_byte)
        all_echo_messages = self.read_all_messages_in_pipe(message_identifier=transcode.msgin_identifier['echo'], timeout=0.1)
        if all_echo_messages:
            success = False
            for message in all_echo_messages:
                if message['echoed_byte'] == authantication_byte:
                    print('Communication successful. Current design is: {}'.format(message['device_version']))
                    success = True
                    break
            if not success:
                print('Communication unsuccessful! Device did not echo correct authentication byte.')
        else:
            print('Communication unsuccessful! Device not responding!') 


    def _get_message(self, timeout=0.0, print_all_messages=False):
        ''' This returns the first message in the pipe, or None if there is none within the pipe
        by the time it times out. If timeout=None, this blocks until it reads a message'''
        t0 = systime.time()
        self.ser.timeout = timeout
        byte_message_identifier = self.ser.read(1)
        if byte_message_identifier != b'':
            message_identifier, = struct.unpack('B', byte_message_identifier)
            if message_identifier not in transcode.msgin_decodeinfo.keys():
                print('The computer read a an invalid message identifier.')
                return None, None
            decode_function = transcode.msgin_decodeinfo[message_identifier]['decode_function']
            if timeout:
                self.ser.timeout = max(timeout - (systime.time() - t0), 0.0)    # sets the timeout to read the rest of the message to be the specified timeout, minus whatever time has been used up so far.
            byte_message = self.ser.read(transcode.msgin_decodeinfo[message_identifier]['message_length'] - 1)
            if byte_message_identifier == b'':
                print('The computer read a valid message identifier, but the full message didn\'t arrive.')
                return None, None
            if print_all_messages:
                print(decode_function(byte_message))
            return message_identifier, decode_function(byte_message)
        return None, None

    def return_on_message_type(self, message_identifier, timeout=None, print_all_messages=False):
        timeout_remaining = timeout
        t0 = systime.time()
        while True:
            identifier, message = self._get_message(timeout_remaining, print_all_messages)
            if identifier == message_identifier:
                return message
            if identifier is None:
                return
            if timeout is not None:
                timeout_remaining = max(timeout - (systime.time() - t0), 0.0)

    def return_on_notification(self, finished=None, triggered=None, address=None, timeout=None, print_all_messages=False):
        return_on_any = True if finished is triggered is address is None else False
        timeout_remaining = timeout
        t0 = systime.time()
        while True:
            identifier, message = self._get_message(timeout_remaining, print_all_messages)
            if identifier == transcode.msgin_identifier['notification']:
                if (message['address_notify'] and message['address'] == address) or (message['trig_notify'] == triggered) or (message['finished_notify'] == finished) or return_on_any:
                    return message
            if identifier is None:
                return
            if timeout is not None:
                timeout_remaining = max(timeout - (systime.time() - t0), 0.0)

    def read_all_messages_in_pipe(self, message_identifier=None, timeout=0.0, print_all_messages=False):
        '''Reads all messages in the pipe. If timeout=0, returns when there isn't any left.
        If timeout>0, then this keeps reading for timeout seconds, and returns after that'''
        t0 = systime.time()
        messages = {}
        while True:
            timeout_remaining = max(timeout - (systime.time() - t0), 0.0)
            identifier, message = self._get_message(timeout_remaining, print_all_messages)
            if identifier is None:
                if message_identifier:
                    return messages.setdefault(message_identifier)
                return messages
            messages.setdefault(identifier, []).append(message)

    def write_echo(self, byte_to_echo):
        command = transcode.encode_echo(byte_to_echo)
        self.write_to_serial(command)

    def write_device_options(self, final_ram_address=None, run_mode=None, trigger_mode=None, trigger_time=None, notify_on_main_trig=None, trigger_length=None):
        command = transcode.encode_device_options(final_ram_address=None, run_mode=None, trigger_mode=None, trigger_time=None, notify_on_main_trig=None, trigger_length=None)
        self.write_to_serial(command)

    def write_powerline_trigger_options(self, trigger_on_powerline=None, powerline_trigger_delay=None):
        command = transcode.encode_powerline_trigger_options(trigger_on_powerline=None, powerline_trigger_delay=None)
        self.write_to_serial(command)

    def write_action(self, enable=None, trigger_now=False, request_state=False, reset_output_coordinator=False, disable_after_current_run=False, notify_when_current_run_finished=False, request_powerline_state=False):
        command = transcode.encode_action(enable=None, trigger_now=False, request_state=False, reset_output_coordinator=False, disable_after_current_run=False, notify_when_current_run_finished=False, request_powerline_state=False)
        self.write_to_serial(command)

    def write_general_debug(self, message):
        command = transcode.encode_general_debug(message)
        self.write_to_serial(command)

    def write_static_state(self, state):
        command = transcode.encode_static_state(state)
        self.write_to_serial(command)

    def write_instructions(self, instructions):
        ''' "instructions" are the encoded timing instructions that will be loaded into the pulse generator memeory.
        These instructions must be generated using the transcode.encode_instruction function. 
        This function accecpts encoded instructions in the following formats (where each individual instruction is always
        in bytes/bytearray): A single encoded instruction, multiple encoded instructions joined together in a single bytes/bytearray, 
        or a list, tuple, or array of single or multiple encoded instructions.'''
        if isinstance(instructions, (list, tuple, np.ndarray)):
            self.write_to_serial(b''.join(instructions)) 
        else:
            self.write_to_serial(instructions) 

    def write_to_serial(self, command):
        self.ser.write(command)

    # These are the functions that I have to complete that are defined in labscript.
    #####################################################
    def program_manual(self, values):
        return {}

    def transition_to_buffered(self, device_name, h5file, initial_values, fresh):
        print('boo! transtion to buffered')
        # get stop time:
        with h5py.File(h5file, 'r') as hdf5_file:
            props = properties.get(hdf5_file, device_name, 'device_properties')
            self.stop_time = props.get('stop_time', None) # stop_time may be absent if we are not the master pseudoclock

            group = hdf5_file['devices/%s'%device_name]
            pulse_program = group['PULSE_PROGRAM'][:]
            device_properties = labscript_utils.properties.get(hdf5_file, device_name, 'device_properties')
            self.is_master_pseudoclock = device_properties['is_master_pseudoclock']


        return {}
    
    def transition_to_manual(self):
        self.start_time = None
        self.stop_time = None
        return True

    def check_if_done(self):
        # Wait up to 1 second for the shot to be done, returning True if it is
        # or False if not.
        if getattr(self, 'start_time', None) is None:
            self.start_time = time.time()
        timeout = min(self.start_time + self.stop_time - time.time(), 1)
        if timeout < 0:
            return True
        time.sleep(timeout)
        return self.start_time + self.stop_time < time.time()

    def shutdown(self):
        return

    def abort_buffered(self):
        return self.transition_to_manual()

    def abort_transition_to_buffered(self):
        return True

    def check_remote_values(self):
        remote_values = None
        return remote_values


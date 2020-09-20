import numpy as np
import struct

#########################################################
# decode
def decode_internal_error(message):
    ''' Messagein identifier:  1 byte: 100
    Message format:                     BITS USED   FPGA INDEX.
    tags:               1 byte  [0]     2 bits      [0+:2]      unsigned int.
        invalid_identifier_received     1 bit       [0]
        timeout_waiting_for_full_msg    1 bit       [1]  
        received_message_not_forwarded  1 bit       [2]  
    error information:  1 byte  [1]     8 bits      [8+:8]     unsigned int.

    The 'error_info' represents the "device_index" for the received message, which basically says where the meassage should have headed in the FPGA.
    '''
    tags, =         struct.unpack('<Q', message[0:1] + bytes(7))
    error_info, =   struct.unpack('<Q', message[1:2] + bytes(7))
    invalid_identifier_received_tag =       (tags >> 0) & 0b1        
    timeout_waiting_for_msg_tag =           (tags >> 1) & 0b1     
    received_message_not_forwarded_tag =    (tags >> 2) & 0b1 
    invalid_identifier_received =       decode_lookup['invalid_identifier'][invalid_identifier_received_tag]
    timeout_waiting_for_msg =           decode_lookup['msg_receive_timeout'][timeout_waiting_for_msg_tag]
    received_message_not_forwarded =    decode_lookup['msg_not_forwarded'][received_message_not_forwarded_tag]
            #warnings.warn('The FPGA received a message with an invalid message identifier.')
    return {'invalid_identifier_received':invalid_identifier_received, 'timeout_waiting_to_receive_message':timeout_waiting_for_msg, 'received_message_not_forwarded':received_message_not_forwarded, 'error_info':error_info}

def decode_easyprint(message):
    ''' Messagein identifier:  1 byte: 102
    Message format:                     BITS USED   FPGA INDEX.
    printed message:    8 bytes [0:3]   64 bits     [0+:64]     '''
    binary_representation = []
    for letter in message[::-1]:
        binary_representation.append('{:08b} '.format(letter))
    return ''.join(binary_representation)

def decode_devicestate(message):
    ''' Messagein identifier:  1 byte: 103
    Message format:                     BITS USED   FPGA INDEX.
    output state:       3 bytes [0:3]   24 bits     [0+:24]     unsigned int. LSB=output 0
    final ram address:  2 bytes [3:5]   16 bits     [24+:16]    unsigned int.
    trigger time:       7 bytes [5:12]  56 bits     [40+:56]    unsigned int.
    trigger length:     1 byte  [12]    8 bits      [96+:8]     unsigned int.
    tags:               1 byte  [13]    6 bits      [104+:6]    unsigned int.
        run mode                        1 bit       [104]   
        trigger mode                    2 bit       [105+:2] 
        notify on main trig             1 bit       [107]   
        clock source                    1 bit       [108]   
        run enable                      1 bit       [109] 
    current ram address:2 bytes [14:16] 16 bits     [112+:16]   unsigned int.
    '''
    state =                 np.unpackbits(np.array([message[0], message[1], message[2]], dtype=np.uint8), bitorder='little')
    final_ram_address, =    struct.unpack('<Q', message[3:5] + bytes(6))
    trigger_time, =         struct.unpack('<Q', message[5:12] + bytes(1))
    trigger_length, =       struct.unpack('<Q', message[12:13] + bytes(7))
    tags, =                 struct.unpack('<Q', message[13:14] + bytes(7))
    current_ram_address, =  struct.unpack('<Q', message[14:16] + bytes(6))
    run_mode_tag =              (tags >> 0) & 0b1            
    trigger_mode_tag =          (tags >> 1) & 0b11              
    notify_on_main_trig_tag =   (tags >> 3) & 0b1    
    clock_source_tag =          (tags >> 4) & 0b1  
    run_enable_tag =            (tags >> 5) & 0b1  
    run_mode =              decode_lookup['run_mode'][run_mode_tag]
    trigger_mode =          decode_lookup['trigger_mode'][trigger_mode_tag]
    notify_on_main_trig =   decode_lookup['notify_on_main_trig'][notify_on_main_trig_tag]
    clock_source =          decode_lookup['clock_source'][clock_source_tag]
    run_enable =            decode_lookup['run_enable'][run_enable_tag]
    return {'state:':state, 'final_ram_address':final_ram_address, 'trigger_time':trigger_time, 'run_mode':run_mode, 'trigger_mode':trigger_mode, 'notify_on_main_trig':notify_on_main_trig, 'trigger_length':trigger_length, 'clock_source':clock_source, 'run_enable':run_enable, 'current_address':current_ram_address}

def decode_powerlinestate(message):
    ''' Messagein identifier:  1 byte: 105
    Message format:                             BITS USED   FPGA INDEX.
    tags:                       1 byte  [0]     2 bits      [0+:2]    unsigned int.
        trig_on_powerline                       1 bit       [0]   
        powerline_locked                        1 bit       [1] 
    powerline_period:           3 bytes [1:4]   22 bits     [8+:22]   unsigned int.
    powerline_trigger_delay:    3 bytes [4:7]   22 bits     [32+:22]  unsigned int.
    '''
    tags, =                     struct.unpack('<Q', message[0:1] + bytes(7))
    powerline_period, =         struct.unpack('<Q', message[1:4] + bytes(5))
    powerline_trigger_delay, =  struct.unpack('<Q', message[4:7] + bytes(5))
    trig_on_powerline_tag = (tags >> 0) & 0b1
    powerline_locked_tag =  (tags >> 1) & 0b1
    trig_on_powerline = decode_lookup['trig_on_powerline'][trig_on_powerline_tag]
    powerline_locked =  decode_lookup['powerline_locked'][powerline_locked_tag]
    return {'trig_on_powerline':trig_on_powerline, 'powerline_locked':powerline_locked, 'powerline_period':powerline_period, 'powerline_trigger_delay':powerline_trigger_delay}

def decode_notification(message):
    ''' Messagein identifier:  1 byte: 104
    Message format:                             BITS USED   FPGA INDEX.
    current instruction address:2 bytes [0:2]   16 bits     [0+:16]   unsigned int.
    tags:                       1 byte  [2]     3 bits      [16+:3]   
        instriction notify tag                  1 bit       [16] 
        trigger notify tag                      1 bit       [17] 
        end of run notify tag                   1 bit       [18] 
    '''
    address_of_notification, =  struct.unpack('<Q', message[0:2] + bytes(6))
    tags, =                     struct.unpack('<Q', message[2:3] + bytes(7))
    address_notify_tag =    (tags >> 0) & 0b1
    trig_notify_tag =       (tags >> 1) & 0b1
    finished_notify_tag =   (tags >> 2) & 0b1
    address_notify =    decode_lookup['address_notify'][address_notify_tag]
    trig_notify =       decode_lookup['trig_notify'][trig_notify_tag]
    finished_notify =        decode_lookup['finished_notify'][finished_notify_tag]
    return {'address':address_of_notification, 'address_notify':address_notify, 'trig_notify':trig_notify, 'finished_notify':finished_notify}

def decode_serialecho(message):
    ''' Messagein identifier:  1 byte: 101
    Message format:                     BITS USED   FPGA INDEX.
    echoed byte:        1 bytes [0:1]   8 bits      [0+:8]     
    device version:     7 bytes [1:8]   56 bits     [8+:56]    '''
    echoed_byte = message[0:1]
    device_version = message[1:8].decode()
    return {'echoed_byte':echoed_byte, 'device_version':device_version}

#########################################################
# encode
def encode_echo(byte_to_echo):
    ''' Messageout identifier:  1 byte: 150
    Message format:                             BITS USED   FPGA INDEX.
    byte_to_echo:               1 byte  [0:18]  8 bits     [0+:8]  
    '''    
    message_identifier = struct.pack('B', msgout_identifier['echo'])
    return message_identifier + byte_to_echo

def encode_device_options(final_ram_address=None, run_mode=None, trigger_mode=None, trigger_time=None, notify_on_main_trig=None, trigger_length=None):
    ''' Messageout identifier:  1 byte: 154
    Message format:                             BITS USED   FPGA INDEX.
    final_RAM_address:          2 bytes [0:2]   16 bits     [0+:16]     unsigned int.
    trigger_time:               7 bytes [2:9]   56 bits     [16+:56]    unsigned int.
    trigger_length:             1 byte  [9]     8 bits      [72+:8]     unsigned int.
    tags:                       1 byte  [10]    4 bits      [80+:4]     unsigned int.
        run_mode                                1 bit       [80]   
        trigger_mode                            2 bits      [81+:2] 
        trigger_notification_enable             1 bit       [83] 
    '''
    if final_ram_address    is not None: final_ram_address = final_ram_address
    if run_mode             is not None: run_mode = run_mode
    if trigger_mode         is not None: trigger_mode = trigger_mode
    if trigger_time         is not None: trigger_time = trigger_time
    if notify_on_main_trig  is not None: notify_on_main_trig = notify_on_main_trig
    if trigger_length       is not None: trigger_length = trigger_length
    run_mode_tag =              encode_lookup['run_mode'][run_mode] << 0
    trigger_mode_tag =          encode_lookup['trigger_mode'][trigger_mode] << 1
    notify_on_main_trig_tag =   encode_lookup['notify_on_trig'][notify_on_main_trig] << 3
    tags = run_mode_tag | trigger_mode_tag | notify_on_main_trig_tag
    message_identifier =    struct.pack('B', msgout_identifier['device_options'])
    final_ram_address =     struct.pack('<Q', final_ram_address)[:2]
    trigger_time =          struct.pack('<Q', trigger_time)[:7]
    trigger_length =        struct.pack('<Q', trigger_length)[:1]
    tags =                  struct.pack('<Q', tags)[:1]
    return message_identifier + final_ram_address + trigger_time + trigger_length + tags

def encode_powerline_trigger_options(trigger_on_powerline=None, powerline_trigger_delay=None):
    ''' Messageout identifier:  1 byte: 156
    Message format:                             BITS USED   FPGA INDEX.
    powerline_trigger_delay:    3 bytes [0:3]   22 bits     [0+:22]     unsigned int.
    tags:                       1 byte  [3]     1 bits      [24]     unsigned int.
        wait_for_powerline                      1 bit       [24]   
    '''
    if powerline_trigger_delay  is not None: powerline_trigger_delay = powerline_trigger_delay
    if trigger_on_powerline     is not None: trigger_on_powerline = trigger_on_powerline
    trigger_on_powerline_tag =  encode_lookup['trigger_on_powerline'][trigger_on_powerline]
    message_identifier =        struct.pack('B', msgout_identifier['powerline_trigger_options'])
    powerline_trigger_delay =   struct.pack('<Q', powerline_trigger_delay)[:3]
    tags =                      struct.pack('<Q', trigger_on_powerline_tag)[:1]
    return message_identifier + powerline_trigger_delay + tags

def encode_action(enable=None, trigger_now=False, request_state=False, reset_output_coordinator=False, disable_after_current_run=False, notify_when_current_run_finished=False, request_powerline_state=False):
    ''' Messageout identifier:  1 byte: 152
    Message format:                             BITS USED   FPGA INDEX.
    tags:                       1 byte  [0]     8 bits      [0+:8]    
        run_enable                              2 bits      [0+:2]      bit[0] indicates if "run_enable" is to be modified. bit[1] is the actual enable setting, it is ignored it bit[0] = 0   
        trigger_now                             1 bit       [2] 
        request_state                           1 bit       [3]
        reset_outpoot_coordinator               1 bit       [4] 
        disable_after_current_run               1 bit       [5] 
        notify_when_current_run_finished        1 bit       [6]
        request_powerline_state                 1 bit       [7]
    '''
    enable_tag =                        encode_lookup['run_enable'][enable] << 0
    trigger_now_tag =                   encode_lookup['trigger_now'][trigger_now] << 2
    request_state_tag =                 encode_lookup['request_state'][request_state] << 3
    reset_output_coordinator_tag =      encode_lookup['reset_output_coordinator'][reset_output_coordinator] << 4
    disable_after_current_run =         encode_lookup['disable_after_current_run'][disable_after_current_run] << 5
    notify_when_current_run_finished =  encode_lookup['notify_when_finished'][notify_when_current_run_finished] << 6
    request_powerline_state_tag =       encode_lookup['request_powerline_state'][request_powerline_state] << 7
    tags = enable_tag | trigger_now_tag | request_state_tag | reset_output_coordinator_tag | disable_after_current_run | notify_when_current_run_finished | request_powerline_state_tag
    message_identifier =    struct.pack('B', msgout_identifier['action_request'])
    tags =                  struct.pack('<Q', tags)[:1]
    return message_identifier + tags

def encode_general_debug(message):
    ''' Messageout identifier:  1 byte: 153
    Message format:                             BITS USED   FPGA INDEX.
    general_putpose_input:      8 bytes [0:8]   64 bits     [0+:64]     unsigned int.
    '''
    message_identifier =    struct.pack('B', msgout_identifier['general_input'])
    message =               struct.pack('<Q', message)[:8]
    return message_identifier + message

def encode_static_state(state):
    ''' Messageout identifier:  1 byte: 155
    Message format:                             BITS USED   FPGA INDEX.
    main_outputs_state:         3 bytes [0:3]   24 bits     [0+:24]     unsigned int.
    '''
    state = state_multiformat_to_int(state)
    message_identifier =    struct.pack('B', msgout_identifier['set_static_state'])
    state =                 struct.pack('<Q', state)[:3] 
    return message_identifier + state

def encode_instruction(address=0, state=0, duration=1, goto_address=0, goto_counter=0, stop_and_wait=False, hardware_trig_out=False, notify_computer=False, powerline_sync=False):
    ''' Note. This function generates the instruction only. It is sent in a different instruction.
        Messageout identifier:  1 byte: 151
    Message format:                             BITS USED   FPGA INDEX.
    instruction_address:        2 bytes [0:2]   16 bits     [0+:16]     unsigned int.
    main_outputs_state:         3 bytes [2:5]   24 bits     [16+:24]    unsigned int.
    instruction_duration:       6 bytes [5:11]  48 bits     [40+:48]    unsigned int.
    goto_address:               2 bytes [11:13] 16 bits     [88+:16]    unsigned int.
    goto_counter:               4 bytes [13:17] 32 bits     [104+:32]   unsigned int.
    tags:                       1 byte  [17]    3 bits      [136+:3]    unsigned int.
        stop_and_wait                           1 bit       [136]   
        hardware_trigger_out                    1 bits      [137] 
        notify_instruction_activated            1 bit       [138]
        powerline_sync                          1 bit       [139] 
    '''
    #I should include some sort of instruction validation. Ie, check all inputs are valid. Eg, duration!=0.
    state = state_multiformat_to_int(state)
    stop_and_wait_tag =     encode_lookup['stop_and_wait'][stop_and_wait] << 0
    hard_trig_out_tag =     encode_lookup['trig_out_on_instruction'][hardware_trig_out] << 1
    notify_computer_tag =   encode_lookup['notify_on_instruction'][notify_computer] << 2
    powerline_sync_tag =    encode_lookup['powerline_sync'][powerline_sync] << 3
    tags = stop_and_wait_tag | hard_trig_out_tag | notify_computer_tag | powerline_sync_tag
    message_identifier =    struct.pack('B', msgout_identifier['load_ram'])
    address =               struct.pack('<Q', address)[:2]
    state =                 struct.pack('<Q', state)[:3]
    duration =              struct.pack('<Q', duration)[:6]
    goto_address =          struct.pack('<Q', goto_address)[:2]
    goto_counter =          struct.pack('<Q', goto_counter)[:4]
    tags =                  struct.pack('<Q', tags)[:1]
    return message_identifier + address + state + duration + goto_address + goto_counter + tags

def state_multiformat_to_int(state):
    if isinstance(state, (list, tuple, np.ndarray)):
        state_int = 0
        for bit_idx, value in enumerate(state):
            state_int += int(value) << bit_idx
        state = state_int
    return state

#########################################################
# constants
msgin_decodeinfo = {
    100:{'message_length':3, 'decode_function':decode_internal_error},
    101:{'message_length':9, 'decode_function':decode_serialecho},
    102:{'message_length':9, 'decode_function':decode_easyprint},
    103:{'message_length':17, 'decode_function':decode_devicestate},
    104:{'message_length':4, 'decode_function':decode_notification},
    105:{'message_length':8, 'decode_function':decode_powerlinestate}
    }

msgin_identifier = {
    'error':100,
    'echo':101,
    'print':102,
    'devicestate':103,
    'notification':104,
    'powerlinestate':105
    }

decode_lookup = {
    'clock_source':{1:'internal', 0:'external'},
    'run_enable':{1:True, 0:False},
    'noitfy_on_instruction':{1:True, 0:False},
    'notify_on_main_trig':{1:True, 0:False},
    'notify_on_run_finished':{1:True, 0:False},
    'run_mode':{0:'single', 1:'continuous'},
    'trigger_mode':{0:'software', 1:'hardware', 2:'either'},
    'trig_on_powerline':{1:True, 0:False},
    'powerline_locked':{1:True, 0:False},
    'address_notify':{1:True, 0:False},
    'trig_notify':{1:True, 0:False},
    'finished_notify':{1:True, 0:False},
    'invalid_identifier':{1:True, 0:False},
    'msg_not_forwarded':{1:True, 0:False},
    'msg_receive_timeout':{1:True, 0:False}
    }

msgout_identifier = {
    'echo':150,
    'load_ram':151,
    'action_request':152,
    'general_input':153,
    'device_options':154,
    'set_static_state':155,
    'powerline_trigger_options':156
    }

encode_lookup = {
    'run_enable':{True:0b11, False:0b01, None:0b00}, 
    'trigger_now':{True:1, False:0},
    'request_state':{True:1, False:0},
    'request_powerline_state':{True:1, False:0},
    'reset_output_coordinator':{True:1, False:0},
    'disable_after_current_run':{True:1, False:0},
    'notify_when_finished':{True:1, False:0},
    'run_mode':{'single':0, 'continuous':1},
    'trigger_mode':{'software':0, 'hardware':1, 'either':2},
    'notify_on_trig':{True:1, False:0},
    'trigger_on_powerline':{True:1, False:0},
    'stop_and_wait':{True:1, False:0}, 
    'notify_on_instruction':{True:1, False:0},  
    'trig_out_on_instruction':{True:1, False:0},
    'powerline_sync':{True:1, False:0}
    }
'''
I'm not sure how I am supposed to import other classes from files within this device directory. Is it like the following?
'''
# from .blacs_workers import NarwhalDevicesPulseGeneratorWorker

import os
import datetime

from blacs.device_base_class import DeviceTab, define_state, MODE_BUFFERED
from blacs.tab_base_classes import MODE_MANUAL, MODE_TRANSITION_TO_BUFFERED, MODE_TRANSITION_TO_MANUAL, MODE_BUFFERED  

from qtutils import UiLoader
from qtutils.qt import QtCore
from qtutils.qt import QtGui
from qtutils.qt.QtWidgets import QDoubleSpinBox, QComboBox, QTextEdit, QLabel

class CustomDoubleSpinBox(QDoubleSpinBox):
    editingFinished = QtCore.pyqtSignal()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_editing = False
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.user_editing = True
    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.user_editing = False
        self.editingFinished.emit()
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == QtCore.Qt.Key_Enter or event.key() == QtCore.Qt.Key_Return:
            self.clearFocus()
    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

class CustomComboBox(QComboBox):
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

class CustomTextEdit(QTextEdit):
    def __init__(self, max_lines=10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_lines = max_lines
        self.current_lines = 0
    def add_text_to_top(self, text):
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.Start)
        cursor.insertText(text + '\n')
        self.setTextCursor(cursor)
        self.current_lines += 1
        if self.current_lines > self.max_lines:
            self.remove_last_line()
    def remove_last_line(self):
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.movePosition(QtGui.QTextCursor.StartOfBlock, QtGui.QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()
        self.current_lines -= 1
    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

class NarwhalDevicesPulseGeneratorTab(DeviceTab):
    # See phil's thesis p148
    # Capabilities
    num_DO = 24
    def __init__(self,*args,**kwargs):
        DeviceTab.__init__(self,*args,**kwargs)

    def initialise_workers(self):
        """Initialises the  Workers.
        This method is called automatically by BLACS.
        """
        self.serial_number = int(self.settings['connection_table'].find_by_name(self.device_name).BLACS_connection)

        # com_port = str(
        #     self.settings["connection_table"]
        #     .find_by_name(self.device_name)
        #     .BLACS_connection
        # )

        worker_initialisation_kwargs = {
            'serial_number':self.serial_number,
            'num_DO': self.num_DO
        }
        from .blacs_workers import NarwhalDevicesPulseGeneratorWorker
        self.create_worker(
            "main_worker",
            NarwhalDevicesPulseGeneratorWorker,
            worker_initialisation_kwargs,
        )
        # self.create_worker(
        #     "main_worker",
        #     ".blacs_workers.NarwhalDevicesPulseGeneratorWorker",
        #     worker_initialisation_kwargs,
        # )
        self.primary_worker = "main_worker"

    def initialise_GUI(self):
        do_prop = {}
        for i in range(self.num_DO):
            do_prop[f'channel {i:d}'] = {}
        
        # Create the output objects         
        self.create_digital_outputs(do_prop)        
        # Create widgets for output objects
        _, _, do_widgets = self.auto_create_widgets()
        
        # Define the sort function for the digital outputs
        def sort(channel):
            channel = channel.replace('channel ','')
            channel = int(channel)
            return '%02d'%(channel)
        
        # and auto place the widgets in the UI
        self.auto_place_widgets(("Channels",do_widgets,sort))
        
        # Look into this after I have made it work in a more basic fashon. Also, it if fast to load instructions, so I'm not sure if this is necessary.
        # self.supports_smart_programming(True) 
        
        #Checks state on startup
        '''This is sort of causing some issues. This works as it should, but BLACS somehow remembers the state the NDPG was in when blacs last closed, and then there is a conflict and I have to choose which is correct.
        Not sure how to fix that. Maybe it doesn't need fixing, and it just means I havent finished programming the transition from buffered. OR transition_to_manual'''
        self.supports_remote_value_check(True)
        
        # Load status monitor (and start/stop/reset buttons) UI
        self.ui = UiLoader().load(os.path.join(os.path.dirname(os.path.realpath(__file__)),'narwhaldevicespulsegenerator.ui'))        
        self.get_tab_layout().addWidget(self.ui)
        # Connect signals for main controls
        self.ui.button_start.clicked.connect(self.start)
        self.ui.button_pause.toggled.connect(self.pause)
        self.ui.button_stop.clicked.connect(self.stop)
        self.ui.button_reset.clicked.connect(self.reset)
        self.ui.combo_runmode = CustomComboBox(focusPolicy=QtCore.Qt.StrongFocus)
        self.ui.combo_runmode.addItems(['single', 'continuous'])
        self.ui.combo_runmode.currentTextChanged.connect(self.runmode_textchanged)
        self.ui.horizontalLayout_manualcontrol.insertWidget(2, self.ui.combo_runmode)

        # Connect/make the Trigger in controls
        self.ui.combo_triggersource = CustomComboBox(focusPolicy=QtCore.Qt.StrongFocus)
        self.ui.combo_triggersource.addItems(['software', 'hardware', 'either', 'single_hardware'])
        self.ui.combo_triggersource.currentTextChanged.connect(self.triggersource_textchanged)
        self.ui.formLayout_triggerin.insertRow(0, QLabel("Trigger source"), self.ui.combo_triggersource)
        self.ui.check_waitforpowerline.toggled.connect(self.waitforpowerline_toggled)
        self.ui.doublespin_powerlinedelay = CustomDoubleSpinBox(minimum=0, maximum=41.943030, decimals=5, suffix='0 ms', focusPolicy=QtCore.Qt.StrongFocus)
        self.ui.doublespin_powerlinedelay.editingFinished.connect(self.powerlinedelay_editingfinished)
        self.ui.formLayout_triggerin.addRow(QLabel("Delay after powerline"), self.ui.doublespin_powerlinedelay)

        # Connect/make the Trigger out controls
        self.ui.doublespin_triggerduration = CustomDoubleSpinBox(minimum=0, maximum=2.55, decimals=2, suffix='0 μs', value=0.01, singleStep=0.01, focusPolicy=QtCore.Qt.StrongFocus)
        self.ui.doublespin_triggerduration.editingFinished.connect(self.triggerduration_editingfinished)
        self.ui.formLayout_triggerout.addRow(QLabel("Duration"), self.ui.doublespin_triggerduration)  
        self.ui.doublespin_triggerdelay = CustomDoubleSpinBox(minimum=0, maximum=720575940.37927935, decimals=8, suffix='0 s', value=0, singleStep=0.00000001, focusPolicy=QtCore.Qt.StrongFocus)
        self.ui.doublespin_triggerdelay.editingFinished.connect(self.triggerdelay_editingfinished)
        self.ui.formLayout_triggerout.addRow(QLabel("Delay"), self.ui.doublespin_triggerdelay)  

        # Notifications
        self.ui.check_notifytrigout.toggled.connect(self.notifytrigout_toggled)
        self.ui.check_notifyfinished.toggled.connect(self.notifyfinished_toggled)
        self.ui.text_notifications = CustomTextEdit(max_lines=100, focusPolicy=QtCore.Qt.StrongFocus)
        self.ui.text_notifications.setReadOnly(True)
        self.ui.verticalLayout_notifications.addWidget(self.ui.text_notifications)


        # Add icons
        self.ui.button_start.setIcon(QtGui.QIcon(':/qtutils/fugue/control'))
        self.ui.button_start.setToolTip('Start')
        self.ui.button_pause.setIcon(QtGui.QIcon(':/qtutils/fugue/control-pause'))
        self.ui.button_pause.setToolTip('Software enable/disable')
        self.ui.button_stop.setIcon(QtGui.QIcon(':/qtutils/fugue/control-stop-square'))
        self.ui.button_stop.setToolTip('Stop after current run')
        self.ui.button_reset.setIcon(QtGui.QIcon(':/qtutils/fugue/arrow-circle'))
        self.ui.button_reset.setToolTip('Reset')
        
        
        # Status monitor timout
        self.statemachine_timeout_add(2000, self.status_monitor)
    


    def get_child_from_connection_table(self, parent_device_name, port):
        # Don't know what this does, but I think it is ok to leave it.
        # This is a direct output, let's search for it on the internal intermediate device called NarwhalDevicesPulseGeneratorDirectOutputs
        if parent_device_name == self.device_name:
            device = self.connection_table.find_by_name(self.device_name)
            pseudoclock = device.child_list[list(device.child_list.keys())[0]] # there should always be one (and only one) child, the Pseudoclock
            clockline = None
            for child_name, child in pseudoclock.child_list.items():
                # store a reference to the internal clockline
                if child.parent_port == 'internal':
                    clockline = child
                # if the port is in use by a clockline, return the clockline
                elif child.parent_port == port:
                    return child
                
            if clockline is not None:
                # There should only be one child of this clock line, the direct outputs
                direct_outputs = clockline.child_list[list(clockline.child_list.keys())[0]] 
                # look to see if the port is used by a child of the direct outputs
                return DeviceTab.get_child_from_connection_table(self, direct_outputs.name, port)
            else:
                return ''
        else:
            # else it's a child of a DDS, so we can use the default behaviour to find the device
            return DeviceTab.get_child_from_connection_table(self, parent_device_name, port)
    

    
    #These call methods of the blacs_worker, which send signals to the device. Need to decide what to have. start_run is compulsury, the others I can choose what I like.

    # This function gets the status of the Pulseblaster from the spinapi,
    # and updates the front panel widgets!
    @define_state(MODE_MANUAL|MODE_BUFFERED|MODE_TRANSITION_TO_BUFFERED|MODE_TRANSITION_TO_MANUAL,True)  
    def status_monitor(self,notify_queue=None):
        # When called with a queue, this function writes to the queue
        # when the pulseblaster is waiting. This indicates the end of
        # an experimental run.
        '''No idea what the hell that means, But it might be important?'''
        
        # self.status, waits_pending, time_based_shot_over = yield(self.queue_work(self._primary_worker,'check_status'))
        
        notifications, state, powerline_state = yield(self.queue_work(self._primary_worker,'check_status'))

        # Synchronisation
        powerline_freq = 1/(powerline_state['powerline_period']*10E-9)*powerline_state['powerline_locked']
        self.ui.label_powerlinefrequency.setText(f'{powerline_freq:.3f} Hz')
        self.ui.label_referenceclock.setText(f"{state['clock_source']}")

        # Status
        self.ui.label_currentaddress.setText(f"{state['current_address_approx']}")
        self.ui.label_finaladdress.setText(f"{state['final_ram_address']}")
        tick_pixmap = QtGui.QIcon(':/qtutils/fugue/tick').pixmap(QtCore.QSize(16, 16))
        cross_pixmap = QtGui.QIcon(':/qtutils/fugue/cross').pixmap(QtCore.QSize(16, 16))
        if state['running']:
            self.ui.label_running.setPixmap(tick_pixmap)
        else:
            self.ui.label_running.setPixmap(cross_pixmap)
        if state['software_run_enable']:
            self.ui.label_enablesoftware.setPixmap(tick_pixmap)
        else:
            self.ui.label_enablesoftware.setPixmap(cross_pixmap)
        if state['hardware_run_enable']:
            self.ui.label_enablehardware.setPixmap(tick_pixmap)
        else:
            self.ui.label_enablehardware.setPixmap(cross_pixmap)

        self.ui.button_pause.blockSignals(True)
        self.ui.button_pause.setChecked(not state['software_run_enable'])
        self.ui.button_pause.blockSignals(False)

        # Run mode
        #Why block signals? Because other parts of labscript can update the runmode, the runmode can change without me clicking the box. We don't want/need to send this signal again if another part of the program has already changed it.
        self.ui.combo_runmode.blockSignals(True)  
        self.ui.combo_runmode.setCurrentText(state['run_mode'])
        self.ui.combo_runmode.blockSignals(False)

        # Trigger in
        self.ui.combo_triggersource.blockSignals(True)  
        self.ui.combo_triggersource.setCurrentText(state['trigger_source'])
        self.ui.combo_triggersource.blockSignals(False)

        self.ui.check_waitforpowerline.blockSignals(True)
        self.ui.check_waitforpowerline.setChecked(powerline_state['trig_on_powerline'])
        self.ui.check_waitforpowerline.blockSignals(False)

        if not self.ui.doublespin_powerlinedelay.user_editing: 
            self.ui.doublespin_powerlinedelay.setEnabled(powerline_state['trig_on_powerline'])
            self.ui.doublespin_powerlinedelay.blockSignals(True)
            self.ui.doublespin_powerlinedelay.setValue(powerline_state['powerline_trigger_delay']*10E-9*1E3)
            self.ui.doublespin_powerlinedelay.blockSignals(False)

        # Trigger out
        if not self.ui.doublespin_triggerduration.user_editing: 
            self.ui.doublespin_triggerduration.blockSignals(True)
            self.ui.doublespin_triggerduration.setValue(state['trigger_out_length']*10E-9*1E6)
            self.ui.doublespin_triggerduration.blockSignals(False)      
        if not self.ui.doublespin_triggerdelay.user_editing: 
            self.ui.doublespin_triggerdelay.blockSignals(True)
            self.ui.doublespin_triggerdelay.setValue(state['trigger_out_delay']*10E-9)
            self.ui.doublespin_triggerdelay.blockSignals(False)  

        # Notifications
        self.ui.check_notifytrigout.blockSignals(True)
        self.ui.check_notifytrigout.setChecked(state['notify_on_main_trig_out'])
        self.ui.check_notifytrigout.blockSignals(False)
        self.ui.check_notifyfinished.blockSignals(True)
        self.ui.check_notifyfinished.setChecked(state['notify_on_run_finished'])
        self.ui.check_notifyfinished.blockSignals(False)

        now = datetime.datetime.now()
        for notification in notifications:
            if notification['finished_notify']:
                self.ui.text_notifications.add_text_to_top(now.strftime('%H:%M:%S') + ': Run finished.')
            if notification['trigger_notify']:
                self.ui.text_notifications.add_text_to_top(now.strftime('%H:%M:%S') + ': Main trigger out activated.')
            if notification['address_notify']:
                self.ui.text_notifications.add_text_to_top(now.strftime('%H:%M:%S') + f": Instruction {notification['address']} activated.")

        #Do some other shit too. such as:
        if notify_queue:
            for notification in notifications:
                if notification['finished_notify']:
                    notify_queue.put('done')            
                    self.statemachine_timeout_remove(self.status_monitor)
                    self.statemachine_timeout_add(2000,self.status_monitor)
                    break

        # if self.programming_scheme == 'pb_start/BRANCH':
        #     done_condition = self.status['waiting']
        # elif self.programming_scheme == 'pb_stop_programming/STOP':
        #     done_condition = self.status['stopped']
            
        # if time_based_shot_over is not None:
        #     done_condition = time_based_shot_over
            
        # if notify_queue is not None and done_condition and not waits_pending:
        #     # Experiment is over. Tell the queue manager about it, then
        #     # set the status checking timeout back to every 2 seconds
        #     # with no queue.
        #     notify_queue.put('done')
        #     self.statemachine_timeout_remove(self.status_monitor)
        #     self.statemachine_timeout_add(2000,self.status_monitor)
        #     if self.programming_scheme == 'pb_stop_programming/STOP':
        #         # Not clear that on all models the outputs will be correct after being
        #         # stopped this way, so we do program_manual with current values to be sure:
        #         self.program_device()
        # # Update widgets with new status
        # for state in self.status_states:
        #     if self.status[state]:
        #         icon = QtGui.QIcon(':/qtutils/fugue/tick')
        #     else:
        #         icon = QtGui.QIcon(':/qtutils/fugue/cross')
            
        #     pixmap = icon.pixmap(QtCore.QSize(16, 16))
        #     self.status_widgets[state].setPixmap(pixmap)
        

    @define_state(MODE_MANUAL|MODE_BUFFERED|MODE_TRANSITION_TO_BUFFERED|MODE_TRANSITION_TO_MANUAL,True)  
    def start(self,widget=None):
        yield(self.queue_work(self._primary_worker,'start_run'))
        self.status_monitor()

    '''The decorator says what state the outer state machine can be in to allow calls to this method. 
    The True, means only run the most recent entry for a method is run if duplicate entries for the GUI method
    exist in the queue (albeit with different arguments)'''
    @define_state(MODE_MANUAL|MODE_BUFFERED|MODE_TRANSITION_TO_BUFFERED|MODE_TRANSITION_TO_MANUAL,True) 
    def pause(self, checked, widget=None):
        enabled = not checked
        yield(self.queue_work(self._primary_worker,'run_enable_software', enabled))
        self.status_monitor()
        
    @define_state(MODE_MANUAL|MODE_BUFFERED|MODE_TRANSITION_TO_BUFFERED|MODE_TRANSITION_TO_MANUAL,True)  
    def stop(self,widget=None):
        yield(self.queue_work(self._primary_worker,'disable_after_current_run'))
        self.status_monitor()
        
    @define_state(MODE_MANUAL|MODE_BUFFERED|MODE_TRANSITION_TO_BUFFERED|MODE_TRANSITION_TO_MANUAL,True)  
    def reset(self,widget=None):
        yield(self.queue_work(self._primary_worker,'abort_buffered'))
        # At the moment, abort_buffered jsut sends a reset run anyway, but if I cange it in the future, I might have to make a separate function.
        self.status_monitor()
    
    @define_state(MODE_BUFFERED,True)  
    def start_run(self, notify_queue):
        """Starts the Pulseblaster, notifying the queue manager when
        the run is over"""
        self.statemachine_timeout_remove(self.status_monitor)
        self.start()
        self.statemachine_timeout_add(100,self.status_monitor,notify_queue)

    @define_state(MODE_MANUAL|MODE_BUFFERED|MODE_TRANSITION_TO_BUFFERED|MODE_TRANSITION_TO_MANUAL,True) 
    def runmode_textchanged(self, runmode, widget=None):
        yield(self.queue_work(self._primary_worker,'set_runmode', runmode))
        self.status_monitor()

    @define_state(MODE_MANUAL|MODE_BUFFERED|MODE_TRANSITION_TO_BUFFERED|MODE_TRANSITION_TO_MANUAL,True) 
    def triggersource_textchanged(self, triggersource, widget=None):
        yield(self.queue_work(self._primary_worker,'set_triggersource', triggersource))
        self.status_monitor()

    @define_state(MODE_MANUAL|MODE_BUFFERED|MODE_TRANSITION_TO_BUFFERED|MODE_TRANSITION_TO_MANUAL,True) 
    def waitforpowerline_toggled(self, checked, widget=None):
        self.ui.doublespin_powerlinedelay.setEnabled(checked)
        yield(self.queue_work(self._primary_worker,'set_waitforpowerline', checked))
        self.status_monitor()

    @define_state(MODE_MANUAL|MODE_BUFFERED|MODE_TRANSITION_TO_BUFFERED|MODE_TRANSITION_TO_MANUAL,True) 
    def powerlinedelay_editingfinished(self, widget=None):
        value = self.ui.doublespin_powerlinedelay.value()
        yield(self.queue_work(self._primary_worker,'set_powerlinedelay', int(value*1E-3/10E-9)))
        self.status_monitor()

    @define_state(MODE_MANUAL|MODE_BUFFERED|MODE_TRANSITION_TO_BUFFERED|MODE_TRANSITION_TO_MANUAL,True) 
    def triggerduration_editingfinished(self, widget=None):
        value = self.ui.doublespin_triggerduration.value()
        yield(self.queue_work(self._primary_worker,'set_triggerduration', int(value*1E-6/10E-9)))
        self.status_monitor()

    @define_state(MODE_MANUAL|MODE_BUFFERED|MODE_TRANSITION_TO_BUFFERED|MODE_TRANSITION_TO_MANUAL,True) 
    def triggerdelay_editingfinished(self, widget=None):
        value = self.ui.doublespin_triggerdelay.value()
        yield(self.queue_work(self._primary_worker,'set_triggerdelay', int(value/10E-9)))
        self.status_monitor()

    @define_state(MODE_MANUAL|MODE_BUFFERED|MODE_TRANSITION_TO_BUFFERED|MODE_TRANSITION_TO_MANUAL,True) 
    def notifytrigout_toggled(self, checked, widget=None):
        yield(self.queue_work(self._primary_worker,'set_notifytrigout', checked))
        self.status_monitor()

    @define_state(MODE_MANUAL|MODE_BUFFERED|MODE_TRANSITION_TO_BUFFERED|MODE_TRANSITION_TO_MANUAL,True) 
    def notifyfinished_toggled(self, checked, widget=None):
        yield(self.queue_work(self._primary_worker,'set_notifyfinished', checked))
        self.status_monitor()

'''So I should just make whatever buttons make sence for the NDPG. I don't need to follow
the pulseblaster layout.



'''
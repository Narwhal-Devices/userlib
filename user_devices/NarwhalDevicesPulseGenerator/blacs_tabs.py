'''
I'm not sure how I am supposed to import other classes from files within this device directory. Is it like the following?
'''
# from .blacs_workers import NarwhalDevicesPulseGeneratorWorker

import os

from blacs.device_base_class import DeviceTab, define_state, MODE_BUFFERED
from blacs.tab_base_classes import MODE_MANUAL, MODE_TRANSITION_TO_BUFFERED, MODE_TRANSITION_TO_MANUAL, MODE_BUFFERED  

from qtutils import UiLoader
from qtutils.qt import QtCore
from qtutils.qt import QtGui

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
        dds_widgets,ao_widgets,do_widgets = self.auto_create_widgets()
        
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
        self.supports_remote_value_check(True)
        
        # Load status monitor (and start/stop/reset buttons) UI
        ui = UiLoader().load(os.path.join(os.path.dirname(os.path.realpath(__file__)),'narwhaldevicespulsegenerator.ui'))        
        self.get_tab_layout().addWidget(ui)
        # Connect signals for buttons
        ui.start_button.clicked.connect(self.start)
        ui.stop_button.clicked.connect(self.stop)
        ui.reset_button.clicked.connect(self.reset)
        # Add icons
        ui.start_button.setIcon(QtGui.QIcon(':/qtutils/fugue/control'))
        ui.start_button.setToolTip('Start')
        ui.stop_button.setIcon(QtGui.QIcon(':/qtutils/fugue/control-stop-square'))
        ui.stop_button.setToolTip('Stop')
        ui.reset_button.setIcon(QtGui.QIcon(':/qtutils/fugue/arrow-circle'))
        ui.reset_button.setToolTip('Reset')
        
        # initialise dictionaries of data to display and get references to the QLabels
        self.status_states = ['stopped', 'reset', 'running', 'waiting']
        self.status = {}
        self.status_widgets = {}
        for state in self.status_states:
            self.status[state] = False
            self.status_widgets[state] = getattr(ui,'%s_label'%state) 
        
        # Not sure what this does.
        # Status monitor timout
        # self.statemachine_timeout_add(2000, self.status_monitor)
        
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
        pass
        # self.status, waits_pending, time_based_shot_over = yield(self.queue_work(self._primary_worker,'check_status'))
        
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
        
    @define_state(MODE_MANUAL|MODE_BUFFERED|MODE_TRANSITION_TO_BUFFERED|MODE_TRANSITION_TO_MANUAL,True)  
    def stop(self,widget=None):
        yield(self.queue_work(self._primary_worker,'pb_stop'))
        self.status_monitor()
        
    @define_state(MODE_MANUAL|MODE_BUFFERED|MODE_TRANSITION_TO_BUFFERED|MODE_TRANSITION_TO_MANUAL,True)  
    def reset(self,widget=None):
        yield(self.queue_work(self._primary_worker,'pb_reset'))
        self.status_monitor()
    
    @define_state(MODE_BUFFERED,True)  
    def start_run(self, notify_queue):
        """Starts the Pulseblaster, notifying the queue manager when
        the run is over"""
        self.statemachine_timeout_remove(self.status_monitor)
        self.start()
        self.statemachine_timeout_add(100,self.status_monitor,notify_queue)

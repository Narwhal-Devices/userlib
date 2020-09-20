from blacs.device_base_class import DeviceTab, define_state, MODE_BUFFERED

class NarwhalPulseGenTab(DeviceTab):
    def initialise_workers(self):
        self.usb_port = str(self.settings['connection_table'].find_by_name(self.device_name).BLACS_connection)
        self.create_worker("main_worker", "user_devices.NarwhalPulseGen.blacs_workers.NarwhalPulseGenWorker",{'usbport':self.usb_port})
        self.primary_worker = "main_worker"

    @define_state(MODE_BUFFERED, True)
    def start_run(self, notify_queue):
        self.wait_until_done(notify_queue)

    @define_state(MODE_BUFFERED, True)
    def wait_until_done(self, notify_queue):
        """Call check_if_done repeatedly in the worker until the shot is complete"""
        done = yield (self.queue_work(self.primary_worker, 'check_if_done'))
        # Experiment is over. Tell the queue manager about it:
        if done:
            notify_queue.put('done')
        else:
            # Not actual recursion since this just queues up another call
            # after we return:
            self.wait_until_done(notify_queue)
    

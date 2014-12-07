import pyslack
import logging
from threading import Thread
from time import sleep

class MessageManager(Thread):
    def __init__(self, cf, eventQueue, *args):
        Thread.__init__(self)
        self.cf = cf
        self.eventQueue = eventQueue
        self.actions = args

    def run(self):
        while 1:
            m = self.eventQueue.get()
            try:
                if("msg" in m):
                    msg = m["msg"]
                    del m["msg"]
                    for action in self.actions:
                        action.sendMessage( msg, **m)
                m = None
            except Exception,e:
                logging.exception(e)
            sleep(.1)

import imp
import os
import logging
from phoneslack.triggers import *
from phoneslack.actions import *
from phoneslack.actions.manager import MessageManager
from threading import Thread
from Queue import Queue
import sys
from ConfigParser import SafeConfigParser as ConfigParser
from traceback import print_exc
__all__ =["actions", "triggers"]



def main():

    if len(sys.argv) > 1:

        confFile = sys.argv[-1]
        cf = ConfigParser()
        cf.read(confFile)
    else:
        print "Usage: sniff.py <conffile>"
        exit()
    
    eventQueue = Queue()
    triggers = cf.get("SlackPhone", "triggers").split(",")
    triggerList= list()
    for t in triggers:
        for i in dir(globals()[t]):
            try:
                x = getattr( globals()[t], i)                
                if issubclass(x, Thread) and x!=Thread:
                    obj = x( cf, eventQueue)
                    triggerList.append(obj)
                    obj.start()
            except Exception, e:
                pass
    actionList = list()
    actions = cf.get("SlackPhone", "actions").split(",")
    for a in actions:
        for i in dir( globals()[a] ):
            x = getattr( globals()[a], i)
            if "Sender" in str(i):
                obj = x(cf)
                actionList.append(obj)

    manager = MessageManager( cf, eventQueue, *actionList)
    manager.start()
    manager.join()


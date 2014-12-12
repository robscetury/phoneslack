import Skype4Py
from threading import Thread
from ConfigParser import SafeConfigParser as ConfigParser
from os import environ
from os.path import join, expanduser
from time import sleep
from datetime import datetime, timedelta
from json import dumps
from urllib2 import Request, urlopen
from traceback import print_exc
import ctypes
DATE_FORMAT = "%b %d, %Y %I:%M:%S %p"
CallIsFinished = set ([Skype4Py.clsFailed, Skype4Py.clsFinished,
                       Skype4Py.clsMissed, Skype4Py.clsRefused,
                       Skype4Py.clsBusy, Skype4Py.clsCancelled])



EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible

class WatcherThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.cfg = ConfigParser()
        self.dateformat = DATE_FORMAT
        self.hostname = "rknapp-phone"
        self.url="http://10.21.34.15:3145/sendmessage"
        print "Config parser"
        try:
            self.cfg.read( join(expanduser("~"), ".watcher.cfg") )            
        except:
            print_exc()
            pass

    def sendMessage(self, msg):
        message = dict( username=self.getSetting("username"),
                        hostname = self.getSetting("hostname"),
                        dt = datetime.now().strftime(self.getSetting("dateformat") ),
                        msg = msg)
        req = Request( self.getSetting("url"), dumps(message), {"Content-Type":"application/json"})
        u = urlopen(req)
        resp = u.read()
        u.close()
        return resp
    
    def getSetting(self, name):
        try:
            return self.cfg.get("Skype", name)
        except:
            print_exc()
            if hasattr(self, name):
                return getattr(self, name)
        return ""


class VidyoWatcher(WatcherThread):

    def __init__(self):
        WatcherThread.__init__(self)        
        self.username = "Rob Knapp"
        self.incall = False
        
    
    def procWindows(self, hwnd, lParam):
            if IsWindowVisible(hwnd):
                length = GetWindowTextLength(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                GetWindowText(hwnd, buff, length + 1)
                buff = buff.value                
                if self.incall:

                    if buff.startswith("VidyoDesktop") and buff.endswith("/services/"):
                        self.sendMessage("%(dt)s: %(username)s is out of Vidyo Call")
                        #print "off call"
                        self.incall = False
                else:        
                    if buff.startswith("VidyoDesktop") and not buff.endswith("/services/"):
                        self.sendMessage("%(dt)s: %(username)s is in Vidyo Call")
                        #print "on call"
                        self.incall = True       
    def run( self ):
        while 1:
            EnumWindows( EnumWindowsProc( self.procWindows), 0 )
            sleep(1) 
                    
class SkypeWatcher(WatcherThread):

    def __init__(self):
        WatcherThread.__init__(self)
        self.skype = Skype4Py.Skype()
        
        if not self.skype.Client.IsRunning:
            self.skype.Client.Start()
        
        self.skype.Attach()
        print "Attached"
        self.calls = set()
        
    
    def CallStatusText(self, status):
        return self.skype.Convert.CallStatusToText(status)
    
    def getName( self, user ):
        if(hasattr(user, "FullName") and user.FullName!=""):
            return user.FullName        
        elif(hasattr(user, "DisplayName") and user.DisplayName!=""):
             return user.DisplayName
        elif(hasattr(user, "Handle")):
            return user.Handle
        elif(hasattr( user, "PartnerDisplayName") and user.PartnerDisplayName!=""):
             return user.PartnerDisplayName
        elif(hasattr( user, "PartnerHandle")):
             return user.PartnerHandle
            
    def getCallUserString(self, call):
        userList = list()
        if len(call.Participants)>0:
            for u in call.Participants:
                userList.append( self.getName(u) )
        userList.append( self.getName( call ) )
        return userList

    def datestamp(self):
        return datetime.now().strftime(self.getSetting("dateformat"))
    
    def CallFinish(self, callId):
        self.calls.remove(callId)
        msg = "%(dt)s: %(username)s is off call"
        print msg
        self.sendMessage( msg )
             
    def OnCall(self, call):
        
        self.calls.add(call.Id)
        msg = u"%(dt)s: %(username)s is on call with "
        userList = self.getCallUserString(call)
        msg += " %s"%( unicode(u",".join(userList)))
        self.sendMessage( msg )
        print msg

    
        
    def run(self):
        print "running.."
        while 1:
            currentCalls = set()
            if(len(self.skype.ActiveCalls)>0 ):                
                for call in self.skype.ActiveCalls:
                    currentCalls.add(call.Id)
                    if call.Id not in self.calls:
                        self.OnCall( call )
            endedCalls = self.calls - currentCalls
            for callId in endedCalls:
                self.CallFinish(callId)
            sleep(1)
            
if __name__=="__main__":
             v = VidyoWatcher()
             v.start()
             t = SkypeWatcher()
             t.start()
             while 1:
                 try:
                    t.join(1)
                    v.join(1)
                 except:
                     exit()

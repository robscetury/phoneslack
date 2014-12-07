from urllib2 import urlopen
import logging
from threading import Thread
import socket
from time import sleep
import datetime

class SkypeThread(Thread):
	
	def __init__(self, cf, eventQueue):
		Thread.__init__(self)
		self.url = "http://mystatus.skype.com/%s.txt"
                self.users = cf.get("SlackPhone","skypeuser").split(",")
                self.status = dict()
                self.incall = dict()
                for u in self.users:
                    self.status[u] = "Online"
                    self.incall[u] = False
		self.onphonestatus = cf.get("SlackPhone", "skypestatus")
		self.timeout = cf.getfloat("SlackPhone", "skypesleep")
                hostname = cf.get("SlackPhone", "slackbotname")
                if hostname=="{hostname}":
                        hostname = socket.gethostname()
                self.hostname = hostname
                self.DATE_FORMAT=cf.get("SlackPhone", "dateformat")
                self.eventQueue = eventQueue

	def run(self):
            global slack, DATE_FORMAT, slack, slackchannel, hostname
            logging.info("Starting skype thread")
            while 1:
                try:
                    for usr in self.users:
                        logging.info("getting '%s'"%( self.url%usr) )
                        u = urlopen(self.url%usr)
                        logging.info(u.getcode())
                        if(u.getcode() == 200):
                            data = u.read()
                            dt = datetime.datetime.now()
                            logging.info("'%s'"%data)
                            if data != self.status[usr]:
                                logging.warn("Status changed to %s"%data)
                                self.status[usr]= data
                                logging.warn("in call?%s"%self.incall[usr])
                                if self.status[usr] == self.onphonestatus and not self.incall[usr]:
                                    logging.warn("Starting skype call: %s"%self.status[usr])
                                    self.eventQueue.put( dict( msg="%(dt)s: %(username)s on Skype.",
                                                               username=usr,
                                                               hostname=self.hostname,
                                                               dt = dt.strftime( self.DATE_FORMAT)))
                                    self.incall[usr]=True
                                elif self.status[usr]=="Online" and self.incall[usr]:
                                    logging.warn("Ending Skype Call: %s"%self.status[usr])
                                    self.eventQueue.put( dict( msg="%(dt)s: %(username)s off Skype",
                                                               username=usr,
                                                               hostname=self.hostname,
                                                               dt = dt.strftime(self.DATE_FORMAT)))
                                    self.incall[usr]=False

                except KeyboardInterrupt, e:
                    return
                except Exception, e:
                    logging.exception(e)
                    pass
                finally:
                    logging.warn("Sleeping for %s"%self.timeout)
                    sleep(self.timeout)

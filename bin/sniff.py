#!/usr/bin/python
import socket
from struct import *
import datetime
import pcapy
import sys
import os
import pyslack
import logging
import netinfo
from threading import Thread
from urllib2 import urlopen
from time import sleep
from ConfigParser import SafeConfigParser as ConfigParser

logging.basicConfig(filename="/var/log/slackphone.log", level=logging.WARN)


class SkypeThread(Thread):
	
	def __init__(self, skypename, skypetimeout, skypestatus):
		Thread.__init__(self)
		self.url = "http://mystatus.skype.com/%s.txt"%skypename
		self.status = "Online"
		self.onphonestatus = skypestatus
		self.timeout = skypetimeout
		self.incall = False
	def run(self):
		global slack, DATE_FORMAT, slack, slackchannel, hostname
		logging.info("Starting skype thread")
		while 1:
			try:
				logging.info("getting %s"%self.url)
				u = urlopen(self.url)
				logging.info(u.getcode())
				if(u.getcode() == 200):
					data = u.read()
					dt = datetime.datetime.now()
					logging.info("'%s'"%data)
					if data != self.status:
						logging.warn("Status changed to %s"%data)
						self.status= data
						if self.status == self.onphonestatus and not self.incall:
							 logging.warn("Starting skype call: %s"%self.status)
							 slack.chat_post_message(slackchannel,
		        	                                "%s: I'm on Skype."%dt.strftime(DATE_FORMAT),
        		        	                        username=hostname)
							 self.incall=True
						elif self.status=="Online" and self.incall:
							logging.warn("Ending Skype Call: %s"%self.status)
					                slack.chat_post_message(slackchannel,
			                                "%s: I'm off Skype"%dt.strftime(DATE_FORMAT),
                        				        username=hostname)
							self.incall=False

			except KeyboardInterrupt, e:
				return
			except Exception, e:
				logging.exception(e)
				pass
			finally:
				sleep(self.timeout)

def parse_packet( header, packet):
	eth_length = 14
	eth_header= packet[:eth_length]
	eth = unpack("!6s6sH", eth_header)
	eth_protocol = socket.ntohs(eth[2])

	if eth_protocol == 8:
		ip_header = packet[eth_length:20+eth_length]
		iph = unpack("!BBHHHBBH4s4s", ip_header)
		version_ihl = iph[0]
	        version = version_ihl >> 4
        	ihl = version_ihl & 0xF
 
        	iph_length = ihl * 4
 
        	ttl = iph[5]
        	protocol = iph[6]
        	s_addr = socket.inet_ntoa(iph[8]);
        	d_addr = socket.inet_ntoa(iph[9]);

		if protocol == 17:
			u = iph_length + eth_length
            		udph_length = 8
     			udp_header = packet[u:u+8]
 
            		#now unpack them :)
            		udph = unpack('!HHHH' , udp_header)
             
            		source_port = udph[0]
            		dest_port = udph[1]
            		length = udph[2]
            		checksum = udph[3]
			if (source_port >=50000 and source_port <=50511) or (dest_port >= 50000 and dest_port < 50511):
				#print s_addr, d_addr
				if valid_packet( s_addr, d_addr):
					processCall( datetime.datetime.now(), s_addr, d_addr )

	hasCallEnded( datetime.datetime.now() )

def valid_packet( source, dest):
	global gateway, broadcast
	if dest == "224.0.0.252" or source == "224.0.0.252":
		logging.debug("rejected IGMP traffic")
		return False
	if dest == broadcast or source == broadcast:
		logging.debug("rejected broadcast traffic")
		return False
	if dest==gateway or source == gateway:
		logging.debug("rejected traffic to gateway")
		return False
	if dest=="239.255.255.250" or source == "239.255.255.250":
		logging.debug("INANA traffic, rejected")
		return False

	return True

def processCall( dt , source, dest):
	global inCall, lastPacket, packetCount, minPackCount, slackchannel
	if not inCall:
		lastPacket = dt
		packetCount += 1
		if packetCount > minPackCount:
			global hostname
			logging.warn( "Call Started %s"%dt)
			inCall = True
			slack.chat_post_message(slackchannel,
					"%s: I'm on the phone."%dt.strftime(DATE_FORMAT),
					username=hostname)
			logging.debug("call started")
		logging.debug( "packet from %s to %s, packecount is %s"%(source, dest, packetCount))

	else:
		lastPacket = dt

def hasCallEnded( dt):
	global inCall, lastPacket, slackchannel
	if inCall:
		logging.info( "time diff %s"%(dt - lastPacket).seconds)
	if inCall and ( dt - lastPacket) > datetime.timedelta(seconds=1.5):
		global hostname
		slack.chat_post_message(slackchannel,
				"%s: I'm off the phone"%dt.strftime(DATE_FORMAT),
				username=hostname)
		logging.warn( "Call Ended %s"%dt)
		inCall = False
		lastPacket = None 
		packetCount =0
		
if __name__=="__main__":
	global SLACK_API, minPackCount, DATE_FORMAT, gateway, broadcast, slackchannel,hostname, inCall, lastPacket, packetCount

	SLACK_API=None
	inCall = False
	lastPacket = None
	packetCount = 0
	minPackCount=10
	hostname = socket.gethostname()
	DATE_FORMAT="%b %d, %Y %I:%M:%S %p"
	broadcast=None
	gateway=None
	slack = None
	slackchannel = None

	if len(sys.argv) > 1:
		confFile = sys.argv[-1]
		cf = ConfigParser()
		cf.read(confFile)
		SLACK_API=cf.get("SlackPhone", "slacktoken")
		minPackCount=cf.getint("SlackPhone", "minpacketcount")
		DATE_FORMAT=cf.get("SlackPhone", "dateformat")
		wirelessinterface = cf.get("SlackPhone", "wlaninterface")
		broadcast=netinfo.get_broadcast(wirelessinterface)
		gateway=netinfo.get_routes(wirelessinterface)[0]["gateway"]
		skypesleep = cf.getint("SlackPhone", "skypesleep")
		skypeuser= cf.get("SlackPhone", "skypeuser")
		skypestatus = cf.get("SlackPhone", "skypestatus")
		slackchannel = cf.get("SlackPhone", "channel")
		hostname = cf.get("SlackPhone", "slackbotname")
		if hostname=="{hostname}":
			hostname = socket.gethostname()
	else:
		SLACK_API="{PUT YOUR SLACK TOKEN HERE}"
		minPackCount=10
		hostname = socket.gethostname()
		DATE_FORMAT="%b %d, %Y %I:%M:%S %p"
		broadcast=netinfo.get_broadcast("wlan0")
		gateway=netinfo.get_routes("wlan0")[0]["gateway"]
		skypesleep = 10
		skypeuser= "{Put Your Skype User Here}"
		skypestatus = "Away"
		slackchannel = "#phonealert"

	logging.warn("gateway:%s, broadcast:%s"%(gateway, broadcast))
	logging.warn("minPacketCount %s"%minPackCount)
	logging.warn("DATE_FORMAT %s"%DATE_FORMAT)
	logging.warn("skypeuser %s"%skypeuser)
	logging.warn("skypestatus %s"%skypestatus)
	logging.warn("slackchannel %s"%slackchannel)
	logging.warn("slackbotname %s"%hostname)
	slack = pyslack.SlackClient(SLACK_API)
	devices = pcapy.findalldevs()
	logging.info( devices)
	skype = SkypeThread(skypeuser, skypesleep, skypestatus)
	skype.start()
	if "bridge0" not in devices:
		logging.info( "Starting bridge device")
		os.system("/bin/bash /usr/bin/startBridge.sh")
	
	dev ="bridge0"
	cap = pcapy.open_live( dev, 65536, 1, 0)

	while(1):
		(header, packet) = cap.next()
		parse_packet(header, packet)


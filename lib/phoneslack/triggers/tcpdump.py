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
import json

def valid_mitel_packet(  s_addr, d_addr, source_port, dest_port, gateway, broadcast ):
	 if (source_port >=50000 and source_port <=50511) or (dest_port >= 50000 and dest_port < 50511):

		 if d_addr == "224.0.0.252" or s_addr == "224.0.0.252":
			 logging.debug("rejected IGMP traffic")
			 return False
		 if d_addr == broadcast or s_addr == broadcast:
			 logging.debug("rejected broadcast traffic")
			 return False
		 if d_addr==gateway or s_addr == gateway:
			 logging.debug("rejected traffic to gateway")
			 return False
		 if d_addr=="239.255.255.250" or s_addr == "239.255.255.250":
			 logging.debug("INANA traffic, rejected")
			 return False

		 return True
	 return False


		


class TcpFilter(Thread):
	def __init__(self, cf, eventQueue):
		Thread.__init__(self)
		self.minPackCount=cf.getint("SlackPhone", "minpacketcount")
		self.wirelessinterface = cf.get("SlackPhone", "wlaninterface")
		self.broadcast=netinfo.get_broadcast(self.wirelessinterface)
		self.gateway=netinfo.get_routes(self.wirelessinterface)[0]["gateway"]
		self.device = cf.get("SlackPhone", "inetdevice")
		self.startDev = cf.get("SlackPhone", "startdevice")
		self.devices = pcapy.findalldevs()
		self.valid_packet = globals()[ "valid_%s_packet"%cf.get("SlackPhone", "phonetype")]
		logging.info( self.devices)
		try:
			self.filter = cf.get("SlackPhone", "tcpfilter")
		except:
			self.filter = None
		try:
			phonemap = cf.get("SlackPhone", "phonemap")
		except:
			phonemap = None

		try:
			self.phonemap = json.loads( phonemap )
		except Exception, e:
			logging.exception(e)
			self.phonemap = {}
		logging.info( str( self.phonemap) )
		self.hostname = cf.get("SlackPhone", "slackbotname")	
		self.DATE_FORMAT=cf.get("SlackPhone", "dateformat")
                if self.hostname=="{hostname}":
			self.hostname = socket.gethostname()

		self.eventQueue = eventQueue
		self.inCall = False
		self.lastPacket = None
		self.packetCount = 0
		self.openCalls = dict()		

	def processCall( self, dt , source, dest, source_mac="", dest_mac=""):
		if not self.inCall:			
			self.packetCount += 1
			self.lastPacket = dt
			if self.packetCount > self.minPackCount:
				self.packetCount =0
				username = self.mapPhone( source_mac, dest_mac )
				if username:
					logging.warn( "Call Started %s"%dt)
					self.inCall = True
					if self.getLocalMac( source_mac, dest_mac) != -1:
						self.openCalls[self.getLocalMac( source_mac, dest_mac) ] = dt
					self.eventQueue.put( dict( msg="%(dt)s: %(user)s on the phone.",
								   user=username,
								   hostname = self.hostname, 
								   dt=dt.strftime( self.DATE_FORMAT)) )
					logging.debug("call started")
					logging.debug( "packet from %s to %s, packecount is %s"%(source, dest, self.packetCount))
		elif self.inCall:
			self.lastPacket = dt
			if( self.getLocalMac( source_mac, dest_mac) != -1):
				self.openCalls[ self.getLocalMac( source_mac, dest_mac)] = dt

	def getLocalMac( self, source, dest):
		#logging.info("source = %s, dest=%s"%(source, dest) )
		if not self.phonemap:
			return -1
		elif source in self.phonemap:
			return source
		elif dest in self.phonemap:
			return dest
		
	def mapPhone( self, source, dest):
		logging.info( "source mac %s, dest %s"%(source, dest))
		if not self.phonemap:
			return self.hostname
		elif source in self.phonemap:
			return self.phonemap[source]
		elif dest in self.phonemap:
			return self.phonemap[dest]

	def hasCallEnded( self, dt, source_mac="", dest_mac=""):
		#if self.inCall and self.lastPacket:
		#
		if self.getLocalMac( source_mac, dest_mac) == -1 and self.inCall and ( dt - self.lastPacket) > datetime.timedelta(seconds=1.5):
			self.endCall( dt, source_mac, dest_mac)
		elif self.inCall:
			for k in self.openCalls:				
				if (dt-self.openCalls[k]) > datetime.timedelta( seconds=1.5):
					self.endCall( dt, k, dest_mac )
		
	def endCall( self, dt, source_mac, dest_mac):		
		username = self.mapPhone( source_mac, dest_mac)
		logging.info("ending call for %s"%username)
		if username:
			self.eventQueue.put( dict( msg=	"%(dt)s: %(user)s off the phone",
						   user=username,
						   hostname=self.hostname,
						   dt = dt.strftime( self.DATE_FORMAT)) )
			logging.warn( "Call Ended %s"%dt)
		self.inCall = len(self.openCalls) == 0
		self.lastPacket = None 
		self.packetCount =0
		#elif self.lastPacket:
		#	logging.info( "time diff %s"%(dt - self.lastPacket).seconds)
	def mac_string(self, s):
		return "%.2x:%.2x:%.2x:%.2x:%.2x:%.2x"%( ord(s[0]), ord(s[1]), ord(s[2]), ord(s[3]), ord(s[4]), ord(s[5]) )

	def parse_packet( self, header, packet):
		eth_length = 14
		eth_header= packet[:eth_length]
		eth = unpack("!6s6sH", eth_header)
		eth_protocol = socket.ntohs(eth[2])
		dest_mac = self.mac_string(packet[0:6])
		source_mac = self.mac_string(packet[6:12])
		
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

				if( self.valid_packet(s_addr, d_addr, source_port, dest_port, self.broadcast, self.gateway) ):
					self.processCall( datetime.datetime.now(), s_addr, d_addr , source_mac, dest_mac)

		self.hasCallEnded( datetime.datetime.now() , source_mac, dest_mac )

	def monitortcp(self):
		if self.device not in self.devices and self.startDev!="":
			logging.info( "Starting bridge device")
			os.system(self.startDev)
	
		cap = pcapy.open_live( self.device, 65536, 1, 0)
		if(self.filter):
			cap.setfilter(self.filter)

		while(1):
			try:
				(header, packet) = cap.next()
				self.parse_packet(header, packet)
			except Exception, e:
				logging.exception(e)

	def run(self):
		self.monitortcp()

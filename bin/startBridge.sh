#!/bin/bash
# startBridge.sh
# Automatic bridge creation and packet capture (plug-and-capture) on a Raspberry Pi
# 'Inspired' by William Knowles' PiTap.
#  Took his script and removed some fucntionaly, rather than learn a bunch of 
#  bridge-utils stuff myself.
# Original Developer: William Knowles
# Website: williamknowles.co.uk
# Twitter: twitter.com/william_knows
# Modified By Rob Knapp  rknapp@voxintconsultants.com

### PATH SETUP
baseDirectory=/var/log/
logFile=$baseDirectory/slackphone.log

### BRIDGE NETWORK INTERFACES
# Create bridge and add interfaces.
brctl addbr bridge0
brctl addif bridge0 eth0
brctl addif bridge0 eth1
# Zero the IP addresses on the interfaces.
ifconfig eth0 0.0.0.0
ifconfig eth1 0.0.0.0
# Start the bridge.
ifconfig bridge0 up


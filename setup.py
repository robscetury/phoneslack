#!/usr/bin/env python

from distutils.core import setup

setup(name="phoneslack",
	version="0.1a",
	description="Phone interface between slack and phone/voip systems",
	author="Rob Knapp",
	author_email="rknapp@voxintconsultants.com",
	packages=[],
	data_files = [
			("/etc/init.d", ["init.d/sniffer"]),
			("/etc/sniffer", ["config/sniff.conf"]),
			("/usr/bin/", ["bin/sniff.py", "bin/startBridge.sh"])],
	requires=["pycapy", "netinfo", "pyslack"]
	)
	
	

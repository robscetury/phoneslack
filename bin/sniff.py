#!/usr/bin/python

import logging
import os
import sys

sys.path.append( os.curdir)

import phoneslack
logging.basicConfig(filename="/var/log/slackphone.log", level=logging.INFO)

if __name__=="__main__":
	phoneslack.main()

phoneslack
==========

An interface to post to slack when on the phone/in Skype call

Why would you do this?
----------------------

Recently, my company moved to a new office.  Three developers that were used to having separate offices where put into a single office with cubicles.  Two of us -- I'm one of them -- have loud voices.  So it's almost impossible for one person to be on the phone and the other two have a conversation at the same time. (Always about work, of course. :) ).

Anyway, the phone calls we are one can tend to be long, and often we are listening to a meeting of users trying to process the conversation for requirements.  So --> on the phone for a long time, mostly silent...which leads to people forgetting to be quiet.

After a few days, we got in the habit of saying "I'm calling..." or "On the phone with..." but like I said that can get forgotten easily.  So we came up with the idea of having an LED sign that says "Rob is on the phone with Cletus" (or whomever) so that we have easy visual clues about people's phone states.

This is the first step in that direction. Its is a simple script, that I run on a raspberry pi that is setup as a network tap between my VoIP (mitel) phone and the network.

When it detects "mitel phone like activity", it posts to a slack channel, letting my coworkers know I'm on the phone.
(We work in a small office and have loud voices...)

What it does:

1) My company uses mitel phones that utilize the minet protocol.  This makes me sad, since SIP provides much richer data.... but alas, they don't.
They also run the minet using what could be SSL encryption over TCP 6800 for control and UDP traffic over ports 50000-50511.  If it detects UDP traffic in that range that isn't IGMP or other non-mitel traffic, it's posts an "I'm on the phone" message to slack, once it stops, it posts "I'm off the phone."

2)We also use Skype extensively.  So, phoneslack can also detect Skype calls, using two different methods: 

2a) IF Skype has been configured to change status when on a call.  You will need to enable Skype web status (http://goo.gl/2zDxHE) and provide your Skype username.  It does this by polling your status every 10 seconds.  If it switches from "Online" to "Away", then it says you are on the phone.  (You can change what status it looks for in the conf file... I found that if I used "Do not Disturb", then if my windows 7 machine locked, phoneslack would post a false positive when I unlocked the screen... meaning Skype changes your status briefly during that time.  Not sure why it would do that.

2b) In the client sub directory, there is a watcher that will monitor Skype and vidyo (another application we use).  When Skype (or vidyo) calls, the watcher will post a message to the phoneslack server running on the pi. (You'll need to provide a configuration on the windows box for this to work.)   When using Skype, metadata is provided about the call.

In this mode, the phoneslack server must be configured to run with the webserver plugin.  Please not that currently there is NO SECURITY on these messages.  The webserer will accept messages from anyone and try to post them.  And the messages are sent in plain text. I'll probably fix that at some point, but for now its something you should think about before using in this mode.

What it doesn't do:
	1) Work with anything other than mitel phones
	2) capture the meta data
	3) interface with an LED sign (that will be a separate app that takes slack messages and displays them, which will be part of this package eventually.)
	

This is super simple and whipped together quickly.  I expect to improve:

1) I'd like to get meta data, but sadly my mitel phone uses encryption

2) Like to support additional phones and sip

3) Like to support other forms of communication... Mozilla's hello, hangouts, etc.

4) If when I get a smart watch, I'll probably do some integration there as well.

5) Improve the architecture.

Rough Instructions:

You will need a:

Raspberry Pi B/B+ model (I used B+)

A Rasp compatible Wifi Dongle

A Rasp Compatible USB Ethernet Adapter

A Rasp Case

An SD Card

For setup you'll need a keyboard and monitor

0) Assemble the pi.

1) Install Raspbian ( http://raspbian.org )

2) Install tcpdump/libpcap

3) Install python and python-dev

4) Configure your wifi dongle (this is what will connect to slack), the other Ethernet plugs will run the network tap.

5) Put the raspberry pi inline with your sip phone, connecting eth0 to your router and eth1 to your phone. (Reverse will work too.):
    router ------- rasppi ------ phone
    [ Dig the fancy ascii art. :) ]

6) I *think* after that all you'll need to do is "sudo python seutp.py install"

7) Modify /etc/sniffer/sniff.conf and fill in values in {}  (except hostname if that is what you want the slack bot to be called...)

8)  run "sudo update-rc.d sniffer defaults" and then restart the pi.

9) Optional: On the windows box you are using (if you are), copy the "client" directory and in a console run python.exe setup.py py2exe, this will generate an executable you can put in your startup folder to enable the Skype/vidyo watcher.  (Copy .watcher.cfg to your home directory and modify as needed.)

By "think" I mean the setup is untested.  I did everything manually and then wrote the setup by trying to remember what I've done.

While the pi is booting, your phone will be disconnected from the network.  
Once the sniffer service is up and running, your phone should connect normally.


Support:
You can reach me for support at rknapp at voxintconsultants dot com.  I'll help where I can, I know Linux fairly well but am pretty new to raspberry pi -- this is my first solo project.  So I may not be too helpful with the pi specific stuff.


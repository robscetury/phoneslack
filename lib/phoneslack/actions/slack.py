import pyslack
import logging
from threading import Thread


class SlackSender(object):
    def __init__(self, cf ):
        self.SLACK_API=cf.get("SlackPhone", "slacktoken")
        self.slack = pyslack.SlackClient(self.SLACK_API)
        self.slackchannel = cf.get("SlackPhone", "channel")

    def sendMessage( self, msg, **kwargs):
        username = kwargs["hostname"]
        self.slack.chat_post_message(self.slackchannel,
                                     msg%kwargs,
                                     username=kwargs["hostname"])

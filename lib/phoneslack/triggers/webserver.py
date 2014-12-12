import SimpleHTTPServer
import SocketServer
from threading import Thread
from json import loads
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from cgi import FieldStorage
import logging 

class MessageHandler(BaseHTTPRequestHandler):
    eventQueue = None
    def do_POST(self):
        try:
            path = self.path
            contentLength = int(self.headers["content-length"])
            logging.info( "I got path %s"%path)
            logging.info( MessageHandler.eventQueue) 
            if path=="/sendmessage":
                logging.info("Its the correct path")
                msg = loads( self.rfile.read(contentLength) )
                logging.info("got message %s"%str(msg) )
                
                MessageHandler.eventQueue.put( msg )
            self.send_response(200)
            self.end_headers()
            self.wfile.write("OK")
        except Exception, e:
            logging.exception(e)

        logging.info("done")
        return

class WebServerThread(Thread):
    	def __init__(self, cf, eventQueue):
		Thread.__init__(self)
                self.cf = cf
                self.port = cf.getint("SlackPhone", "port")
                MessageHandler.eventQueue = eventQueue

        def run(self):
            logging.info("starting webserver")
            server = HTTPServer(("", self.port), MessageHandler)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                server.socket.close()
            except Exception, e:
                logging.exception(e)

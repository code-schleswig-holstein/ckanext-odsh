import socket
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import time
import requests
import pdb
import threading
import asyncore


hostName = "localhost"
hostPort = 5002

# data = "test"
# with open('catalog.rdf', 'r') as myfile:
#         data=myfile.read()

# TODO: better was to set data on RequestHandler
data = ""

class RequestHandler(BaseHTTPRequestHandler):

    # GET
    def do_GET(self):
        self.send_response(requests.codes.ok)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(data.encode("utf-8"))

    # POST
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        self.send_response(200)
        print(post_data)
        self.wfile.write("".encode("utf-8"))  # send back to client

    def do_HEAD(self):
        self.send_response(requests.codes.ok)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()


class HarvestServerMock(threading.Thread):
    def __init__(self):
        # init thread
        self._stop_event = threading.Event()
        self.thread_name = self.__class__
        self.server = HTTPServer((hostName, hostPort), RequestHandler)
        threading.Thread.__init__(self, name=self.thread_name, target=self.server.serve_forever)
        # self.setDaemon(True)


#     def run(self):
#         while not self._stop_event.isSet():
#             asyncore.loop(timeout=0.01, count=1)

        # pdb.set_trace()

        # try:
        # except KeyboardInterrupt:
        #         pass

    def close(self):
        self.server.server_close()
       # print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))

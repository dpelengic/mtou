#!/usr/bin/python
import sys
import socket
import struct
import re
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn
import thread
import errno

RES_ERROR = 400
RES_OK = 200
SERVER_RUNNING = 1


def ip_regex(self, mode):
    """IP address regex"""
    if mode: # mcast range
        isvalid = re.match(r"^(2(2[4-9]|3[0-9]))\.([0-9]|[1-9][0-9]|1([0-9][0-9])|2([0-4][0-9]|5[0-5]))\.([0-9]|[1-9][0-9]|1([0-9][0-9])|2([0-4][0-9]|5[0-5]))\.([0-9]|[1-9][0-9]|1([0-9][0-9])|2([0-4][0-9]|5[0-5]))$", self)
    else: # whole ipv4 range
        isvalid = re.match(r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$", self) 

    if isvalid:
        return 1
    else:
        return None

def validate_ip_port(IP, PORT, mode):
    """Validate IP/PORT"""

    # check PORT validity
    if str.isdigit(PORT) and 0 < int(PORT) <= 65535:
        pass
    else:
        return None

    # check IP validity
    isvalid = ip_regex(IP, mode) # 0 for whole IP range, 1 for multicast
    if isvalid:
        return 1
    else:
        return None


class Handler(BaseHTTPRequestHandler):
    """This class will handle any incoming request"""

    protocol_version = "HTTP/1.1"

    def finish(self,*args,**kw):
        """Call this instead of base class finish(), after client closed connections cases"""
        try:
            if not self.wfile.closed:
                self.wfile.flush()
                self.wfile.close()
        except socket.error:
            pass
            self.rfile.close()

    def mcast_join(self, MCAST_GRP, MCAST_PORT):
        """Join on requested MCAST channel"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((MCAST_GRP, int(MCAST_PORT)))
        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while SERVER_RUNNING: # Flag checking if server is undergoing shutdown
            try:
                self.wfile.write(sock.recv(10240)) # Relay the traffic
            except socket.error as e:
                if e.errno == errno.EPIPE:
                    print "Client closed connection."
                else:
                    print("Unhandled error: ", e)
                break

    def do_GET(self):
        """Handler for the GET requests"""

        MCAST_PAIR = self.path.split(":")

	if 2 == len(MCAST_PAIR): # expecting two parameters in list, IP and PORT
	    MCAST_GRP = MCAST_PAIR[0].translate(None, "/")
	    MCAST_PORT = MCAST_PAIR[1]
	    mcastisvalid = validate_ip_port(MCAST_GRP, MCAST_PORT, 1) # mode = 1, validating mcast ip range
	else:
	    #print("Missing parameters.")
            rcode =  RES_ERROR
            self.send_error(rcode, "Missing parameters")
            self.end_headers()
            return

        if mcastisvalid: # Success, join multicast group and relay
            rcode = RES_OK
	    self.send_response(rcode)
            self.end_headers()
	    self.mcast_join(MCAST_GRP, MCAST_PORT)		
        else: # Fail with error
            rcode = RES_ERROR
	    self.send_error(rcode, "Invalid IP/PORT")
	    self.end_headers()
	return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle each request in separate thread"""


try:
    print "Usage: ./application <IP> <PORT>"    
    print "eg.: ./application 192.168.1.10 80" 
    print "##################################\n"
    if 3 > len(sys.argv):
        print "Defaulting bind to 0.0.0.0:8080..."
        BIND_IP = "0.0.0.0"
        PORT_NUMBER = 8080
    else:
        BIND_IP = sys.argv[1]
        PORT_NUMBER = sys.argv[2]
        
    bindisvalid = validate_ip_port(BIND_IP, str(PORT_NUMBER), 0) # mode = 0, validating entire ipv4 range
    if bindisvalid:
        """Create a web server and define the handler to manage the incoming request"""
        try:
            server = ThreadedHTTPServer((BIND_IP, int(PORT_NUMBER)), Handler)
            print "Started httpserver on " , BIND_IP, PORT_NUMBER
            server.serve_forever() # Wait forever for incoming http requests
        except socket.error as e:
            if (e.errno == errno.EADDRNOTAVAIL) or (e.errno == errno.EADDRINUSE):
                print "Cannot assign requested address/port."
            elif e.errno == errno.EACCES:
                print "Permission denied. Are you root?"
            else:
                print("Unhandled error: ", e)
    else:
        print "Invalid IP/PORT."

except KeyboardInterrupt:
    print "\nShutting down..."
    SERVER_RUNNING = 0 # Server undergoing shutdown, terminate playout loops with this flag
    server.shutdown()
    server.server_close()

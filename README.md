# MTOU

(M)ulticast (TO) (U)nicast - MTOU, will transmit Multicast traffic via Unicast.
This makes it, for example, possible to watch Multicast video streams from a local content provider anywhere in the world.

## About

MTOU should be started on a machine, that has access to Multicast video streams.
Running MTOU will start a HTTP server, accepting any request with a valid Multicast IP/Port pair in path parameter. MTOU will then join to the specified Multicast channel, and relay all traffic back to the client via Unicast.

All requests are handled in a separate thread, so multiple clients, targeting different streams are possible. CPU and memory usage is minimal, bandwidth is dependant on number of clients and stream bitrate.

Tested Python version:
```
$ python -V
Python 2.7.9
```

## Example usage

Make the application executable:
```
$ chmod +x mtou.py 
```

Starting the MTOU server with default bind options:
```
$ ./mtou.py 
Usage: ./application <IP> <PORT>
eg.: ./application 192.168.1.10 80
##################################

Defaulting bind to 0.0.0.0:8080...
Started httpserver on  0.0.0.0 8080
```

Starting the MTOU server with custom IP / Port parameters:
```
$ ./mtou.py 127.0.0.1 8080
Usage: ./application <IP> <PORT>
eg.: ./application 192.168.1.10 80
##################################

Started httpserver on  127.0.0.1 8080
```
___

Example Client request (Tested with VLC media player):
```
http://127.0.0.1:8080/239.1.1.1:5000
```
Note that path parameter should be a valid Multicast IP and Port pair. Putting any other/more parameters, will fail with HTTP 400 error code.

_This example also assumes video content is available on MTOU server, Multicast address 239.1.1.1, port 5000._

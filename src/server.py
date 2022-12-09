from node import Node

import json
import socket
import threading
import sys

FILENAME = "movie.Mjpeg"
BOOTSTRAP = "bootstrap.json"

class Server(Node):
    
    def __init__(self, host, bootstrapper):
        super(Server, self).__init__(host, bootstrapper)

    def connect(self, address, port):
        self.ativos.add(address)
        self.socket.sendto(("STREAMING").encode('utf-8') ,(address, port))

    def disconnect(self, address, port):
        pass

    def main(self):

        threading.Thread(target=self.listen, args=()).start()
        self.socket.sendto("NEIGHBOURS".encode('utf-8'), (self.bootstrapper, 4000))


if __name__ == '__main__':

    server = Server(sys.argv[1], sys.argv[2])
    server.main()

# python3 node.py 10.0.1.2 3001 10.0.0.10
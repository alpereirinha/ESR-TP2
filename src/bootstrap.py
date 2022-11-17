from node import Node

import socket
import threading

BOOTSTRAP = "bootstrap.json"

class Bootstrap(Node):
    def __init__(self, host, port):
        super().__init__(host, port)
        

   """  def main(self):
        threading.Thread(target=startServer, args=()).start() """

    def sendNeighbours(self, ip):

        try:
            data = json.load(open('bootstrap.json', 'r'))
        except:
            raise IOError
        
        for i in data:
            if ip in i['node']:
                msg = ' '.join(i['vizinhos'])
                self.socket.sendto(msg.encode('utf-8'), (ip, 3000))


if __name__ == '__main__':
    server = Server()
    server.main()
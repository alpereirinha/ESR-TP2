from node import Node
import socket, threading, sys, os, time
from pprint import pprint

class Client:

    def __init__(self, host):

        self.host = host
        self.port = 3000
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((host, 3000))
        self.lock = threading.Lock()

    
    def connect(self, addr):

        self.socket.sendto(("CONNECT " + str(self.host)).encode('utf-8'), (addr, 3000))


    def process(self, addr):
        
        self.connect(addr)

        while True:
            
            data, (address, port) = self.socket.recvfrom(1024) #probably vai ter que ser alterado
            aux_msg = data.decode('utf-8').split(' ')
            print(aux_msg)

    def streaming(self, addr):

        time.sleep(5)
        self.socket.sendto(("DISCONNECT " + str(self.host)).encode('utf-8'), (addr, 3000))

    def main(self, addr):

        threading.Thread(target=self.process, args=([addr])).start()
        threading.Thread(target=self.streaming, args=([addr])).start()
        

if __name__ == '__main__':

    client = Client(sys.argv[1])
    client.main(sys.argv[2])

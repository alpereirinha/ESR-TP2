import socket, threading, sys, os, time, json
from pprint import pprint
from node import Node

class Bootstrap:

    def __init__(self, host):
        
        self.host = host
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.nodes = {} #para guardar os nodos e os vizinhos existentes
        #sintaxe : {'10.0.0.10': ['10.0.1.1','10.0.1.2'])}
        

    def parseBootstrapper(self):
        
        file = json.load(open("bootstrap.json", 'r'))

        print(file)
        
        for elem in file:
            node = elem['node']
            neighbors = []
            for neighbor in elem['vizinhos']:
                neighbors.append(neighbor)
            
            self.nodes[node] = neighbors

    def sendNeighbours(self, addr):

        neighbours = ','.join(self.nodes[addr])
        self.socket.sendto(("ADDME " + neighbours).encode('utf-8'), (addr, 3000))
        self.nodes.pop(addr)
        print("NODES: " + str(self.nodes))
        if len(self.nodes) == 0:
            self.socket.sendto(("STARTFLOOD").encode('utf-8'), ('10.0.0.10', 3000)) 

    def servico_bt(self):

        self.socket.bind((self.host, 4000))

        while True:

            data, (address, port) = self.socket.recvfrom(1024)

            aux_msg = data.decode('utf-8').split(' ')
        
            if aux_msg[0] == "NEIGHBOURS":
                
                self.sendNeighbours(address)
                
            #defineRoutes(data,address)    



    def main(self):

        self.parseBootstrapper()
        threading.Thread(target=self.servico_bt, args=()).start()

if __name__ == '__main__':

    bootstrap = Bootstrap(sys.argv[1])
    bootstrap.main()
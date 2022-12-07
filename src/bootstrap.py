import socket, threading, sys, os, time, json
from pprint import pprint
from node import Node

class Bootstrap(Node):

    def __init__(self, host):
        super.__init__(host)

        self.nodes = {} #para guardar os nodos e os vizinhos existentes
        #sintaxe : {'10.0.0.10': ['10.0.1.1','10.0.1.2'])}

    def parseBootstrapper(self):
        file = json.load(open("bootstrap.json", 'r'))

        for elem in file:
            node = elem['node']
            neighbors = {}
            for neighbor in elem['vizinhos']:
                neighbors.append(neighbor)
            
            self.nodes[node] = neighbors

    def sendNeighbours(self, addr):
        neighbours = ' '.join(self.nodes[addr])
        self.socket.send(neighbours.encode('utf-8'))

    def main(self):

        threading.Thread(target=self.servico, args=()).start()

if __name__ == '__main__':

    bootstrap = Bootstrap(sys.argv[1], sys.argv[2])
    bootstrap.main()
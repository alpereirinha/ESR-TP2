import socket, threading, sys, os, time, json
from pprint import pprint
from node import Node

class Bootstrap:

    def __init__(self, host, filename):
        
        self.host = host
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.filename = filename
        self.servers = {}
        self.nodes = {} #para guardar os nodos e os vizinhos existentes
        #sintaxe : {'s1': ['r1:10.0.1.1','r2:10.0.1.2'])}

    def parseBootstrapper(self):
        
        file = json.load(open(self.filename, 'r'))

        print(file)

        for server in file["servers"]:

            self.servers[server["node"]] = server["ip"]
        
        for elem in file["overlay"]:

            node = elem['node']
            neighbors = []
            for neighbor in elem['vizinhos']:
                neighbors.append(neighbor)
            
            self.nodes[node] = neighbors

    def sendNeighbours(self, addr, name):

        neighbours = ','.join(self.nodes[name])
        self.socket.sendto(("ADDME " + ','.join(list(self.servers.keys())) + " " + neighbours).encode('utf-8'), (addr, 3000))

    def servico_bt(self):

        self.socket.bind((self.host, 4000))

        while True:

            data, (address, port) = self.socket.recvfrom(1024)

            aux_msg = data.decode('utf-8').split(' ')
        
            if aux_msg[0] == "NEIGHBOURS":
                
                self.sendNeighbours(address, aux_msg[1])

            elif aux_msg[0] == "ACK": #confirmação do nodo na rede

                self.remove_node(aux_msg[1])
                
    def remove_node(self, node):

        self.nodes.pop(node)

        if len(self.nodes) == 0:

            for server in self.servers:

                self.socket.sendto(("STARTFLOOD").encode('utf-8'), (self.servers[server], 3000)) 

    def main(self):

        self.parseBootstrapper()
        threading.Thread(target=self.servico_bt, args=()).start()

if __name__ == '__main__':

    bootstrap = Bootstrap(sys.argv[1], sys.argv[2])
    bootstrap.main()


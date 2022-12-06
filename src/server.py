from node import Node

import json
import socket
import threading

FILENAME = "movie.Mjpeg"
BOOTSTRAP = "bootstrap.json"

class Server:
    
    def __init__(self):
        self.bootstrapper = {} #para guardar os nodos e os vizinhos existentes
        #sintaxe : {'10.0.0.10': ['10.0.1.1','10.0.1.2'])}

    def startServer(self):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('10.0.0.10', 3000))
        s.listen()

        while True:

            clientSocket, address = s.accept()
            data = clientSocket.recv(1024)
            print(f"Recebi {data.decode('utf-8')}")

            threading.Thread(target=self.processMessage,args=(clientSocket,data,address)).start()

    def processMessage(self, clientSocket, data, address):

        for node in self.bootstrapper:

            if address[0] in self.bootstrapper:

                msg = ' '.join(self.bootstrapper[node])
                clientSocket.send(msg.encode('utf-8'))
        
        clientSocket.close()


        #obter caminho para o cliente que enviou a mensagem
        #para enviar mensagem de volta

    def parseBootstrapper(self):
        bootstrap = json.load(open("bootstrap.json", 'r'))

        for elem in bootstrap:
            node = elem['node']
            neighbors = {}
            for neighbor in elem['vizinhos']:
                neighbors.append(neighbor)
            
            self.bootstrapper[node] = neighbors

    def bfs(self, visited, queue, node):
        visited.append(node)
        queue.append(node)
        hops = 0

        while queue:
            s = queue.pop(0)

            for neighbour in self.bootstrapper[s]:
                if neighbour not in visited:
                    visited.append(neighbour)
                    queue.append(neighbour)
                    #criar entrada na routing table
                    #definir num_hops = hops 
                    #definir o previous node = s
            hops = hops + 1

    def flood(self):
        visited = []
        queue = []
        #bfs(visited, queue, #nodo onde começa) começa nele próprio?

    def main(self):

        threading.Thread(target=self.startServer, args=()).start()

if __name__ == '__main__':

    server = Server()
    server.main()

# python3 node.py 10.0.1.2 3001 10.0.0.10
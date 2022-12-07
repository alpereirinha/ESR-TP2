from node import Node

import json
import socket
import threading

FILENAME = "movie.Mjpeg"
BOOTSTRAP = "bootstrap.json"

class Server(Node):
    
    def __init__(self):
        super.__init__()

    def startServer(self):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('10.0.0.10', 3000))
        s.listen()

        while True:

            clientSocket, address = s.accept()
            data = clientSocket.recv(1024)
            print(f"Recebi {data.decode('utf-8')}")

            threading.Thread(target=self.processMessage,args=(clientSocket,data,address)).start()
    
    def askBootstrap(self):

        try:

            self.socket.send("NEIGHBOURS".encode('utf-8'))
            data, (address, port) = self.socket.recv(1024)

            print(f"Recebi {data.decode('utf-8')}")

            for node in data.decode('utf-8').split(" "):
                self.routing_table[node] = (node, 1, "no")

        except socket.error as m:

            print(f"não consegui criar, tá tudo lixado: {m}")

    def processMessage(self, clientSocket, data, address):

        for node in self.bootstrapper:

            if address[0] in self.bootstrapper:

                msg = ' '.join(self.bootstrapper[node])
                clientSocket.send(msg.encode('utf-8'))
        
        clientSocket.close()


        #obter caminho para o cliente que enviou a mensagem
        #para enviar mensagem de volta

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
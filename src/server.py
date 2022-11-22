from node import Node

import json
import socket
import threading

FILENAME = "movie.Mjpeg"
BOOTSTRAP = "bootstrap.json"

class Server:

#   def __init__(self):

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

        file = json.load(open('bootstrap.json', 'r'))

        for x in file:

            if address[0] in x['node']:

                msg = ' '.join(x['vizinhos'])
                clientSocket.send(msg.encode('utf-8'))
        
        clientSocket.close()


        #obter caminho para o cliente que enviou a mensagem
        #para enviar mensagem de volta

    def main(self):

        threading.Thread(target=self.startServer, args=()).start()

if __name__ == '__main__':

    server = Server()
    server.main()

# python3 node.py 10.0.1.2 3001 10.0.0.10
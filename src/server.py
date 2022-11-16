from node import Node

import socket
import threading

FILENAME = "movie.Mjpeg"

class Server(Node):
    def __init__(self, host, port):
        super().__init__(host, port)

    def main(self):
        threading.Thread(target=startServer, args=()).start()

    def startServer(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('10.0.0.10', 3000))
        s.listen()

        while True:
             clientSocket, address = s.accept()
             data = clientSocket.recv(1024)
             threading.Thread(target=self.processMessage,args=(s,clientSocket,data,address)).start()

    def processMessage(self, clientSocket, data, address):
        msg = data.decode('utf-8')
        #obter caminho para o cliente que enviou a mensagem
        #para enviar mensagem de volta

if __name__ == '__main__':
    server = Server()
    server.main()
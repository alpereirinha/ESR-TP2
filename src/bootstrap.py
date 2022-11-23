import socket, threading, sys, os, time, json
from pprint import pprint

class Bootstrap:

    def __init__(self, host, port):

        self.bootstrap = json.load(open("bootstrap.json", 'r'))
        self.host = host
        self.port = int(port)

    def getNeighbours(self, clientAddress, clientSocket):

        for elem in self.bootstrap:

            if clientAddress[0] in elem['node']:

                clientSocket.send(' '.join(elem['vizinhos']).encode('utf-8'))

    def servico(self):

        try:

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((self.host, self.port))
            s.listen()
            print(f"tou a ouvir no host {self.host} e no port {self.port}")

        except socket.error as m:

            print(f"não consegui criar, tá tudo lixado: {m}")

        while True:

            clientSocket, clientAddress = s.accept()
            print(f"aceitei o gajo com ip {clientAddress}")
            data = clientSocket.recv(1024)

            # ADDME

            if data.decode('utf-8').split(' ')[0] == "JOIN":

                self.getNeighbours(clientAddress, clientSocket)

        s.close()

    def main(self):

        threading.Thread(target=self.servico, args=()).start()

if __name__ == '__main__':

    bootstrap = Bootstrap(sys.argv[1], sys.argv[2])
    bootstrap.main()
import socket, threading, sys, os, time
from pprint import pprint

class Node:
    def __init__(self, host, port):
        self.neighbours = set()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.lock = threading.Lock()
        self.host = host
        self.port = port
        self.received = "false"

        try:
            self.socket.bind((host,port))
        except socket.error as m:
            print(f"FALHOU {host}:{port}")
            print(m)
            sys.exit()

    def askNeighbours(self, ip):
        msg = "BOOTSTRAP"
        self.socket.sendto(msg.encode('utf-8'), (ip, 3000))
        resposta, server_add = self.socket.recv(1024)
        print(f"Recebi {resposta.decode('utf-8')} do servidor {server_add}")
        lista = list(resposta.decode('utf-8').split(" "))
        self.neighbours.append(set(lista))

    def msgToNeighbours(self):
        for x in list(self.neighbours):
            msg = "ADDME " + str(self.host)
            self.socket.sendto(msg.encode('utf-8'), (x, 3000))
            print(f"Enviei para {x}")

    def getNotification(self):
        # monitor à espera de notificações

        # while !received:
        #     self.wait()

        self.socket.listen()
        # resposta, server_add = self.socket.recv(1024)
        (clientSocket, clientAddress) = self.socket.accept()
        # with self.lock:

        while(True):

            data = clientSocket.recv(1024)
            if(data != b''):

                aux_msg = data.decode('utf-8')
                if aux_msg[0] == "ADDME":
                # Send back what you received
                    self.neighbours.add(aux_msg[1])
                    clientSocket.send(data)

                    break
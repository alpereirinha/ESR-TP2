import socket, threading, sys, os, time
from pprint import pprint

class Node:

    def __init__(self, host):

        self.neighbours = set()
        self.lock = threading.Lock()
        self.host = host

    def askNeighbours(self):

        msg = "BOOTSTRAP"

        try:

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((self.host, 3000))
            self.lock.acquire()
            s.connect(('10.0.0.10', 3000))
            s.send(msg.encode('utf-8'))
            resposta = s.recv(1024)

            print(f"Recebi {resposta.decode('utf-8')}")

            # modifica os vizinhos
            lista = list(resposta.decode('utf-8').split(" "))
            self.neighbours = self.neighbours.union(set(lista))
            print(self.neighbours)
            self.lock.release()
            s.close()

        except socket.error as m:

            print(m)

    def servico(self):

        try:

            self.askNeighbours()
            self.msgToNeighbours()

        except socket.error as m:
            print(m)

# tornar esta cena tcp decente

    def msgToNeighbours(self):

        try:

            print(list(self.neighbours))
            for x in list(self.neighbours):

                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind((self.host, 3000))
                s.connect((x, 4000))
                msg = "ADDME " + str(self.host)
                s.send(msg.encode('utf-8'))
                print(f"Enviei para {x}")
                s.close()

        except socket.error as m:
            print(m)

    def getNotification(self):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, 4000))
        s.listen()
        print('tou a ouvir')
        clientSocket, clientAddress = s.accept()
        print('aceitei')

        while True:

            try:

                data = clientSocket.recv(1024)

                if data != b'':

                    aux_msg = data.decode('utf-8').split(' ')

                    if aux_msg[0] == "ADDME":

                        self.lock.acquire()
                        self.neighbours.add(aux_msg[1])
                        print("ADDME: ")
                        print(self.neighbours)
                        self.lock.release()
                    # clientSocket.send(data)

            except socket.error as m:

                print(m)
                break

    def main(self):

        threading.Thread(target=self.servico, args=()).start()
        threading.Thread(target=self.getNotification, args=()).start()

if __name__ == '__main__':
    node = Node(sys.argv[1])
    node.main()
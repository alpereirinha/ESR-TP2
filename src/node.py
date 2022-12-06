import socket, threading, sys, os, time
from pprint import pprint

class Node:

    def __init__(self, host, port):

        self.host = host
        self.port = int(port)
        self.neighbours = set() #secalhar já não precisamos disto?
        self.routing_table = {}
        #possível sintaxe do dicionário i guess:
        #dict([(('ip_destino','10.1.0.10'), ('next_hop','10.2.0.1'), ('num_hops','3'), ('active','yes')), (....)])
        self.previous_node = "" #para guardarmos o nodo de onde veio o flood e não enviarmos para ele (?)

    def askBootstrap(self):

        try:

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # s.bind((self.host, self.port))
            s.connect(('10.0.0.10', 3000)) # ip server e port

            print("espero conectar com 10.0.0.10 no port 3000")

            s.send("JOIN ".encode('utf-8'))
            res = s.recv(1024)

            print(f"recebi {res.decode('utf-8')}")

            self.neighbours = self.neighbours.union(set(res.decode('utf-8').split(" ")))

            print(f"info que tenho dos vizinhos: {self.neighbours}")

            s.close()

        except socket.error as m:

            print(f"não consegui criar, tá tudo lixado: {m}")

    def servico(self):

        while True:

            time.sleep(3)
            print(self.neighbours)

    def main(self):

        self.askBootstrap()
        threading.Thread(target=self.servico, args=()).start()

if __name__ == '__main__':

    node = Node(sys.argv[1], sys.argv[2])
    node.main()
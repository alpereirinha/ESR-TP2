import socket, threading, sys, os, time
from pprint import pprint

PORT = 3000

class Node:

    def __init__(self, host, bootstrapper):

        self.host = host
        self.bootstrapper = bootstrapper
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.routing_table = {}
        #possível sintaxe do dicionário i guess:
        #dict([(('10.1.0.10' : [('next_hop','10.2.0.1'), ('num_hops','3'), ('active','yes'))])
        self.previous_node = "" #para guardarmos o nodo de onde veio o flood e não enviarmos para ele (?)

    def askBootstrap(self):

        try:

            self.socket.send("NEIGHBOURS".encode('utf-8'))
            data, (address, port) = self.socket.recv(1024)

            print(f"Recebi {data.decode('utf-8')}")

            for node in data.decode('utf-8').split(" "):
                self.routing_table[node] = (node, float('inf'), "no")

        except socket.error as m:

            print(f"não consegui criar, tá tudo lixado: {m}")

    def listen(self):
        while True:
            data, (address, port) = self.socket.recv(1024) #probably vai ter que ser alterado

            #definir formato da data
            #if == NEIGHBOURS self.sendNeighbours(address)
            #defineRoutes(data,address)

    def servico(self):

        while True:

            time.sleep(3)
            print(self.neighbours)

    def defineRoutes(self, data, address):

        #falta receber

        str_to_send = ""
        list_to_send = []
        for neighbour in self.routing_table:
            #deve haver uma maneira melhor de fazer esta string
            neighbour_str = "key:" + neighbour + ",values:" + ' '.join(self.routing_table[neighbour])
            #enviar também o instante? para comparar os delays
            list_to_send.append(neighbour_str)
        
        str_to_send = ';'.join(list_to_send)
        self.socket.send(str_to_send.encode("utf-8"))

    def main(self):

        self.askBootstrap()
        threading.Thread(target=self.servico, args=()).start()

if __name__ == '__main__':

    node = Node(sys.argv[1], sys.argv[2])
    node.main()
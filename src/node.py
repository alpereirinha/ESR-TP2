import socket, threading, sys, os, time
from pprint import pprint

PORT = 3000

class Node:

    def __init__(self, host, bootstrapper):
        self.lock = threading.Lock()
        self.host = host
        self.bootstrapper = bootstrapper
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((host, PORT))
        self.socket2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket2.bind((host, 5000))
        self.routing_table = {}
        #possível sintaxe do dicionário i guess:
        #dict([(('10.1.0.10' : [('next_hop','10.2.0.1'), ('num_hops','3'), ('active','yes'))])
        #self.previous_node = "" #para guardarmos o nodo de onde veio o flood e não enviarmos para ele (?)
        #self.flooded = 0
        #self.neighbours = set()
        #self.ativos = set()

    def listen(self):

        while True:

            data, (address, port) = self.socket.recvfrom(1024) #probably vai ter que ser alterado

            aux_msg = data.decode('utf-8').split(' ')

            print(aux_msg)

            if aux_msg[0] == "ADDME": #recebe a lista de vizinhos a adicionar

                self.addNeighbours(aux_msg[1])

            elif aux_msg[0] == "FLOOD": #mensagem de flood (começa no servidor)

                self.handleFlood(address, int(aux_msg[1]), aux_msg[2:], int(time.time() * 1000), port)
            
            elif aux_msg[0] == "STARTFLOOD": #começar construção do overlay (a partir do servidor)
                
                vizinhos = [x for x in self.routing_table if self.routing_table[x][1] == 1]
                print ("VIZINHOS: " + str(vizinhos))

                str_to_send = ""
                list_to_send = []
                for neighbour in vizinhos:
                    neighbour_str = neighbour + ":" + ','.join(map(str, self.routing_table[neighbour]))
                    list_to_send.append(neighbour_str)

                str_to_send = ' '.join(list_to_send)
                for x in vizinhos:
                    print("entrei" + str(x))
                    print("port" + str(port))
                    self.socket.sendto(("FLOOD " + str(int(time.time() * 1000)) + " " + str_to_send).encode("utf-8"),(x, PORT))

                    #self.socket.sendto(("FLOOD 0 " + str(int(time.time() * 1000)) + " 0 " + self.host).encode('utf-8') ,(x, PORT))

            elif aux_msg[0] == "STARTSTREAMING": #recebe mensagem de um router para começar a stream
                
                self.start_stream(address, PORT)

            elif aux_msg[0] == "STOPSTREAMING": #pedido para se desconectar

                self.stop_stream(address, PORT)

            print(f"\n\nTABELA : {self.routing_table}")
            #print(f"VIZINHOS: {self.neighbours}")
            #print(f"ATIVOS: {self.ativos}")

    def listenRTP(self):

        while True:

            data, (address, port) = self.socket2.recvfrom(20480) #probably vai ter que ser alterado

            self.handle_stream(data)

    def handle_stream(self, data):

        for n in [x for x in self.routing_table if self.routing_table[x][3] == "yes"]:
            
            self.socket.sendto(data, (n, 5000))

    def addNeighbours(self, msg):

        for x in msg.split(","):

            self.lock.acquire()
            self.routing_table[x] = (x, 1, -1, 'no')
            self.lock.release()

    def handleFlood(self, address, instant, table, my_instant, port):

        changed = 0

        entries = table
        print(entries)

        for entry in entries:
            splited = entry.split(":")
            key = splited[0]
            values = splited[1].split(',')
            print("VALUES: " + str(values))
            tempo = my_instant-instant + int(values[2]) #float?
            if (key in self.routing_table): #entrada já existe na minha tabela

                if (self.routing_table[key][2] != -1): #entrada já foi preenchida com algum valor previamente

                    if((self.routing_table[key][2] > tempo) #valor que recebo para um certo destino é menor
                    or (self.routing_table[key][2] == tempo and int(values[1]) + 1 < self.routing_table[key][1])):
                    #valor que recebo é igual ao que já tenho mas tem menor número de saltos
                        self.routing_table[key] = (address, int(values[1]) + 1, tempo, self.routing_table[key][3])
                        changed = 1

                else: #entrada existe mas ainda não foi ainda preenchida com tempo (caso dos vizinhos)
                    self.routing_table[key] = (self.routing_table[key][0], self.routing_table[key][1], tempo, self.routing_table[key][3]) #altera o tempo (em ms) para lá chegar
                    changed = 1

            else: #entrada não existe
                self.routing_table[key] = (address, int(values[1]) + 1, tempo, 'no')
                changed = 1

            if (changed): #só continuo o flood se a minha tabela tiver alterado
                vizinhos = [x for x in self.routing_table if self.routing_table[x][1] == 1]

                str_to_send = ""
                list_to_send = []
                for neighbour in self.routing_table:
                    neighbour_str = neighbour + ":" + ','.join(map(str, self.routing_table[neighbour]))
                    list_to_send.append(neighbour_str)

                str_to_send = ' '.join(list_to_send)
                for x in vizinhos:
                    self.socket.sendto(("FLOOD " + str(int(time.time() * 1000)) + " " + str_to_send).encode("utf-8"),(x,port))
                #FLOOD instant neighbour1:value1,value2,value3 neighbour:value1,value2,value3


    def start_stream(self, address, port):

        self.routing_table[address] = (self.routing_table[address][0], self.routing_table[address][1], self.routing_table[address][2], "yes")

        if 1 == len([x for x in self.routing_table if self.routing_table[x][3] == "yes"]):

            self.socket.sendto(("STARTSTREAMING").encode('utf-8') ,(self.routing_table["10.0.0.10"][0], PORT))

    def stop_stream(self, address, port):

        self.routing_table[address] = (self.routing_table[address][0], self.routing_table[address][1], self.routing_table[address][2], "no")
        
        if not len([x for x in self.routing_table if self.routing_table[x][3] == "yes"]):

            self.socket.sendto(("STOPSTREAMING").encode('utf-8') ,(self.routing_table["10.0.0.10"][0], PORT))

    def servico(self):

        while True:

            time.sleep(3)
            print(self.routing_table)


    def main(self):

        threading.Thread(target=self.listen, args=()).start()
        threading.Thread(target=self.listenRTP, args=()).start()
        self.socket.sendto("NEIGHBOURS".encode('utf-8'), (self.bootstrapper, 4000))
        
        #threading.Thread(target=self.servico, args=()).start()

if __name__ == '__main__':

    node = Node(sys.argv[1], sys.argv[2])
    node.main()


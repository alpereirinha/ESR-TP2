import socket, threading, sys, os, time
from pprint import pprint

PORT = 3000

class Node:

    def __init__(self, host, bootstrapper):
        self.lock = threading.Lock()
        self.host = host
        self.bootstrapper = bootstrapper
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("", PORT))
        self.socket2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket2.bind(("", 5000))
        self.routing_table = {}
        self.ips = {}
        self.keys = {}
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

            #print(aux_msg)

            if aux_msg[0] == "ADDME": #recebe a lista de vizinhos a adicionar

                self.addNeighbours(aux_msg[1])

            elif aux_msg[0] == "FLOOD": #mensagem de flood (começa no servidor)

                self.handleFlood(address, int(aux_msg[1]), aux_msg[2:], int(time.time() * 1000), port)
            
            elif aux_msg[0] == "STARTFLOOD": #começar construção do overlay (a partir do servidor)

                self.startFlood()

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
            
            self.socket.sendto(data, (self.ips[n], 5000))

    def addNeighbours(self, msg):

        for x in msg.split(","):
            info = x.split(":")

            self.lock.acquire()
            self.routing_table[info[0]] = (info[1], 1, -1, 'no')
            self.ips[info[0]] = info[1]
            self.keys[info[1]] = info[0]
            self.lock.release()
        self.routing_table[self.host] = (self.host, 0, 0, 'no')

    def handleFlood(self, address, instant, table, my_instant, port):

        changed = 0

        print(table)
        #print("RECEIVED:" + address)
        #print("DIFERENCA:" + str(my_instant-instant))

        if (self.routing_table[self.keys[address]][2] == -1 or 
        self.routing_table[self.keys[address]][2] > my_instant-instant):
            self.routing_table[self.keys[address]] = (address, 1, my_instant-instant, self.routing_table[self.keys[address]][3])
            changed = 1

        for entry in table:
            splited = entry.split(":")
            key = splited[0]
            values = splited[1].split(',')
            #print("VALUES: " + str(values))
            tempo = my_instant-instant + int(values[2])
            if (key in self.routing_table): #entrada já existe na minha tabela
                if(int(values[2]) != -1): #se o vizinho que me enviou já sabe o tempo
                    if(key != self.host): #entrada não é referente a mim
                        if (key in self.ips and self.ips[key] == address): #entrada é do vizinho da qual estou a receber
                            if(self.routing_table[key][2] == -1 or self.routing_table[key][2] > my_instant-instant):
                                self.routing_table[key] = (self.ips[key], 1, my_instant-instant, 'no')

                        else: #entrada NÃO é do vizinho que estou a receber
                            if (self.routing_table[key][2] != -1): #entrada já foi preenchida com algum valor previamente

                                if((self.routing_table[key][2] > tempo) #valor que recebo para um certo destino é menor
                                or (self.routing_table[key][2] == tempo and int(values[1]) + 1 < self.routing_table[key][1])):
                                #valor que recebo é igual ao que já tenho mas tem menor número de saltos
                                    self.routing_table[key] = (address, int(values[1]) + 1, tempo, self.routing_table[key][3])
                                    changed = 1

                            else: #entrada existe mas ainda não foi ainda preenchida com tempo (caso dos vizinhos)
                                if (self.ips[key] != address): #quem está a preencher não é o vizinho
                                    self.routing_table[key] = (address, int(values[1]) + 1, tempo, self.routing_table[key][3]) #altera o tempo (em ms) para lá chegar
                                    changed = 1
                                else:
                                    self.routing_table[address] = (address, 1, my_instant-instant, 'no')
                                    changed = 1

            else: #entrada não existe
                if(int(values[2]) != -1): #se o vizinho que me enviou já sabe o tempo
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
                    self.socket.sendto(("FLOOD " + str(int(time.time() * 1000)) + " " + str_to_send).encode("utf-8"),(self.ips[x],port))
                #FLOOD instant neighbour1:value1,value2,value3 neighbour:value1,value2,value3
    
    def startFlood(self):
        vizinhos = [x for x in self.routing_table if self.routing_table[x][1] == 1]
        print ("VIZINHOS: " + str(vizinhos))

        str_to_send = ""
        list_to_send = []
        for neighbour in vizinhos:
            neighbour_str = neighbour + ":" + ','.join(map(str, self.routing_table[neighbour]))
            list_to_send.append(neighbour_str)

        str_to_send = ' '.join(list_to_send)
        for x in vizinhos:
            self.socket.sendto(("FLOOD " + str(int(time.time() * 1000)) + " " + str_to_send).encode("utf-8"),(self.ips[x], PORT))

    def start_stream(self, address, port):

        self.routing_table[address] = (self.routing_table[address][0], self.routing_table[address][1], self.routing_table[address][2], "yes")

        if 1 == len([x for x in self.routing_table if self.routing_table[x][3] == "yes"]):

            self.socket.sendto(("STARTSTREAMING").encode('utf-8') ,(self.routing_table["10.0.0.10"][0], PORT))

    def stop_stream(self, address, port):

        self.routing_table[address] = (self.routing_table[address][0], self.routing_table[address][1], self.routing_table[address][2], "no")
        
        if not len([x for x in self.routing_table if self.routing_table[x][3] == "yes"]):

            self.socket.sendto(("STOPSTREAMING").encode('utf-8') ,(self.routing_table["s1"][0], PORT))

    def servico(self):

        while True:

            time.sleep(3)
            print(self.routing_table)


    def main(self):

        threading.Thread(target=self.listen, args=()).start()
        threading.Thread(target=self.listenRTP, args=()).start()
        self.socket.sendto(("NEIGHBOURS " + str(self.host)).encode('utf-8'), (self.bootstrapper, 4000))
        
        #threading.Thread(target=self.servico, args=()).start()

if __name__ == '__main__':

    node = Node(sys.argv[1], sys.argv[2])
    node.main()


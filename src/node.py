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
        self.aux_routing_table = {}
        self.ips = {}
        self.keys = {}
        self.flood_nr = 0
        #possível sintaxe do dicionário i guess:
        #dict([(('10.1.0.10' : [('next_hop','10.2.0.1'), ('num_hops','3'), ('active','yes'))])
        #self.previous_node = "" #para guardarmos o nodo de onde veio o flood e não enviarmos para ele (?)
        #self.flooded = 0
        self.neighbours = {}
        #self.ativos = set()

    def listen(self):

        while True:

            data, (address, port) = self.socket.recvfrom(1024) #probably vai ter que ser alterado

            aux_msg = data.decode('utf-8').split(' ')

            #print(aux_msg)

            if aux_msg[0] == "ADDME": #recebe a lista de vizinhos a adicionar

                self.addNeighbours(aux_msg[1])

            elif aux_msg[0] == "FLOOD": #mensagem de flood (começa no servidor)

                self.handleFlood(address, int(aux_msg[1]), int(aux_msg[2]), aux_msg[3:], int(time.time() * 1000), port)
            
            elif aux_msg[0] == "STARTFLOOD": #começar construção do overlay (a partir do servidor)

                self.startFlood()
                #print("acabei flood")
                time.sleep(30)
                #print("vou começar novo flood")
                self.startFlood()

                #FALTA IMPLEMENTAR OS FLOODS PERIODICOS DIREITOS

            elif aux_msg[0] == "STARTSTREAMING": #recebe mensagem de um router para começar a stream
                
                self.start_stream(address, PORT)

            elif aux_msg[0] == "STOPSTREAMING": #pedido para se desconectar

                self.stop_stream(address, PORT)

            print(f"\n\nTABELA : {self.aux_routing_table}")
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
            self.aux_routing_table[info[0]] = (info[1], 1, -1, 'no')
            self.ips[info[0]] = info[1]
            self.keys[info[1]] = info[0]
            #self.neighbours.add(info[0])
            self.lock.release()
        self.aux_routing_table[self.host] = (self.host, 0, 0, 'no')
        self.neighbours = dict(self.aux_routing_table)

    def handleFlood(self, address, instant, flood, table, my_instant, port):

        changed = 0

        if(self.flood_nr != flood): 
            self.flood_nr = flood
            if(self.flood_nr > 1):
                self.aux_routing_table.clear()
                self.aux_routing_table = dict(self.neighbours)

        #print(table)
        #print("RECEIVED:" + address)
        #print("my instant: " + str(my_instant))
        #print("instant: " + str(instant))
        #print("DIFERENCA:" + str(my_instant-instant))

        if (self.aux_routing_table[self.keys[address]][2] == -1 or 
        self.aux_routing_table[self.keys[address]][2] > my_instant-instant):
            self.aux_routing_table[self.keys[address]] = (address, 1, my_instant-instant, self.aux_routing_table[self.keys[address]][3])
            changed = 1

        for entry in table:
            splited = entry.split(":")
            key = splited[0]
            values = splited[1].split(',')
            #print("VALUES: " + str(values))
            tempo = my_instant-instant + int(values[2])
            if (key in self.aux_routing_table): #entrada já existe na minha tabela
                if(int(values[2]) != -1): #se o vizinho que me enviou já sabe o tempo
                    if(key != self.host): #entrada não é referente a mim
                        if (key in self.ips and self.ips[key] == address): #entrada é do vizinho da qual estou a receber
                            if(self.aux_routing_table[key][2] == -1 or self.aux_routing_table[key][2] > my_instant-instant):
                                self.aux_routing_table[key] = (self.ips[key], 1, my_instant-instant, 'no')

                        else: #entrada NÃO é do vizinho que estou a receber
                            if (self.aux_routing_table[key][2] != -1): #entrada já foi preenchida com algum valor previamente

                                if((self.aux_routing_table[key][2] > tempo) #valor que recebo para um certo destino é menor
                                or (self.aux_routing_table[key][2] == tempo and int(values[1]) + 1 < self.aux_routing_table[key][1])):
                                #valor que recebo é igual ao que já tenho mas tem menor número de saltos
                                    self.aux_routing_table[key] = (address, int(values[1]) + 1, tempo, self.aux_routing_table[key][3])
                                    changed = 1

                            else: #entrada existe mas ainda não foi ainda preenchida com tempo (caso dos vizinhos)
                                if (self.ips[key] != address): #quem está a preencher não é o vizinho
                                    self.aux_routing_table[key] = (address, int(values[1]) + 1, tempo, self.aux_routing_table[key][3]) #altera o tempo (em ms) para lá chegar
                                    changed = 1
                                else:
                                    self.aux_routing_table[address] = (address, 1, my_instant-instant, 'no')
                                    changed = 1

            else: #entrada não existe
                if(int(values[2]) != -1): #se o vizinho que me enviou já sabe o tempo
                    self.aux_routing_table[key] = (address, int(values[1]) + 1, tempo, 'no')
                    changed = 1

        if (changed): #só continuo o flood se a minha tabela tiver alterado
            vizinhos = [x for x in self.aux_routing_table if self.aux_routing_table[x][1] == 1]

            str_to_send = ""
            list_to_send = []
            for neighbour in self.aux_routing_table:
                neighbour_str = neighbour + ":" + ','.join(map(str, self.aux_routing_table[neighbour]))
                list_to_send.append(neighbour_str)

                str_to_send = ' '.join(list_to_send)
                for x in vizinhos:
                    self.socket.sendto(("FLOOD " + str(int(time.time() * 1000)) + " " + str(self.flood_nr) + " " + str_to_send).encode("utf-8"),(self.ips[x],port))
                #FLOOD instant neighbour1:value1,value2,value3 neighbour:value1,value2,value3

        else: #se já não mudou posso passar a auxiliar para principal
            #print("PAREI DE MUDAR")
            self.routing_table = dict(self.aux_routing_table)
            print(f"\n\nNOVA TABELA : {self.routing_table}")
    
    def startFlood(self):
        self.flood_nr += 1
        if (self.flood_nr > 1):
            self.aux_routing_table.clear()
            self.aux_routing_table = dict(self.neighbours)

        vizinhos = [x for x in self.neighbours if x != self.host] #if self.aux_routing_table[x][1] == 1]
        print ("VIZINHOS: " + str(vizinhos))

        str_to_send = ""
        list_to_send = []
        for neighbour in vizinhos:
            neighbour_str = neighbour + ":" + ','.join(map(str, self.aux_routing_table[neighbour]))
            list_to_send.append(neighbour_str)

        str_to_send = ' '.join(list_to_send)

        for x in vizinhos:
            self.socket.sendto(("FLOOD " + str(int(time.time() * 1000)) + " " + str(self.flood_nr) + " " + str_to_send).encode("utf-8"),(self.ips[x], PORT))

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

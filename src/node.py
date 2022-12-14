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
        self.routing_tables = {}
        self.aux_routing_tables = {}
        self.server = "s1"
        self.latency_tolerance = 100
        self.ips = {}
        self.keys = {}
        self.flood_nr = 0
        self.neighbours = {}
        self.check = False
        #possível sintaxe do dicionário i guess:
        #dict([(('10.1.0.10' : [('next_hop','10.2.0.1'), ('num_hops','3'), ('active','yes'))])
        #self.previous_node = "" #para guardarmos o nodo de onde veio o flood e não enviarmos para ele (?)
        #self.flooded = 0
        #self.ativos = set()

    def listen(self):

        while True:

            data, (address, port) = self.socket.recvfrom(1024) #probably vai ter que ser alterado

            aux_msg = data.decode('utf-8').split(' ')

            # print(aux_msg)

            if aux_msg[0] == "ADDME": #recebe a lista de vizinhos a adicionar

                self.addNeighbours(aux_msg[1], aux_msg[2])

            elif aux_msg[0] == "FLOOD": #mensagem de flood (começa no servidor)
                self.handleFlood(aux_msg[1], address, int(aux_msg[2]), int(aux_msg[3]), aux_msg[4:], int(time.time() * 1000), port)
            
            elif aux_msg[0] == "STARTFLOOD": #começar construção do overlay (a partir do servidor)

                threading.Thread(target=self.period_flood, args=()).start()

            elif aux_msg[0] == "STARTSTREAMING": #recebe mensagem de um router para começar a stream
                print(f"Pedido do {aux_msg[1]} para começar a realizar streaming")
                self.start_stream(self.keys[address], aux_msg[1], PORT)

            elif aux_msg[0] == "STOPSTREAMING": #pedido para se desconectar

                print(f"Pedido do {aux_msg[1]} para parar de realizar streaming")
                self.stop_stream(self.keys[address], aux_msg[1], PORT)

            # print(f"\n\nTABELA : {self.routing_tables[self.server]}")
            # print(f"\n\nTABELA : {self.aux_routing_tables[self.server]}")
            #print(f"VIZINHOS: {self.neighbours}")
            #print(f"ATIVOS: {self.ativos}")

    def listenRTP(self):

        while True:

            data, (address, port) = self.socket2.recvfrom(20480) #probably vai ter que ser alterado
            self.handle_stream(data)

    def handle_stream(self, data):

        for n in set([self.routing_tables[self.server][x][0] for x in self.routing_tables[self.server] if self.routing_tables[self.server][x][3] == "yes"]):
            
            # print(f"tou streamar para {n}")
            self.socket.sendto(data, (n, 5000))

    def addNeighbours(self, servers, msg):

        for server in servers.split(","):

            self.routing_tables[server] = {}
            self.aux_routing_tables[server] = {}

            for x in msg.split(","):
                info = x.split(":")

                self.lock.acquire()
                self.aux_routing_tables[server][info[0]] = (info[1], 1, -1, 'no')
                self.ips[info[0]] = info[1]
                self.keys[info[1]] = info[0]
                #self.neighbours.add(info[0])
                self.lock.release()
            self.neighbours = dict(self.aux_routing_tables[server])
            self.aux_routing_tables[server][self.host] = (self.host, 0, 0, 'no')

        self.socket.sendto(("ACK " + self.host).encode('utf-8'), (self.bootstrapper, 4000))

        print(self.keys)
        print(self.ips)
        # threading.Thread(target=self.check_server, args=()).start()

    def period_flood(self):

        while True:

            self.startFlood()
            time.sleep(20)

    def handleFlood(self, server, address, instant, flood, table, my_instant, port):

        changed = 0

        if(self.flood_nr != flood): 
            self.flood_nr = flood
            if(self.flood_nr > 1):
                self.aux_routing_tables[server].clear()
                self.aux_routing_tables[server] = dict(self.neighbours)

        #print(table)
        #print("RECEIVED:" + address)
        #print("my instant: " + str(my_instant))
        #print("instant: " + str(instant))
        #print("DIFERENCA:" + str(my_instant-instant))
        # print(f"KEYS: {self.keys}")
        # print(f"KEYS: {self.ips}")
        # print(f"KEYS: {self.keys[address]}")

        if (self.aux_routing_tables[server][self.keys[address]][2] == -1 or 
        self.aux_routing_tables[server][self.keys[address]][2] > my_instant-instant):
            self.aux_routing_tables[server][self.keys[address]] = (address, 1, my_instant-instant, self.aux_routing_tables[server][self.keys[address]][3])
            changed = 1

        for entry in table:
            splited = entry.split(":")
            key = splited[0]
            values = splited[1].split(',')
            #print("VALUES: " + str(values))
            tempo = my_instant-instant + int(values[2])
            if (key in self.aux_routing_tables[server]): #entrada já existe na minha tabela
                if(int(values[2]) != -1): #se o vizinho que me enviou já sabe o tempo
                    if(key != self.host): #entrada não é referente a mim
                        if (key in self.ips and self.ips[key] == address): #entrada é do vizinho da qual estou a receber
                            if(self.aux_routing_tables[server][key][2] == -1 or self.aux_routing_tables[server][key][2] > my_instant-instant):
                                self.aux_routing_tables[server][key] = (self.ips[key], 1, my_instant-instant, 'no')

                        else: #entrada NÃO é do vizinho que estou a receber
                            if (self.aux_routing_tables[server][key][2] != -1): #entrada já foi preenchida com algum valor previamente

                                if((self.aux_routing_tables[server][key][2] > tempo) #valor que recebo para um certo destino é menor
                                or (self.aux_routing_tables[server][key][2] == tempo and int(values[1]) + 1 < self.aux_routing_tables[server][key][1])):
                                #valor que recebo é igual ao que já tenho mas tem menor número de saltos
                                    self.aux_routing_tables[server][key] = (address, int(values[1]) + 1, tempo, self.aux_routing_tables[server][key][3])
                                    changed = 1

                            else: #entrada existe mas ainda não foi ainda preenchida com tempo (caso dos vizinhos)
                                if (self.ips[key] != address): #quem está a preencher não é o vizinho
                                    self.aux_routing_tables[server][key] = (address, int(values[1]) + 1, tempo, self.aux_routing_tables[server][key][3]) #altera o tempo (em ms) para lá chegar
                                    changed = 1
                                else:
                                    self.aux_routing_tables[server][address] = (address, 1, my_instant-instant, 'no')
                                    changed = 1

            else: #entrada não existe
                if(int(values[2]) != -1): #se o vizinho que me enviou já sabe o tempo
                    self.aux_routing_tables[server][key] = (address, int(values[1]) + 1, tempo, 'no')
                    changed = 1

        if (changed): #só continuo o flood se a minha tabela tiver alterado
            vizinhos = [x for x in self.aux_routing_tables[server] if self.aux_routing_tables[server][x][1] == 1]

            str_to_send = ""
            list_to_send = []

            for neighbour in self.aux_routing_tables[server]:
                neighbour_str = neighbour + ":" + ','.join(map(str, self.aux_routing_tables[server][neighbour]))
                list_to_send.append(neighbour_str)

                str_to_send = ' '.join(list_to_send)
                for x in vizinhos:
                    self.socket.sendto(("FLOOD " + server + " " + str(int(time.time() * 1000)) + " " + str(self.flood_nr) + " " + str_to_send).encode("utf-8"),(self.ips[x],port))
                #FLOOD instant neighbour1:value1,value2,value3 neighbour:value1,value2,value3

        else: #se já não mudou posso passar a auxiliar para principal
            #print("PAREI DE MUDAR")
                if self.flood_nr > 1 and len(self.routing_tables[server]) == len(self.aux_routing_tables[server]):

                    with self.lock:
                        for entry in self.aux_routing_tables[server]:

                            self.aux_routing_tables[server][entry] = (self.aux_routing_tables[server][entry][0], self.aux_routing_tables[server][entry][1], self.aux_routing_tables[server][entry][2], self.routing_tables[server][entry][3])

                        router_extr = [x for x in self.neighbours if x[0] == "p"]

                        # print(router_extr)

                        if not self.check and self.host[0] == "r" and len(router_extr):
                            
                            print("-> Começou a thread com check_server")
                            threading.Thread(target=self.check_server, args=()).start()
                            self.check = True

                        # print(f"\n\nTABELA : {self.routing_tables}")
                        # print(f"\n\nTABELA AUX : {self.aux_routing_tables}")
                        self.routing_tables[server] = dict(self.aux_routing_tables[server])

                elif self.flood_nr == 1:

                    with self.lock:

                        self.routing_tables[server] = dict(self.aux_routing_tables[server])

            # print(f"\n\nNOVA TABELA : {self.routing_table}")
    
    def check_server(self):

        while True:

            with self.lock:
                
                streaming = [x for x in self.routing_tables[self.server] if x[0] == "p" and self.routing_tables[self.server][x][3] == "yes"]

                print(f"melhor latência do servidor atual: {self.routing_tables[self.server][self.server][2]}ms")
                print(f"threshold: {self.latency_tolerance}\n")

                if len(streaming) and self.routing_tables[self.server][self.server][2] > self.latency_tolerance:

                    new_server = "s" + str((int(self.server[1]) % len(self.routing_tables)) + 1)

                    for entry in [x for x in self.routing_tables[self.server] if self.routing_tables[self.server][x][3] == "yes"]:

                        self.routing_tables[new_server][entry] = (self.routing_tables[new_server][entry][0], self.routing_tables[new_server][entry][1], self.routing_tables[new_server][entry][2], "yes")

                        self.routing_tables[self.server][entry] = (self.routing_tables[self.server][entry][0], self.routing_tables[self.server][entry][1], self.routing_tables[self.server][entry][2], "no")

                    print(self.routing_tables[self.server][self.server][0])
                    self.socket.sendto(("STOPSTREAMING " + streaming[0]).encode('utf-8') ,(self.routing_tables[self.server][self.server][0], PORT))
                    self.socket.sendto(("STARTSTREAMING " + streaming[0]).encode('utf-8') ,(self.routing_tables[new_server][new_server][0], PORT))
                    self.server = new_server

            print(f"eu {self.host} -> uso o servidor: {self.server}\n")
            time.sleep(10)

    def startFlood(self):
        pass

    def start_stream(self, address, pc, port):

        # self.routing_tables[self.server][address] = (self.routing_tables[self.server][address][0], self.routing_tables[self.server][address][1], self.routing_tables[self.server][address][2], "yes")
        self.routing_tables[self.server][pc] = (self.routing_tables[self.server][pc][0], self.routing_tables[self.server][pc][1], self.routing_tables[self.server][pc][2], "yes")

        self.socket.sendto(("STARTSTREAMING " + pc).encode('utf-8') ,(self.routing_tables[self.server][self.server][0], PORT))



    def stop_stream(self, address, pc, port):

        # self.routing_tables[self.server][address] = (self.routing_tables[self.server][address][0], self.routing_tables[self.server][address][1], self.routing_tables[self.server][address][2], "no")
        self.routing_tables[self.server][pc] = (self.routing_tables[self.server][pc][0], self.routing_tables[self.server][pc][1], self.routing_tables[self.server][pc][2], "no")
        
        self.socket.sendto(("STOPSTREAMING " + pc).encode('utf-8') ,(self.routing_tables[self.server][self.server][0], PORT))

    def servico(self):

        while True:

            print(f"\n\nTABELA : {self.routing_tables}")
            time.sleep(10)

    def main(self):

        threading.Thread(target=self.listen, args=()).start()
        threading.Thread(target=self.listenRTP, args=()).start()
        # threading.Thread(target=self.check_server, args=()).start()
        # threading.Thread(target=self.servico, args=()).start()
        self.socket.sendto(("NEIGHBOURS " + str(self.host)).encode('utf-8'), (self.bootstrapper, 4000))
        
        # threading.Thread(target=self.servico, args=()).start()

if __name__ == '__main__':

    node = Node(sys.argv[1], sys.argv[2])
    node.main()

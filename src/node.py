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
        #possível sintaxe do dicionário i guess:
        #dict([(('10.1.0.10' : [('next_hop','10.2.0.1'), ('num_hops','3'), ('active','yes'))])
        #self.previous_node = "" #para guardarmos o nodo de onde veio o flood e não enviarmos para ele (?)
        #self.flooded = 0
        #self.ativos = set()

    def listen(self):

        while True:

            data, (address, port) = self.socket.recvfrom(1024) #probably vai ter que ser alterado

            aux_msg = data.decode('utf-8').split(' ')

            print(aux_msg)

            if aux_msg[0] == "ADDME": #recebe a lista de vizinhos a adicionar

                self.addNeighbours(aux_msg[1], aux_msg[2])

            elif aux_msg[0] == "FLOOD": #mensagem de flood (começa no servidor)

                self.handleFlood(aux_msg[1], address, int(aux_msg[2]), int(aux_msg[3]), aux_msg[4:], int(time.time() * 1000), port)
            
            elif aux_msg[0] == "STARTFLOOD": #começar construção do overlay (a partir do servidor)

                self.startFlood()
                # threading.Thread(target=self.period_flood, args=()).start()

                #FALTA IMPLEMENTAR OS FLOODS PERIODICOS DIREITOS

            elif aux_msg[0] == "STARTSTREAMING": #recebe mensagem de um router para começar a stream
                
                self.start_stream(self.keys[address], PORT)

            elif aux_msg[0] == "STOPSTREAMING": #pedido para se desconectar

                self.stop_stream(self.keys[address], PORT)

            # print(f"\n\nTABELA : {self.routing_tables[self.server]}")
            # print(f"\n\nTABELA : {self.aux_routing_tables[self.server]}")
            #print(f"VIZINHOS: {self.neighbours}")
            #print(f"ATIVOS: {self.ativos}")

    def listenRTP(self):

        while True:

            data, (address, port) = self.socket2.recvfrom(20480) #probably vai ter que ser alterado
            self.handle_stream(data)

    def handle_stream(self, data):

        for n in [x for x in self.routing_tables[self.server] if self.routing_tables[self.server][x][3] == "yes"]:
            
            print(f"tou streamar para {n}")
            self.socket.sendto(data, (self.ips[n], 5000))

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
            self.aux_routing_tables[server][self.host] = (self.host, 0, 0, 'no')
            self.neighbours = dict(self.aux_routing_tables[server])

        threading.Thread(target=self.check_server, args=()).start()

    def period_flood(self):

        while True:

            self.startFlood()
            time.sleep(30)

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
            self.routing_tables[server] = dict(self.aux_routing_tables[server])
            # print(f"\n\nNOVA TABELA : {self.routing_table}")
    
    def check_server(self):

        # while True:

            # if self.routing_tables[self.server][self.server][1] > self.latency_tolerance:

            #     self.socket.sendto(("STOPSTREAMING").encode('utf-8') ,(self.routing_tables[self.server][self.server][0], PORT))
            #     self.server = "s" + str((int(self.server[1]) % len(self.routing_tables)) + 1)
            #     print(f"mudei para o server: {self.server}")
            #     self.socket.sendto(("STARTSTREAMING").encode('utf-8') ,(self.routing_tables[self.server][self.server][0], PORT))

            # time.sleep(3)

            # apenas para teste
        time.sleep(15)

        if self.host == "r3":

            new_server = "s" + str((int(self.server[1]) % len(self.routing_tables)) + 1)
            for entry in [x for x in self.routing_tables[self.server] if self.routing_tables[self.server][x][3] == "yes"]:

                self.routing_tables[new_server][entry] = (self.routing_tables[new_server][entry][0], self.routing_tables[new_server][entry][1], self.routing_tables[new_server][entry][2], "yes")
                self.routing_tables[self.server][entry] = (self.routing_tables[self.server][entry][0], self.routing_tables[self.server][entry][1], self.routing_tables[self.server][entry][2], "no")
                print(f"\n\n{self.routing_tables}")

            self.socket.sendto(("STOPSTREAMING").encode('utf-8') ,(self.routing_tables[self.server][self.server][0], PORT))
            self.socket.sendto(("STARTSTREAMING").encode('utf-8') ,(self.routing_tables[new_server][new_server][0], PORT))
            self.server = new_server
            print(f"eu {self.host} -> mudei para o server: {self.server}")

        time.sleep(15)

        if self.host == "r2":

            new_server = "s" + str((int(self.server[1]) % len(self.routing_tables)) + 1)
            for entry in [x for x in self.routing_tables[self.server] if self.routing_tables[self.server][x][3] == "yes"]:

                self.routing_tables[new_server][entry] = (self.routing_tables[new_server][entry][0], self.routing_tables[new_server][entry][1], self.routing_tables[new_server][entry][2], "yes")
                self.routing_tables[self.server][entry] = (self.routing_tables[self.server][entry][0], self.routing_tables[self.server][entry][1], self.routing_tables[self.server][entry][2], "no")
                print(f"\n\n{self.routing_tables}")

            self.socket.sendto(("STOPSTREAMING").encode('utf-8') ,(self.routing_tables[self.server][self.server][0], PORT))
            self.socket.sendto(("STARTSTREAMING").encode('utf-8') ,(self.routing_tables[new_server][new_server][0], PORT))
            self.server = new_server
            print(f"eu {self.host} -> mudei para o server: {self.server}")
        
        time.sleep(15)

        if self.host == "r3":

            new_server = "s" + str((int(self.server[1]) % len(self.routing_tables)) + 1)
            for entry in [x for x in self.routing_tables[self.server] if self.routing_tables[self.server][x][3] == "yes"]:

                self.routing_tables[new_server][entry] = (self.routing_tables[new_server][entry][0], self.routing_tables[new_server][entry][1], self.routing_tables[new_server][entry][2], "yes")
                self.routing_tables[self.server][entry] = (self.routing_tables[self.server][entry][0], self.routing_tables[self.server][entry][1], self.routing_tables[self.server][entry][2], "no")
                print(f"\n\n{self.routing_tables}")

            self.socket.sendto(("STOPSTREAMING").encode('utf-8') ,(self.routing_tables[self.server][self.server][0], PORT))
            self.socket.sendto(("STARTSTREAMING").encode('utf-8') ,(self.routing_tables[new_server][new_server][0], PORT))
            self.server = new_server
            print(f"eu {self.host} -> mudei para o server: {self.server}")


    def startFlood(self):
        pass

    def start_stream(self, address, port):

        self.routing_tables[self.server][address] = (self.routing_tables[self.server][address][0], self.routing_tables[self.server][address][1], self.routing_tables[self.server][address][2], "yes")

        if 1 == len([x for x in self.routing_tables[self.server] if self.routing_tables[self.server][x][3] == "yes"]):

            self.socket.sendto(("STARTSTREAMING").encode('utf-8') ,(self.routing_tables[self.server][self.server][0], PORT))



    def stop_stream(self, address, port):

        self.routing_tables[self.server][address] = (self.routing_tables[self.server][address][0], self.routing_tables[self.server][address][1], self.routing_tables[self.server][address][2], "no")
        
        if not len([x for x in self.routing_tables[self.server] if self.routing_tables[self.server][x][3] == "yes"]):

            self.socket.sendto(("STOPSTREAMING").encode('utf-8') ,(self.routing_tables[self.server][self.server][0], PORT))



    def main(self):

        threading.Thread(target=self.listen, args=()).start()
        threading.Thread(target=self.listenRTP, args=()).start()
        self.socket.sendto(("NEIGHBOURS " + str(self.host)).encode('utf-8'), (self.bootstrapper, 4000))
        
        #threading.Thread(target=self.servico, args=()).start()

if __name__ == '__main__':

    node = Node(sys.argv[1], sys.argv[2])
    node.main()

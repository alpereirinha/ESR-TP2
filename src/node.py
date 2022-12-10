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

                self.handleFlood(address, aux_msg[1], aux_msg[2:], int(time.time() * 1000))
            
            elif aux_msg[0] == "STARTOVERLAY": #começar construção do overlay (a partir do servidor)
                
                for x in self.neighbours:

                    self.socket.sendto(("FLOOD 0 " + str(int(time.time() * 1000)) + " 0 " + self.host).encode('utf-8') ,(x, PORT))

            elif aux_msg[0] == "CONNECT": #recebe mensagem de um router para se conectar (começa no pc)
                
                self.connect(address, port)

            elif aux_msg[0] == "DISCONNECT": #pedido para se desconectar
                
                self.disconnect(address, port)

            elif aux_msg[0] == "STREAMING": #recebe mensagem de um router com streaming (começa no servidor)

                for n in self.ativos:
                    
                    self.socket.sendto(("STREAMING").encode('utf-8') ,(n, PORT))

            print(f"\n\nTABELA : {self.routing_table}")
            print(f"VIZINHOS: {self.neighbours}")
            print(f"ATIVOS: {self.ativos}")

    def addNeighbours(self, msg):

        for x in msg.split(","):

            self.lock.acquire()
            self.routing_table[x] = (x, 1, -1, 'no')
            self.lock.release()

    def handleFlood(self, address, instant, table, my_instant):

        changed = 0

        entries = table.split(" ") 

        for entry in entries:
            key = entry.split(":")[0]
            values = entry.split(":")[1]
            tempo = my_instant-instant+ float(values[2]) #float?
            if (key in self.routing_table): #entrada já existe na minha tabela

                if (self.routing_table[key][2] != -1): #entrada já foi preenchida com algum valor previamente

                    if((self.routing_table[key][2] > tempo) #valor que recebo para um certo destino é menor
                    or (self.routing_table[key][2] == tempo and int(values[1]) + 1 < self.routing_table[key][1])):
                    #valor que recebo é igual ao que já tenho mas tem menor número de saltos

                        self.routing_table[key][0] = values[0] #altera o nodo pela qual tem que seguir
                        self.routing_table[key][1] = int(values[1]) + 1 #altera o número de saltos para lá chegar
                        self.routing_table[key][2] = tempo #altera o tempo (em ms) para lá chegar
                        changed = 1

                else: #entrada existe mas ainda não foi ainda preenchida com tempo (caso dos vizinhos)
                    self.routing_table[key][2] = tempo #altera o tempo (em ms) para lá chegar
                    changed = 1

            else: #entrada não existe
                self.routing_table[key] = (values[0], int(values[1]) + 1, tempo, 'no')
                changed = 1

            if (changed): #só continuo o flood se a minha tabela tiver alterado
                vizinhos = [x for x in self.routing_table if self.routing_table[x][1] == 1 and x != address]

                str_to_send = ""
                list_to_send = []
                for neighbour in vizinhos:
                    neighbour_str = neighbour + ":" + ','.join(self.routing_table[neighbour])
                    list_to_send.append(neighbour_str)

                str_to_send = ' '.join(list_to_send)
                self.socket.send(("FLOOD " + str(int(time.time() * 1000)) + " " + str_to_send).encode("utf-8"))
                #FLOOD instant neighbour1:value1,value2,value3 neighbour:value1,value2,value3


    def connect(self, address, port):
        print(self.neighbours)
        
        if not len(self.ativos): #se ainda não tiver vizinhos ativos
            self.ativos.add(address)
            self.socket.sendto((("CONNECT ") + str(self.host)).encode('utf-8') ,(list(self.routing_table.keys())[0][1], 3000))
                
        elif len(self.ativos): #se já tiver vizinhos ativos
            self.ativos.add(address)
            self.socket.sendto(("STREAMING").encode('utf-8') ,(address, port))


    def disconnect(self, address, port):
        print(f"antigo: {self.ativos}")
        self.ativos.discard(address)
        print(f"novo: {self.ativos}")
        
        if not len(self.ativos):
            self.socket.sendto(("DISCONNECT " + str(self.host)).encode('utf-8'), (list(self.routing_table.keys())[0][1], 3000))
            self.socket.sendto(("STOPSTREAMING").encode('utf-8') ,(address, port))


    def servico(self):

        while True:

            time.sleep(3)
            print(self.routing_table)


    def main(self):

        threading.Thread(target=self.listen, args=()).start()
        self.socket.sendto("NEIGHBOURS".encode('utf-8'), (self.bootstrapper, 4000))
        
        #threading.Thread(target=self.servico, args=()).start()

if __name__ == '__main__':

    node = Node(sys.argv[1], sys.argv[2])
    node.main()

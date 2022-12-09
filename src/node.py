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
        self.previous_node = "" #para guardarmos o nodo de onde veio o flood e não enviarmos para ele (?)
        self.flooded = 0
        self.neighbours = set()
        self.ativos = set()

    def listen(self):

        while True:

            data, (address, port) = self.socket.recvfrom(1024) #probably vai ter que ser alterado
            
            aux_msg = data.decode('utf-8').split(' ')
            
            print(aux_msg)

            if aux_msg[0] == "ADDME": #recebe a lista de vizinhos a adicionar

                self.addNeighbours(aux_msg[1])
            
            elif aux_msg[0] == "FLOOD" and self.flooded==0: #mensagem de flood (começa no servidor)

                self.handleFlood(address, aux_msg[1], aux_msg[2], aux_msg[3], aux_msg[4])
            
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
            self.neighbours.add(x)
            self.lock.release()

    def handleFlood(self, address, hops, instant, total_time, server_ip):

        self.flooded += 1
        
        try:
            # [((IP DO SERVIDOR), (IP DA ORIGEM)): (SALTO, PING)]
            value = self.routing_table[(server_ip, address)][0]
        except:
            value = float("inf") 
            
        # FLOOD (NUMERO DE SALTOS) (TEMPO DO INSTANTE DO ENVIO) (TEMPO TOTAL) (IP DO SERVIDOR)
        if int(hops) + 1 < value:
            self.routing_table[(server_ip, address)] = (int(hops) + 1, int(time.time() * 1000) - int(instant) + int(total_time))  
            
            vizinhos = [x for x in self.neighbours if x != server_ip and x != address] #criar método servidor
            
            for n in vizinhos:
                self.socket.sendto(("FLOOD " + str(self.routing_table[(server_ip, address)][0]) + " " + str(int(time.time() * 1000)) + " " + str(self.routing_table[(server_ip, address)][1]) + " " + server_ip).encode('utf-8'), (n, PORT))   


    def connect(self, address, port):
        print(self.neighbours)
        
        if not len(self.ativos):
            self.ativos.add(address)
            self.socket.sendto((("CONNECT ") + str(self.host)).encode('utf-8') ,(list(self.routing_table.keys())[0][1], 3000))
                
        elif len(self.ativos):
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

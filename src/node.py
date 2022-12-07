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

    def listen(self):

        while True:

            data, (address, port) = self.socket.recvfrom(1024) #probably vai ter que ser alterado
            
            aux_msg = data.decode('utf-8').split(' ')
            
            print(aux_msg)

            if aux_msg[0] == "ADDME":

                for x in aux_msg[1].split(","):
                                   
                    self.lock.acquire()
                    self.routing_table[x] = (x, 1, "no")                    
                    self.lock.release()
            
            elif aux_msg[0] == "FLOOD" and self.flooded==0:

                self.flooded += 1
                print(aux_msg[1])

                try:
                    value = routing_table[aux_msg[4]][1]
                except:
                    value = float("inf") 

                # FLOOD (NUMERO DE SALTOS) (TEMPO QUE FOI ACUMULADO ANTES DA ORIGEM) (TEMPO DA ORIGEM) (IP DO SERVIDOR)
                if int(aux_msg[1]) + 1 < value:

                    #routing_table[aux_msg[4]][2]
                    self.routing_table[aux_msg[4]] = (address, int(aux_msg[1]) + 1, "no")  
                
                neighbours = [x for x in self.routing_table if x != aux_msg[4] and x != address]

                for n in neighbours:
                    
                    self.socket.sendto(("FLOOD " + str(self.routing_table[aux_msg[4]][1]) + " 200 " +  "0 " + aux_msg[4]).encode('utf-8') ,(n, PORT))   
            
            elif aux_msg[0] == "STARTOVERLAY":
                
                for x in self.routing_table:

                    self.socket.sendto(("FLOOD 0 200 0 " + self.host).encode('utf-8') ,(x, PORT))


    def servico(self):

        while True:

            time.sleep(3)
            print(self.routing_table)

    def defineRoutes(self, data, address):

        #falta receber

        str_to_send = ""
        list_to_send = []

        for neighbour in self.routing_table:
            #deve haver uma maneira melhor de fazer esta string
            neighbour_str = "key:" + neighbour + ",values:" + ' '.join(self.routing_table[neighbour])
            #enviar também o instante? para comparar os delays
            list_to_send.append(neighbour_str)
        
        for x in self.routing_table:
            str_to_send = ';'.join(list_to_send)
            self.socket.sendto(str_to_send.encode("utf-8"), (x, PORT))





    def main(self):

        threading.Thread(target=self.listen, args=()).start()
        self.socket.sendto("NEIGHBOURS".encode('utf-8'), (self.bootstrapper, 4000))
        
        threading.Thread(target=self.servico, args=()).start()

if __name__ == '__main__':

    node = Node(sys.argv[1], sys.argv[2])
    node.main()
from node import Node
import socket, threading, sys, os, time
from pprint import pprint

class Client(Node):

    def __init__(self, host):

        self.host = host
        self.port = 3000
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((host, 3000))
        self.lock = threading.Lock()

    
    def sendConnect(self, addr):

        self.socket.sendto(("CONNECT " + str(self.host)).encode('utf-8'), (addr, 3000))

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

    def connect(self, address, port):
        print(self.neighbours)
        
        if not len(self.ativos): #se ainda não tiver vizinhos ativos
            self.ativos.add(address)
                
        elif len(self.ativos): #se já tiver vizinhos ativos
            self.ativos.add(address)
            self.socket.sendto(("STREAMING").encode('utf-8') ,(address, port)) #começa o streaming


    def process(self, addr):
        
        #self.connect(addr)

        while True:
            
            data, (address, port) = self.socket.recvfrom(1024) #probably vai ter que ser alterado
            aux_msg = data.decode('utf-8').split(' ')
            print(aux_msg)

    def streaming(self, addr):

        time.sleep(5)
        self.socket.sendto(("DISCONNECT " + str(self.host)).encode('utf-8'), (addr, 3000))

    def main(self, addr):

        threading.Thread(target=self.process, args=([addr])).start()
        self.socket.sendto("NEIGHBOURS".encode('utf-8'), (self.bootstrapper, 4000))
        #threading.Thread(target=self.streaming, args=([addr])).start()
        

if __name__ == '__main__':

    client = Client(sys.argv[1])
    client.main(sys.argv[2])

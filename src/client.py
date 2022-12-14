from node import Node
import socket, threading, sys, os, time
from pprint import pprint
from tkinter import Tk
from RtpPacket import RtpPacket
from ClienteGUI import ClienteGUI

PORT = 3000

class Client(Node):

    def __init__(self, host, bootstrapper):

        super(Client, self).__init__(host, bootstrapper)
        self.lock = threading.Lock()
        self.root = Tk()
        print(self.host)
        self.clienteGUI = ClienteGUI(self.root, "", PORT, int(self.host[-1]))
    
    def start_stream(self, nome, pc, port):
        pass

    def stop_stream(self, nome, pc, port):
        pass

    def start_stream(self):

        self.socket.sendto(("STARTSTREAMING " + self.host).encode('utf-8') ,(self.routing_tables[self.server][self.server][0], PORT))

    def stop_stream(self):

        self.socket.sendto(("STOPSTREAMING " + self.host).encode('utf-8') ,(self.routing_tables[self.server][self.server][0], PORT))

    def startFlood():
        pass

    def handle_stream(self, data):

        rtpPacket = RtpPacket()
        rtpPacket.decode(data)
        
        currFrameNbr = rtpPacket.seqNum()
        # print("Current Seq Num: " + str(currFrameNbr))
                            
        if currFrameNbr > self.clienteGUI.frameNbr: # Discard the late packet
            self.clienteGUI.frameNbr = currFrameNbr
            self.clienteGUI.updateMovie(self.clienteGUI.writeFrame(rtpPacket.getPayload()))

        if self.clienteGUI.frameNbr == 500:
            self.clienteGUI.frameNbr = 0

    def check_server(self):
        pass

    def main(self):

        super().main()
        self.clienteGUI.master.title(self.host)
        val = input()
        if val == "start":

            self.start_stream()

        self.root.mainloop()

        #threading.Thread(target=self.process, args=([addr])).start()
        #self.socket.sendto("NEIGHBOURS".encode('utf-8'), (self.bootstrapper, 4000))
        #threading.Thread(target=self.streaming, args=([addr])).start()
        

if __name__ == '__main__':

    client = Client(sys.argv[1], sys.argv[2])
    client.main()


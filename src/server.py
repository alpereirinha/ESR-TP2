from node import Node

import json
import threading
from random import randint
import sys, traceback, threading, socket, time
from VideoStream import VideoStream
from RtpPacket import RtpPacket

PORT = 3000

FILENAME = "movie.Mjpeg"
BOOTSTRAP = "bootstrap.json"
TIME = 3

class Server(Node):

    def __init__(self, host, bootstrapper):
        super(Server, self).__init__(host, bootstrapper)
        self.videostream = VideoStream(FILENAME)
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def start_stream(self, nome, pc, port):

        # self.routing_tables[self.host][nome] = (self.routing_tables[self.host][nome][1], self.routing_tables[self.host][nome][2], self.routing_tables[self.host][nome][0], "yes")
        self.routing_tables[self.host][pc] = (self.routing_tables[self.host][pc][0], self.routing_tables[self.host][pc][1], self.routing_tables[self.host][pc][2], "yes")
        threading.Thread(target=self.sendRtp).start()

    def stop_stream(self, nome, pc, port):

        # self.routing_tables[self.host][nome] = (self.routing_tables[self.host][nome][1], self.routing_tables[self.host][nome][2], self.routing_tables[self.host][nome][0], "no")
        self.routing_tables[self.host][pc] = (self.routing_tables[self.host][pc][0], self.routing_tables[self.host][pc][1], self.routing_tables[self.host][pc][2], "no")

    def check_server(self):
        pass

    def startFlood(self):

        self.flood_nr += 1
        if (self.flood_nr > 1):
            self.aux_routing_tables[self.host].clear()
            self.aux_routing_tables[self.host] = dict(self.neighbours)

        vizinhos = [x for x in self.neighbours if x != self.host] #if self.aux_routing_tables[self.server][x][1] == 1]
        print ("VIZINHOS: " + str(vizinhos))

        str_to_send = ""
        list_to_send = []
        for neighbour in vizinhos:
            neighbour_str = neighbour + ":" + ','.join(map(str, self.aux_routing_tables[self.host][neighbour]))
            list_to_send.append(neighbour_str)

        str_to_send = ' '.join(list_to_send)

        for x in vizinhos:
            self.socket.sendto(("FLOOD " + self.host + " " + str(int(time.time() * 1000)) + " " + str(self.flood_nr) + " " + str_to_send).encode("utf-8"),(self.ips[x], PORT))

    def sendRtp(self):
        """Send RTP packets over UDP."""
        while True:

            data = self.videostream.nextFrame()

            if data:

                frameNumber = self.videostream.frameNbr()

                for node in set([self.routing_tables[self.host][x][0] for x in self.routing_tables[self.host] if self.routing_tables[self.host][x][3] == "yes"]):
                    try:
                        address = node
                        port = 5000
                        packet =  self.makeRtp(data, frameNumber)
                        self.rtpSocket.sendto(packet, (address, 5000))
                    except:
                        print("Connection Error")
                        print('-'*60)
                        traceback.print_exc(file=sys.stdout)
                        print('-'*60)

            else:
                self.videostream.file.seek(0)
                self.videostream.frameNum = 0
            time.sleep(0.04)
        # Close the RTP socket
        self.rtpSocket.close()
        print("All done!")

    def makeRtp(self, payload, frameNbr):
        """RTP-packetize the video data."""
        version = 2
        padding = 0
        extension = 0
        cc = 0
        marker = 0
        pt = 26 # MJPEG type
        seqnum = frameNbr
        ssrc = 0
        
        rtpPacket = RtpPacket()
        
        rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
        # print("Encoding RTP Packet: " + str(seqnum))
        
        return rtpPacket.getPacket()

    def main(self):
        super().main()

        # while self.host not in self.routing_tables:

        #     # mudar isto para await
        #     time.sleep(15)
        # threading.Thread(target=self.sendRtp).start()

if __name__ == '__main__':

    server = Server(sys.argv[1], sys.argv[2])
    server.main()

# python3 node.py 10.0.1.2 3001 10.0.0.10

from node import Node

import json
import threading
from random import randint
import sys, traceback, threading, socket
from videostream import VideoStream
from RtpPacket import RtpPacket

PORT = 3000

FILENAME = "movie.Mjpeg"
BOOTSTRAP = "bootstrap.json"

class Server(Node):
    
    def __init__(self, host, bootstrapper):
        super(Server, self).__init__(host, bootstrapper)
        #self.videostream = VideoStream(FILENAME)
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def start_stream(self, address, port):

        self.routing_table[address] = (self.routing_table[address][1], self.routing_table[address][2], self.routing_table[address][0], "yes")

    def stop_stream(self, address, port):

        self.routing_table[address] = (self.routing_table[address][1], self.routing_table[address][2], self.routing_table[address][0], "no")

    def disconnect(self, address, port):
        pass

    def sendRtp(self):
        """Send RTP packets over UDP."""
        while True:

            # self.clientInfo['event'].wait(0.05)
            
            # # Stop sending if request is PAUSE or TEARDOWN
            # if self.clientInfo['event'].isSet():
            #     break

            data = self.videostream.nextFrame()

            if data:

                frameNumber = self.videostream.frameNbr()

                print([x for x in self.routing_table if self.routing_table[x][3] == "yes"])
                for node in [x for x in self.routing_table if self.routing_table[x][3] == "yes"]:
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
        print("Encoding RTP Packet: " + str(seqnum))
        
        return rtpPacket.getPacket()

    def main(self):
        super().main()
        #threading.Thread(target=self.sendRtp).start()

if __name__ == '__main__':

    server = Server(sys.argv[1], sys.argv[2])
    server.main()

# python3 node.py 10.0.1.2 3001 10.0.0.10

from node import Node

FILENAME = "movie.Mjpeg"

class Server(Node):
    def __init__(self, host, port):
        super().__init__(host, port)
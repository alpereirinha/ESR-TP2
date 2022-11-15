from node import Node

class Client(Node):
    def __init__(self, host, port):
        super().__init__(host, port)
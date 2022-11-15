class VideoStream:
    def __init__(self, filename):
        self.filename = filename
        try:
            self.file = open(filename, 'rb')
        except:
            raise IOError
        self.frame = 0

    def getNextFrame(self):
        data = self.file.read(5)

        if data:
            framelength = int(data)

            data = self.file.read(framelength)
            self.frame += 1
        
        return data
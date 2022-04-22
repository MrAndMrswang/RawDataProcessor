from utils.log import getLogger
import os

#
class BinFile:
    def __init__(self, filePath) ->None :
        self.file = open(filePath, 'rb')
        self.polar = filePath.split('/')[-1][13:15]
        size = os.path.getsize(filePath)
        getLogger("spacePacketCreator").info("open file size:" + str(size))
        
    def read(self, n):
        return self.file.read(n)
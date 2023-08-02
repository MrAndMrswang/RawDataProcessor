from utils.log import getLogger
from vo.spacePacket import SpacePacket
from .spDecoder import SPDecoder
import pickle

class SPCreator:
    def __init__(self, binFile):
        self.binFile = binFile
        self.spacePacketsLengthMAX = 2000000
        self.startIndex = 0
        

    # save data range by range
    def saveOneRangeData(self, packetIndex, packets):
        dumpFileName = "./data/%s/decode/rangeLine_%d.pkl" % (self.binFile.polar, packetIndex)
        dumpFile = open(dumpFileName, 'wb')
        pickle.dump(packets, dumpFile)


    def createSpacekets(self):
        readDataSize = 0
        packets = []
        i = 0
        while(1):
            getLogger("spacePacketCreator").info("space packet index=%d|readDataSize=%dMB|%dB" % (i, readDataSize/1024/1024, readDataSize))
            decoder = SPDecoder(self.binFile)
            packet0 = SpacePacket()

            # Packet Primary Header
            ok = decoder.preparePacketPrimaryHeader(packet0)
            if ok == False:
                getLogger("spacePacketCreator").warn("break|preparePacketPrimaryHeader")
                break
            
            # Packet Secondary Header
            decoder.preparePacketSecondaryHeader(packet0)
            i += 1

            getLogger("spacePacketCreator").info("index=%d|spacePacket.NumberOfQuads=%d|spacePacket.packetDataLength=%d" % (i, packet0.NumberOfQuads, packet0.packetDataLength)) 
            readDataSize += packet0.packetDataLength + 1 + 6
            # 
            if (not packet0.isEcho()) or (not packet0.isMeasurementMode()): # or i < self.startIndex:
                getLogger("spacePacketCreator").warn("index=%d|type:%d|isEcho=%d|isMM=%d" % (i, packet0.signalType, packet0.isEcho(), packet0.testMode))
                self.binFile.read(packet0.packetDataLength - 61)
                continue

            # User Data Field
            decoder.prepareUserDataFiled(packet0)
            getLogger("spacePacketCreator").info("index=%d|ISampleValue length=%d" % (i, packet0.QSampleValue.shape[0]))

            # validate
            # Space Packet Length = Multiple of 4 Octets

            # one list, one ISampleValue length
            if len(packets) == 0 or packets[0].swathNumber == packet0.swathNumber:
                packets.append(packet0)
            else:
                getLogger("spacePacketCreator").info("index=%d|one kind|Sample len=%d|swathNumber change:  %d->%d" % (i, packet0.QSampleValue.shape[0], packets[0].swathNumber, packet0.swathNumber))
                
                self.saveOneRangeData(i, packets)
                packets = [packet0]
                

            if i == self.spacePacketsLengthMAX:
                getLogger("spacePacketCreator").info("getEnoughPackets|index=%d" % i)
                break
                
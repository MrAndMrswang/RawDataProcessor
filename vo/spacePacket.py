#
class SpacePacket:
    def __init__(self):
        self.hCode = 0
        self.hCodeBitsSize = 0
        self.userDataCnt = 0
        self.bitRateCodeList = []
        self.thresholdIndexList = []


        # space packet define
        self.primaryHeader = 0
        self.packetDataLength = 0 
        self.datationService = 0
        self.fixedAncillaryDataField = 0
        self.subCommutationAncillaryDataServiceField = 0
        self.countersService = 0
        self.radarSampleCountService = 0

        self.ISampleValue = []
        self.QSampleValue = []

    #
    def isEcho(self):
        return self.signalType == 0


    def saveTHIDX(self, thidx):
        self.thresholdIndexList.append(thidx)
    

    def saveBRC(self, brc):
        # getLogger("spacePacketCreator").info("saveBRC|brc=%s" % (brc))
        self.bitRateCodeList.append(brc)
    

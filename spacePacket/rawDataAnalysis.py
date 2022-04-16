import math

# section 4.1
class RawDataAnalysis:
    def __init__(self, spacePackets):
        self.spacePackets = spacePackets
        self.allDataLength = 0

    def calcMean(self):
        iSumValue = 0
        qSumValue = 0
        for packet0 in self.spacePackets:
            for i in range(packet0.ISampleValue):
                self.allDataLength += 1
                iSumValue += packet0.ISampleValue[i]
                qSumValue += packet0.QSampleValue[i]
                
        
        self.iMean = iSumValue / self.allDataLength
        self.qMean = qSumValue / self.allDataLength
    
    def calcSTD(self):
        iSquare = 0
        qSquare = 0
        for packet0 in self.spacePackets:
            for i in range(packet0.ISampleValue):
                iSquare += math.pow(packet0.ISampleValue[i] - self.iMean, 2)
                qSquare += math.pow(packet0.QSampleValue[i] - self.qMean, 2)
                
        
        self.iSTD = math.sqrt(iSquare / self.allDataLength)
        self.qSTD = math.sqrt(qSquare / self.allDataLength)
    
    def calcIQGain(self):
        self.iQGain = self.iSTD / self.qSTD
        self.lowerBounds = 1 - 3 / math.sqrt(self.allDataLength)
        self.upperBounds = 1 + 3 / math.sqrt(self.allDataLength)


    # for each range line
    def calcIQquadraturedeparture(self):
        lastSWST = 0
        ckList = []
        zkList = []

        # need to refresh
        m = 0
        iSum = 0
        iSquare = 0
        qSum = 0
        qSquare = 0
        iqMulti = 0


        for packet0 in self.spacePackets:
            if lastSWST != 0 and lastSWST != packet0.radarConfigurationSupportService.swst:
                sqq = qSquare - math.pow(qSquare, 2) / m
                sii = iSquare - math.pow(iSquare, 2) / m
                siq = iqMulti - iSum * qSum / m
                ck = siq / math.sqrt(sii * sqq)
                zk = 0.5 / math.log((1 + ck) / (1 - ck))
                ckList.append(ck)
                zkList.append(zk)

                m = 0   
                iSum = 0
                iSquare = 0
                qSum = 0
                qSquare = 0
                iqMulti = 0

            
            lastSWST = packet0.radarConfigurationSupportService.swst
            for i in range(len(packet0.ISampleValue)):
                m += 1

                iSum += packet0.ISampleValue[i]
                iSquare += math.pow(packet0.ISampleValue[i], 2)

                qSum += packet0.QSampleValue[i]
                qSquare += math.pow(packet0.QSampleValue[i], 2)

                iqMulti += packet0.ISampleValue[i] * packet0.QSampleValue[i]


        # Calculate the mean and the standard deviation of the vector z
        zSum = 0
        for v in zkList:
            zSum += v
        zMean = zSum / len(zkList)

        zQuare = 0
        for v in zkList:
            zQuare += math.pow(v - zMean, 2)

        zSTD = math.sqrt(zQuare / len(zkList))

        # Calculate the IQ quadrature departure
        c = math.tanh(zMean)
        xigema1 = math.tanh(zMean + zSTD) - c
        xigema0 = c - math.tanh(zMean - zSTD)

        self.quadratureDeparture = math.asin(c)
        self.quadratureDepartureLowerBound = math.asin(c - xigema0)
        self.quadratureDepartureUpperBound = math.asin(c + xigema1)

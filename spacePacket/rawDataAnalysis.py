import math
import numpy as np
from utils.log import getLogger

# section 4.1
# for one range line
class RawDataAnalysis:
    # space packets for one range line
    def __init__(self, spacePackets):
        self.spacePackets = spacePackets
        self.allDataLength = 0

    def process(self):
        self.calcMean()
        self.calcSTD()
        self.calcIQGain()
        self.calcIQquadraturedeparture()


    def calcMean(self):
        iSumValue = 0
        qSumValue = 0
        for packet0 in self.spacePackets:
            self.allDataLength += packet0.ISampleValue.shape[0]
            iSumValue += np.sum(packet0.ISampleValue)
            qSumValue += np.sum(packet0.QSampleValue)
                
        self.iMean = iSumValue / self.allDataLength
        self.qMean = qSumValue / self.allDataLength
        getLogger("corrector").info("self.iMean=%f|self.qMean=%f" % (self.iMean, self.qMean))
    

    def calcSTD(self):
        iSquare = 0
        qSquare = 0
        for packet0 in self.spacePackets:
            iSquare += np.sum((packet0.ISampleValue - self.iMean) ** 2)
            qSquare += np.sum((packet0.QSampleValue - self.qMean) ** 2)
                
        self.iSTD = math.sqrt(iSquare / self.allDataLength)
        self.qSTD = math.sqrt(qSquare / self.allDataLength)
        getLogger("corrector").info("self.iSTD=%f|self.qSTD=%f" % (self.iSTD, self.qSTD))
    

    def calcIQGain(self):
        self.iQGain = self.iSTD / self.qSTD
        self.lowerBounds = 1 - 3 / math.sqrt(self.allDataLength)
        self.upperBounds = 1 + 3 / math.sqrt(self.allDataLength)
        getLogger("corrector").info("self.iQGain=%f|self.lowerBounds=%f|self.upperBounds=%f" % (self.iQGain, self.lowerBounds, self.upperBounds))


    # for each range line
    def calcIQquadraturedeparture(self):
        ckList = []
        zkList = []

        #
        iSum = 0
        iSquare = 0
        qSum = 0
        qSquare = 0
        iqMulti = 0

        for packet0 in self.spacePackets:
            iSum += np.sum(packet0.ISampleValue)
            iSquare += np.sum(packet0.ISampleValue ** 2)

            qSum += np.sum(packet0.QSampleValue)
            qSquare += np.sum(packet0.QSampleValue ** 2)

            iqMulti += np.sum(packet0.ISampleValue * packet0.QSampleValue)


        sqq = qSquare - math.pow(qSum, 2) / self.allDataLength
        sii = iSquare - math.pow(iSum, 2) / self.allDataLength
        siq = iqMulti - iSum * qSum / self.allDataLength
        ck = siq / math.sqrt(sii * sqq)
        zk = 0.5 * math.log((1 + ck) / (1 - ck))
        ckList.append(ck)
        zkList.append(zk)

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

        getLogger("verbose").info("zMean=%f|zSTD=%f|quadratureDeparture=%s|up=%f|down=%f" % (zMean, zSTD, self.quadratureDeparture, self.quadratureDepartureUpperBound, self.quadratureDepartureLowerBound))

        if self.quadratureDeparture > self.quadratureDepartureUpperBound:
            self.quadratureDeparture = self.quadratureDepartureUpperBound
        
        if self.quadratureDeparture < self.quadratureDepartureLowerBound:
            self.quadratureDeparture = self.quadratureDepartureLowerBound

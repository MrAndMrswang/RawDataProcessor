from decode import SpacePacketDecoder
import numpy as np
import math

class RawDataAnalysis:
    def __init__(self, filePath):
        self.decoder = SpacePacketDecoder(self.rawDataFilePath)


    def calcMeanOfRawData(self):
        iArray = np.array(self.decoder.iEValueList + self.decoder.iOValueList)
        iMean = np.mean(iArray)
        iSTD = np.std(iArray)

        qArray = np.array(self.decoder.qEValueList + self.decoder.qOValueList)
        qMean = np.mean(qArray)
        qSTD = np.std(iArray)

        # calculate the IQ Gain Imbalance
        iQGain = iSTD / qSTD
        length = len(iArray)
        lowerBounds = 1 - 3 / math.sqrt(length)
        upperBounds = 1 + 3 / math.sqrt(length)


    def calcStandardDeviationsOfRawData(self):

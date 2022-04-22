import pickle
import math
import numpy
from .rawDataAnalysis import RawDataAnalysis

from utils.log import getLogger

class Corrector:
    def __init__(self) -> None:
        pass


    def correct(self, name):
        self.preparePackets(name)
        self.IQBias()
        self.saveCorrectedData(name)


    def saveCorrectedData(self, name):
        dumpFileName = "./data/correct/%s.pkl" % name
        dumpFile = open(dumpFileName, 'wb')
        pickle.dump(self.packets, dumpFile)
    

    def preparePackets(self, name):
        self.pklFile = name
        self.packets = pickle.load(open("./data/decode/%s.pkl" % name, "rb"))
        getLogger("corrector").info("npyFile=%s|packets len = %d" % (self.pklFile, len(self.packets)))

        self.analysis = RawDataAnalysis(self.packets)
        self.analysis.process()


    def IQBias(self):
        packetsIndex = 0
        for packet0 in self.packets:
            getLogger("corrector").info("before|packetsIndex=%d|Qvalue=%s" % (packetsIndex,packet0.QSampleValue[0:10]))

            # 1. correct for biases
            packet0.ISampleValue = packet0.ISampleValue + self.analysis.iMean
            packet0.QSampleValue = packet0.QSampleValue + self.analysis.qMean

            # 2. correct for gain imbalance
            packet0.QSampleValue = self.analysis.iQGain * packet0.QSampleValue

            # 3. Correct the Q channel for non-orthogonality:
            packet0.QSampleValue = packet0.QSampleValue / math.cos(self.analysis.quadratureDeparture) - packet0.ISampleValue * math.tan(self.analysis.quadratureDeparture)

            getLogger("corrector").info("before|packetsIndex=%d|iMean=%f|qMean=%f|IQGain=%f|quadratureDeparture=%s" % (packetsIndex,self.analysis.iMean, self.analysis.qMean, self.analysis.iQGain, self.analysis.quadratureDeparture))

            getLogger("corrector").info("after|packetsIndex=%d|all=%d|ISampleValue.length=%s|value=%s" % (packetsIndex, len(self.packets), packet0.ISampleValue.shape[0], packet0.QSampleValue[0:10]))

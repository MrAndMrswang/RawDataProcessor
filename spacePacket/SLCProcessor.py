from utils.log import getLogger
import numpy as np
import math
import matplotlib.pyplot as plt
import pickle

# version 0.1.
class SLCProcessor:
    def __init__(self) -> None:
        pass


    def compress(self, name):
        self.pklFile = name
        packets = pickle.load(open("./data/decode/%s.pkl" % name, "rb"))
        getLogger("SLCProcessing").info("npyFile=%s|packets len = %d" % (self.pklFile, len(packets)))

        rangeCompressMat = self.rangeCompress(packets)
        self.azimuthCompress(rangeCompressMat)


    # range compress
    def rangeCompress(self, packets):
        rangelength = len(packets[0].ISampleValue)
        azimuthLength = len(packets)
        resData = np.zeros((rangelength, azimuthLength), dtype = "complex_")
        index = 0
        for packet in packets:
            samplePoint = packet.SamplingFrequencyAfterDecimation * packet.TXPL
            tim = np.linspace(-packet.TXPL / 2, packet.TXPL / 2,  int(samplePoint))
            phi1 = packet.TXPSF + packet.TXPRR * packet.TXPL / 2
            phi2 = packet.TXPRR / 2
            chirpReplica = np.exp(-1j*2*np.pi*(phi1*tim + phi2*tim**2))
            getLogger("verbose").info("i=%d|len:%d|phi1=%f|phi2=%f" % (index, len(tim), phi1, phi2))

            # cross
            echoData = np.array(packet.ISampleValue) + 1j*np.array(packet.QSampleValue)
            res = np.correlate(chirpReplica, echoData, mode='full')
            res = res[math.floor(len(chirpReplica)/2) : 
                      rangelength + math.floor(len(chirpReplica)/2)]
            resData[::, index] = res
            index += 1
        
        return resData


    # azimuth compress
    def azimuthCompress(self, rangeCompressMat):
        # get azimuth chirp
        rangelength, azimuthLength = rangeCompressMat.shape
        tempMat = rangeCompressMat.copy()
        zeros0 = np.zeros(tempMat[::, 0:300].shape)
        tempMat[::, 0:300] = zeros0
        tempMat[::, azimuthLength-300:azimuthLength] = zeros0
        maxPos = np.unravel_index(np.argmax(np.abs(tempMat)), tempMat.shape)
        mychirp = rangeCompressMat[maxPos[0], maxPos[1]-300 : maxPos[1]+300]
        for i in range(rangelength):
            temp = np.correlate(mychirp, rangeCompressMat[i, ::], mode='full')
            temp = temp[math.floor(len(mychirp)/2) : 
                      azimuthLength + math.floor(len(mychirp)/2)]
            tempMat[i, ::] = temp
        
        plt.figure()
        plt.pcolor(np.fliplr(np.flipud(np.abs(tempMat[::3, ::3]))), vmin = 1, vmax = 2*10**8)
        plt.colorbar()
        plt.savefig("./pic/test.png", dpi=800)

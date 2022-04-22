from utils.log import getLogger
import numpy as np
import math
import matplotlib.pyplot as plt
from scipy import fft
import pickle

# version 0.1.
class SLCProcessor:
    def __init__(self, polar, name) -> None:
        self.polar = polar
        self.name = name


    def compress(self):
        packets = pickle.load(open("./data/%s/correct/%s" % (self.polar, self.name), "rb"))
        getLogger("SLCProcessing").info("npyFile=%s|packets len = %d" % (self.name, len(packets)))

        rangeCompressMat = self.rangeCompress(packets)
        self.azimuthCompress(rangeCompressMat)


    # range compress
    def rangeCompress(self, packets):
        rangelength = packets[0].ISampleValue.shape[0]
        azimuthLength = len(packets)
        resData = np.zeros((rangelength, azimuthLength), dtype = "complex_")
        getLogger("SLCProcessing").info("rangelength=%d|azimuthLength=%d" % (rangelength, azimuthLength))
        index = 0
        for packet in packets:
            samplePoint = packet.SamplingFrequencyAfterDecimation * packet.TXPL
            tim = np.linspace(-packet.TXPL / 2, packet.TXPL / 2,  int(samplePoint))
            phi1 = packet.TXPSF + packet.TXPRR * packet.TXPL / 2
            phi2 = packet.TXPRR / 2
            chirpReplica = np.exp(-1j*2*np.pi*(phi1*tim + phi2*tim**2))
            
            # cross
            echoData = packet.ISampleValue + 1j*packet.QSampleValue
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
        
        tempMat = np.fliplr(np.flipud(np.abs(tempMat)))
        # self.showALL(tempMat)
        self.showPart(tempMat)
        

    def showALL(self, tempMat):
        tempMat = tempMat[::3, ::3]
        scale = 100
        (r1, c1) = tempMat.shape
        plt.figure(figsize=(scale*c1/r1, scale), dpi=128)
        plt.pcolor(tempMat, vmin = 1, vmax = 2*10**8)
        plt.colorbar()
        plt.savefig("./pic/%s/%s_all.png" % (self.polar, self.name.split('.')[0]))


    def showPart(self, tempMat):
        (row, col) = tempMat.shape
        picNum = int(row / 20)
        for index in range(20):
            showMat = tempMat[index*picNum:(index+1)*picNum, ::]
            scale = 100
            (r1, c1) = showMat.shape
            plt.figure(figsize=(scale*c1/r1, scale), dpi=100)
            plt.pcolor(showMat, vmin = 1, vmax = 2*10**8)
            plt.colorbar()
            plt.savefig("./pic/%s/%s_%d.png" % (self.polar, self.name.split('.')[0], index))
        

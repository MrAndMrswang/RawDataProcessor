from utils.log import getLogger
import numpy as np
import math
import os
import gc
import matplotlib.pyplot as plt
import pickle
import multiprocessing
import scipy.io as sio

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
            getLogger("SLCProcessing").info("chirpReplica=%d|phi1=%f|phi2=%f|samplePoint=%d" % 
            (len(chirpReplica), phi1, phi2, samplePoint))
            # cross
            echoData = packet.ISampleValue + 1j*packet.QSampleValue
            res = np.correlate(chirpReplica, echoData, mode='full')
            res = res[math.floor(len(chirpReplica)/2) : 
                      rangelength + math.floor(len(chirpReplica)/2)]
            resData[::, index] = res
            index += 1
        
        
        # resDataTemp = np.fliplr(np.flipud(np.abs(resData)))
        # figName = "./pic/%s/all/%s_range" % (self.polar, self.name.split('.')[0])
        # self.saveFig(resDataTemp, figName, 1400)
        return resData


    # azimuth compress
    def azimuthCompress(self, rangeCompressMat):
        # get azimuth chirp
        rangelength, azimuthLength = rangeCompressMat.shape
        getLogger("SLCProcessing").info("rangelength=%d|azimuthLength=%d" % (rangelength, azimuthLength))
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
        getLogger("SLCProcessing").info("azimuthCompress=%s|ready to plot" % self.name)
        self.showALL(tempMat)
        self.showPart(tempMat)
        

    def showALL(self, tempMat):
        figName = "./pic/%s/all/%s_all" % (self.polar, self.name.split('.')[0])
        self.saveFig(tempMat, figName, 2*10**8)


    def showPart(self, tempMat):
        (row, col) = tempMat.shape
        dir0 = "./pic/%s/part/%s" % (self.polar, self.name.split('.')[0])
        if not os.path.exists(dir0):
            os.mkdir(dir0)

        picNum = int(row / 60)
        for index in range(60):
           figName = "%s/%d" % (dir0, index)
           showMat = tempMat[index*picNum:(index+1)*picNum, ::]
           self.saveFig(showMat, figName, 2*10**8)


    def saveFig(self, data, figName, vmax0):
        sio.savemat(figName+'.mat', {'data': data})

        data = data[::3, ::3]
        scale = 100
        (r1, c1) = data.shape
        fig = plt.figure(figsize=(scale*c1/r1, scale), dpi=128)
        # plt.pcolor(data, vmin = 0, vmax = 1400)
        # plt.pcolor(data, vmin = 0, vmax = 2*10**8)
        plt.pcolor(data, vmin = 0, vmax = vmax0)
        
        plt.colorbar()
        plt.savefig(figName+'.png')
        fig.clf()
        plt.close()
        gc.collect()


    # save Origin data as img
    def saveOrigin(self):
        packets = pickle.load(open("./data/%s/decode/%s" % (self.polar, self.name), "rb"))
        rangelength = packets[0].ISampleValue.shape[0]
        azimuthLength = len(packets)
        resData = np.zeros((rangelength, azimuthLength), dtype = "complex_")
        index = 0
        for packet in packets:
            echoData = packet.ISampleValue + 1j*packet.QSampleValue
            resData[::, index] = echoData
            index += 1

        resData = np.fliplr(np.flipud(np.abs(resData[::3, ::3])))
        print(np.mean(resData))
        figName = "./pic/%s/all/%s_ori" % (self.polar, self.name.split('.')[0])
        self.saveFig(resData, figName)


    def saveOriginSingle(self):
        packets = pickle.load(open("./data/%s/decode/%s" % (self.polar, self.name), "rb"))
        rangelength = packets[0].ISampleValue.shape[0]
        azimuthLength = len(packets)
        resDataI = np.zeros((rangelength, azimuthLength))
        index = 0
        for packet in packets:
            resDataI[::, index] = packet.ISampleValue
            index += 1

        print(np.mean(resDataI), np.min(resDataI), np.max(resDataI))
        self.saveFig(resDataI[::3, ::3], "./pic/%s/all/%s_I" % (self.polar, self.name.split('.')[0]))

        resDataI = []
        resDataQ = np.zeros((rangelength, azimuthLength))
        index = 0
        for packet in packets:
            resDataQ[::, index] = packet.QSampleValue
            index += 1

        print(np.mean(resDataQ), np.min(resDataQ), np.max(resDataQ))
        self.saveFig(resDataQ[::3, ::3], "./pic/%s/all/%s_Q" % (self.polar, self.name.split('.')[0]))
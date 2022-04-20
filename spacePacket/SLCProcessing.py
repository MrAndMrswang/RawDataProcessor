from utils.log import getLogger
import numpy as np
import math
import matplotlib.pyplot as plt

# version 0.1.
class SLCProcessor:
    def __init__(self, index) -> None:
        self.index = index


    def compress(self, packets):
        getLogger("SLCProcessing").info("range length=%d|azimut length=%d" % 
            (len(packets[0].ISampleValue), len(packets)))
        if (len(packets) <= 700):
            return

        rangeCompressMat = self.rangeCompress(packets)
        self.azimuthCompress(rangeCompressMat)


    # range compress
    def rangeCompress(self, packets):
        rangelength = len(packets[0].ISampleValue)
        azimuthLength = len(packets)
        resData = np.zeros((rangelength, azimuthLength), dtype = "complex_")
        index = 0
        for packet in packets:
            rcss = packet.radarConfigurationSupportService
            samplePoint = rcss.SamplingFrequencyAfterDecimation * rcss.TXPL
            tim = np.linspace(-rcss.TXPL / 2, rcss.TXPL / 2,  int(samplePoint))
            phi1 = - (rcss.TXPSF + rcss.TXPRR * rcss.TXPL / 2)
            phi2 = - (rcss.TXPRR / 2)
            chirpReplica = np.exp(1j*2*np.pi*(phi1*tim + phi2*tim**2))
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
        plt.savefig("./pic/%d.png" % self.index, dpi=800)


    def test(self):
        # a = np.random.randn(10, 120)
        # c = a.shape
        # print(c[1])
        # for i in range(5):
        #     plt.figure()
        #     plt.pcolor([[1,2,3],[1,2,3],[1,2,3]], cmap="jet")
        #     plt.colorbar()
        
        # plt.show()
        # res = a[::3, ::3]
        # # res = np.unravel_index(np.argmax(np.abs(a)), a.shape)
        tim = np.array([-1, 0 , 1, 2, 3, 4])
        print("2*tim**2:", 2*tim**2)
        ans = 1j*2*np.pi*(1*tim + 2*tim**2)
        print("ans:", ans)

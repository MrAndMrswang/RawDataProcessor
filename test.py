import os
from typing import ValuesView

from sympy import fraction

from spacePacket.spCreator import SPCreator
from spacePacket.slcProcessor import SLCProcessor
from spacePacket.corrector import Corrector
from vo.binFile import BinFile
from scipy.fftpack import fft, ifft
import numpy as np
import math
import matplotlib.pyplot as plt



def ReadFile():
    # NQ = 2863
    # IE Huffmann BRC = 000
    binFile = open(filePath, 'rb')
    size = os.path.getsize(filePath)
    data = binFile.read(10)
    print("data:", data, " data[0]:", data[0:1])
    # for i in range(90):
    #     data = binFile.read(10)
    #     data[0]
    #     if i < 5:
    #         print("data:", data)
        # os.sys.stdout.buffer.write(data)
        # r_int = int.from_bytes(data, byteorder='big')  #将 byte转化为 int
        # b = '{:08b}'.format(r_int)
        # c = '{:08b}'.format(data >> 2)
        # if i == 1:
        #     print("i:%02d" % i, " b:", b, " c:",c)
            

    binFile.close()


# azimuth compress
def azimuthCompress(rangeCompressMat):
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
    plt.show()


def showFreqImg():
    y = np.load("tempMat.npy")
    # print("y.shape", y.shape)
    # [r, c] = y.shape
    # for index in range(r):
    #     fftY = fft(y[index,::])
    #     one = np.ones(fftY.shape)
    #     one[0:125] = np.zeros(125)
    #     fftY1 = fftY * one
    #     y2 = ifft(fftY1)
    #     y[index,::] = y2


    img = np.fliplr(np.flipud(np.abs(y[::3,::3])))
    (x1, y1) = img.shape
    sc = 128
    plt.figure(figsize=(sc*y1/x1, sc), dpi=128)
    plt.pcolor(img, vmin = 1, vmax = 2*10**8)
    plt.colorbar()
    plt.savefig("test.png")


if __name__ == "__main__":
    
    filePath = './data/archives/S1A_IW_RAW__0SDV_20210726T214231_20210726T214303_038954_0498A8_D3A7.SAFE/s1a-iw-raw-s-vv-20210726t214231-20210726t214303-038954-0498a8.dat'
    file0 = BinFile(filePath)

    # decode packets
    creator = SPCreator(file0)
    creator.createSpacekets()

    # 
    fileList0 = os.listdir('./data/%s/decode' % file0.polar)
    fileList0.sort()

    # generate image
    for name in fileList0:
        corrector = Corrector(file0.polar, name)
        corrector.correct()

        slcProcess = SLCProcessor(file0.polar, name)
        slcProcess.compress()

    # slcProcess = SLCProcessor()
    # slcProcess.compress("rangeLine_1552")


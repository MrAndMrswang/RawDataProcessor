import os


# 生成space packet
class SpacePacketDecoder:
    def __init__(self, filePath):
        self.binFile = open(filePath, 'rb')
        self.hCode = 0
        self.hCodeBitsSize = 0
        self.hCodeBitInterceptCnt = 0
        self.readHCodeBitCnt = 0
        self.bitRateCodeList = []
        self.thresholdIndexList = []
        
        size = os.path.getsize(filePath)
        print('open file size:', size)
    
    # Get Packet Data Length: number of octets in packet data field-1
    # Packet Data Field consists of Packet Secondary Header and User Data Field
    # Octet Offset [0, 6)
    def preparePacketPrimaryHeader(self):
        packetPrimaryHeader = self.getBytesFromBinFile(4)
        # get Packet Data Length, unit: Octets
        packetDataLength0 = self.getBytesFromBinFile(2)
        # showBinaryLength = '{:016b}'.format(int.from_bytes(packetDataLength, byteorder='big'))
        intpacketDataLength = int.from_bytes(packetDataLength0, byteorder='big')
        self.PacketDataLength = intpacketDataLength
        self.UserDataLength = intpacketDataLength - 62 + 1
        print("PacketDataLength:", self.PacketDataLength, " UserDataLength:", self.UserDataLength)
    

    def preparePacketSecondaryHeader(self):
        # Datation Service
        # Octet Offset [6, 12)
        datationService = self.getBytesFromBinFile(6)

        # Fixed Ancillary Data Field
        # Octet Offset [12, 26)
        fixedAncillaryDataField = self.getBytesFromBinFile(14)

        # Sub-commutation Ancillary Data Service Field
        # Octet Offset [26, 29)
        subCommutationAncillaryDataServiceField = self.getBytesFromBinFile(3)

        # Counters Service
        # Octet Offset [29, 37)
        countersService = self.getBytesFromBinFile(8)

        # Radar Configuration Support Service
        # Octet Offset [37, 65)
        radarConfigurationSupportService = self.getBytesFromBinFile(28)

        # Radar Sample Count Service
        # Octet Offset [65, 67)
        radarSampleCountService = self.getBytesFromBinFile(2)
        numberOfQuads = int.from_bytes(radarSampleCountService, byteorder='big')
        self.NumberOfQuads = numberOfQuads
        print("NumberOfQuads:", self.NumberOfQuads)

        # N/A
        # Octet Offset [67, 68)
        na = self.getBytesFromBinFile(1)
    

    def getBytesFromBinFile(self, numOfBytes):
        return self.binFile.read(numOfBytes)


    def interceptHCodeBits(self, num):
        while self.hCodeBitsSize < num:
            self.fillHCodeByBinFile()

        bits = self.hCode >> (self.hCodeBitsSize - num)
        # print("hCode:", '{:010b}'.format(self.hCode), " bits:", bits, " num:", num, " self.hCodeBitsSize:", self.hCodeBitsSize)
        self.hCodeBitInterceptCnt += num
        self.remainHCode(self.hCodeBitsSize - num)
        return bits


    def interceptHCodeFirstBit(self):
        return self.interceptHCodeBits(1)


    def fillHCodeByBinFile(self):
        hCode0 = int.from_bytes(self.getBytesFromBinFile(1), byteorder='big')
        self.hCode = self.hCode << 8
        self.hCode = self.hCode | hCode0
        self.hCodeBitsSize += 8
        self.readHCodeBitCnt += 8
        

    def remainHCode(self, num):
        mask = 0xffff >> (16 - num)
        self.hCode = mask & self.hCode
        self.hCodeBitsSize = num
        

    def processHCodeDummies(self):
        dummiesLength = 16 - self.hCodeBitInterceptCnt % 16
        if dummiesLength == 16:
            return
        # print("hCode:",self.hCode, " hCodeSize:", self.hCodeBitsSize, " dummiesLength:", dummiesLength, " self.readHCodeBitCnt:", self.readHCodeBitCnt, "self.hCodeBitInterceptCnt:", self.hCodeBitInterceptCnt)
        self.interceptHCodeBits(dummiesLength)

    def reconstructionFDBQA(self, signList, mCodeList):
        reslist0 = []
        for i in range(len(signList)):
            # sampleReconstruction(self, brc, thidx, sign, mCode)
            brcIndx = int(i/128)
            res = self.sampleReconstruction(
                    self.bitRateCodeList[brcIndx], 
                    self.thresholdIndexList[brcIndx], 
                    signList[i],
                    mCodeList[i])
            reslist0.append(res)

        return reslist0
            

    def prepareUserDataFiled(self):

        # decode IE Huffmann Codes 
        iESignList, iEMCodeList = self.getIEMCode()
        self.processHCodeDummies()
        
        # decode IO Huffmann Codes
        iOSignList, iOMCodeList = self.getIOorQOMCode()
        self.processHCodeDummies()

        # decode QE
        qESignList, qEMCodeList = self.getQEMCode()
        self.processHCodeDummies()

        # decode QO
        qOSignList, qOMCodeList = self.getIOorQOMCode()
        self.processHCodeDummies()

        self._iEValueList = self.reconstructionFDBQA(iESignList, iEMCodeList)
        self._iOValueList = self.reconstructionFDBQA(iOSignList, iOMCodeList)
        self._qEValueList = self.reconstructionFDBQA(qESignList, qEMCodeList)
        self._qOValueList = self.reconstructionFDBQA(qOSignList, qOMCodeList)

        print("Prepare All Data|HCodeIntercept:%d readHCodeBitCnt:%d" % (self.hCodeBitInterceptCnt, self.readHCodeBitCnt))
        
    @property
    def iEValueList(self):
        return self._iEValueList
    
    @property
    def iOValueList(self):
        return self._iOValueList

    @property
    def qEValueList(self):
        return self._qEValueList

    @property
    def qOValueList(self):
        return self._qOValueList


    def saveTHIDX(self, thidx):
        self.thresholdIndexList.append(thidx)
    
    def saveBRC(self, brc):
        self.bitRateCodeList.append(brc)
    
    def getIEMCode(self):
        signList = []
        mCodeList = []
        while(1):
            mCodeQuantity = 128
            if (self.NumberOfQuads - len(signList)) / 128 < 1:
                mCodeQuantity = self.NumberOfQuads - len(signList)

            bitRateCode = self.interceptHCodeBits(3)
            self.saveBRC(bitRateCode)

            if bitRateCode == 0:
                signList0, mCodeList0 = self.huffmanDecode4BRC0(mCodeQuantity)
                # print("NumberOfQuads:%d, signList0:%d" % (self.NumberOfQuads, len(signList)))
            # TODO: other BRC Algorithm
            else:
                print("Other BRC! %d" % bitRateCode)
            
            # print("hCode:", self.hCode, " hCodeSize:", self.hCodeBitsSize)
            signList += signList0
            mCodeList += mCodeList0
            if len(signList) >= self.NumberOfQuads:
                print("Already Get %d MCode! len signList is %d" % (self.NumberOfQuads, len(signList)))
                break
        return signList, mCodeList


    def getIOorQOMCode(self):
        signList = []
        mCodeList = []
        i = 0
        while(1):
            mCodeQuantity = 128
            if (self.NumberOfQuads - len(signList)) / 128 < 1:
                mCodeQuantity = self.NumberOfQuads - len(signList)

            bitRateCode = self.bitRateCodeList[i]
            if bitRateCode == 0:
                signList0, mCodeList0 = self.huffmanDecode4BRC0(mCodeQuantity)
                # print("NumberOfQuads:%d, signList0:%d" % (self.NumberOfQuads, len(signList)))
            # TODO: other BRC Algorithm
            else:
                print("Other BRC! %d" % bitRateCode)
            
            # print("hCode:", self.hCode, " hCodeSize:", self.hCodeBitsSize)
            signList += signList0
            mCodeList += mCodeList0
            i += 1

            if len(signList) >= self.NumberOfQuads:
                print("Already Get %d MCode! len signList is %d" % (self.NumberOfQuads, len(signList)))
                break
        return signList, mCodeList
    

    def getQEMCode(self):
        signList = []
        mCodeList = []
        i = 0
        while(1):
            mCodeQuantity = 128
            if (self.NumberOfQuads - len(signList)) / 128 < 1:
                mCodeQuantity = self.NumberOfQuads - len(signList)

            thidx0 = self.interceptHCodeBits(8)
            self.saveTHIDX(thidx0)

            bitRateCode = self.bitRateCodeList[i]
            if bitRateCode == 0:
                signList0, mCodeList0 = self.huffmanDecode4BRC0(mCodeQuantity)
                # print("NumberOfQuads:%d, signList0:%d" % (self.NumberOfQuads, len(signList)))
            # TODO: other BRC Algorithm
            else:
                print("Other BRC! %d" % bitRateCode)
            
            # print("hCode:", self.hCode, " hCodeSize:", self.hCodeBitsSize)
            signList += signList0
            mCodeList += mCodeList0
            i += 1

            if len(signList) >= self.NumberOfQuads:
                print("Already Get %d MCode! len signList is %d" % (self.NumberOfQuads, len(signList)))
                break
        return signList, mCodeList
        

    # Raw Data -> Huffmann Decoding, Get Sample Code
    # BRC = 0时
    # Binary => M-Code
    # 0         0
    # 10        1
    # 110       2
    # 111       3     
    def huffmanDecode4BRC0(self, mCodeQuantity):
        signList = []
        mCodeList = []

        # one BRC + 128 HCode
        for i in range(mCodeQuantity):
            mCode = -1
            sign = (-1) * self.interceptHCodeFirstBit()

            bit0 = self.interceptHCodeFirstBit()
            if bit0 == 0:
                mCode = 0
            else:
                bit0 = self.interceptHCodeFirstBit()
                if bit0 == 0:
                    mCode = 1
                else:
                    bit0 = self.interceptHCodeFirstBit()
                    if bit0 == 0:
                        mCode = 2
                    else:
                        mCode = 3

            if mCode == -1:
                print("ERROR|mCode is error!")
            # print("sign:", sign, " mCode:", mCode)
            signList.append(sign)
            mCodeList.append(mCode)
                       
        return signList, mCodeList
    
    def sampleReconstruction(self, brc, thidx, sign, mCode):
        res = 0
        thidxSimpleFlag = 0
        mCodeFlag = 0

        if brc == 0:
            thidxSimpleFlag = 3
            mCodeFlag = 3
        elif brc == 1:
            thidxSimpleFlag = 3
            mCodeFlag = 4
        elif brc == 2:
            thidxSimpleFlag = 5
            mCodeFlag = 6
        elif brc == 3:
            thidxSimpleFlag = 6
            mCodeFlag = 9
        elif brc == 4:
            thidxSimpleFlag = 8
            mCodeFlag = 15

        if thidx  <= thidxSimpleFlag:
            if mCode < mCodeFlag:
                res = sign * mCode
            else:
                bThidx = fDBQASimpleReconstructionParam[thidx][brc]
                res = sign * bThidx
                # print("bThidx:", bThidx)
        else: 
            nrl = normalisedReconstructionLevels[mCode][brc]
            sf = sigmaFactors[thidx]
            # print("nrl:", nrl, " sf:", sf)
            res = sign * nrl * sf
        
        return res


fDBQASimpleReconstructionParam = [[3,     4,     6,      9,     15   ],
                                  [3,     4,     6,      9,     15   ],
                                  [3.16,  4.08,  6,      9,     15   ],
                                  [3.53,  4.37,  6.15,   9,     15   ],
                                  [0,     0,     6.50,   9.36,  15   ],
                                  [0,     0,     6.88,   9.50,  15   ],
                                  [0,     0,     0,      10.1,  15.22],
                                  [0,     0,     0,      0,     15.50],
                                  [0,     0,     0,      0,     16.05]]

normalisedReconstructionLevels = [[0.3637, 0.3042, 0.2305, 0.1702, 0.1130],
                                  [1.0915, 0.9127, 0.6916, 0.5107, 0.3389],
                                  [1.8208, 1.5216, 1.1528, 0.8511, 0.5649],
                                  [2.6406, 2.1313, 1.6140, 1.1916, 0.7908],
                                  [0,      2.8426, 2.0754, 1.5321, 1.0167],
                                  [0,      0,      2.5369, 1.8726, 1.2428],
                                  [0,      0,      3.1191, 2.2131, 1.4687],
                                  [0,      0,      0,      2.5536, 1.6947],
                                  [0,      0,      0,      2.8942, 1.9206],
                                  [0,      0,      0,      3.3744, 2.1466],
                                  [0,      0,      0,      0,      2.3725],
                                  [0,      0,      0,      0,      2.5985],
                                  [0,      0,      0,      0,      2.8244],
                                  [0,      0,      0,      0,      3.0504],
                                  [0,      0,      0,      0,      3.2764],
                                  [0,      0,      0,      0,      3.6623]]

sigmaFactors = [0.00  , 0.63  , 1.25  , 1.88  , 2.51  , 3.13  , 3.76  , 4.39  ,
                5.01  , 5.64  , 6.27  , 6.89  , 7.52  , 8.15  , 8.77  , 9.40  ,
                10.03 , 10.65 , 11.28 , 11.91 , 12.53 , 13.16 , 13.79 , 14.41 ,
                15.04 , 15.67 , 16.29 , 16.92 , 17.55 , 18.17 , 18.80 , 19.43 ,
                20.05 , 20.68 , 21.31 , 21.93 , 22.56 , 23.19 , 23.81 , 24.44 ,
                25.07 , 25.69 , 26.32 , 26.95 , 27.57 , 28.20 , 28.83 , 29.45 ,
                30.08 , 30.71 , 31.33 , 31.96 , 32.59 , 33.21 , 33.84 , 34.47 ,
                35.09 , 35.72 , 36.35 , 36.97 , 37.60 , 38.23 , 38.85 , 39.48 ,
                40.11 , 40.73 , 41.36 , 41.99 , 42.61 , 43.24 , 43.87 , 44.49 ,
                45.12 , 45.75 , 46.37 , 47.00 , 47.63 , 48.25 , 48.88 , 49.51 ,
                50.13 , 50.76 , 51.39 , 52.01 , 52.64 , 53.27 , 53.89 , 54.52 ,
                55.15 , 55.77 , 56.40 , 57.03 , 57.65 , 58.28 , 58.91 , 59.53 ,
                60.16 , 60.79 , 61.41 , 62.04 , 62.98 , 64.24 , 65.49 , 66.74 ,
                68.00 , 69.25 , 70.50 , 71.76 , 73.01 , 74.26 , 75.52 , 76.77 ,
                78.02 , 79.28 , 80.53 , 81.78 , 83.04 , 84.29 , 85.54 , 86.80 ,
                88.05 , 89.30 , 90.56 , 91.81 , 93.06 , 94.32 , 95.57 , 96.82 ,
                98.08 , 99.33 , 100.58, 101.84, 103.09, 104.34, 105.60, 106.85,
                108.10, 109.35, 110.61, 111.86, 113.11, 114.37, 115.62, 116.87,
                118.13, 119.38, 120.63, 121.89, 123.14, 124.39, 125.65, 126.90,
                128.15, 129.41, 130.66, 131.91, 133.17, 134.42, 135.67, 136.93,
                138.18, 139.43, 140.69, 141.94, 143.19, 144.45, 145.70, 146.95,
                148.21, 149.46, 150.71, 151.97, 153.22, 154.47, 155.73, 156.98,
                158.23, 159.49, 160.74, 161.99, 163.25, 164.50, 165.75, 167.01,
                168.26, 169.51, 170.77, 172.02, 173.27, 174.53, 175.78, 177.03,
                178.29, 179.54, 180.79, 182.05, 183.30, 184.55, 185.81, 187.06,
                188.31, 189.57, 190.82, 192.07, 193.33, 194.58, 195.83, 197.09,
                198.34, 199.59, 200.85, 202.10, 203.35, 204.61, 205.86, 207.11,
                208.37, 209.62, 210.87, 212.13, 213.38, 214.63, 215.89, 217.14,
                218.39, 219.65, 220.90, 222.15, 223.41, 224.66, 225.91, 227.17,
                228.42, 229.67, 230.93, 232.18, 233.43, 234.69, 235.94, 237.19,
                238.45, 239.70, 240.95, 242.21, 243.46, 244.71, 245.97, 247.22,
                248.47, 249.73, 250.98, 252.23, 253.49, 254.74, 255.99, 255.99]

if __name__ == "__main__":

    filePath = '/home/chao/work/NNSFC/Program/RawDataProcessor/data/S1A_IW_RAW__0SDV_20220315T061928_20220315T062001_042328_050BC0_43C6.SAFE/s1a-iw-raw-s-vh-20220315t061928-20220315t062001-042328-050bc0.dat'
    decoder = SpacePacketDecoder(filePath)
    decoder.preparePacketPrimaryHeader()
    decoder.preparePacketSecondaryHeader()
    decoder.prepareUserDataFiled()
    # ReadFile()
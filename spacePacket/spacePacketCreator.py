import os

from utils.log import getLogger
from .reconstruction import sampleReconstruction 
from .radarConfigurationSupportService import RadarConfigurationSupportService

#
class SpacePacket:
    def __init__(self, binFile):
        self.binFile = binFile
        self.hCode = 0
        self.hCodeBitsSize = 0
        self.userDataCnt = 0
        self.bitRateCodeList = []
        self.thresholdIndexList = []
        self.huffmanDecodeFuncDict  = {
            0: self.huffmanDecodeCore4BRC0,
            1: self.huffmanDecodeCore4BRC1,
            2: self.huffmanDecodeCore4BRC2,
            3: self.huffmanDecodeCore4BRC3,
            4: self.huffmanDecodeCore4BRC4,
            }


        # space packet define
        self.packetPrimaryHeader = 0
        self.packetDataLength = 0 
        self.datationService = 0
        self.fixedAncillaryDataField = 0
        self.subCommutationAncillaryDataServiceField = 0
        self.countersService = 0
        self.radarSampleCountService = 0
        self.radarConfigurationSupportService = RadarConfigurationSupportService()


        self.SampleValueI = []
        self.sampleValueQ = []



    # Get Packet Data Length: number of octets in packet data field-1
    # Packet Data Field consists of Packet Secondary Header and User Data Field
    # Octet Offset [0, 6)
    def preparePacketPrimaryHeader(self):
        self.packetPrimaryHeader = self.getBytesFromBinFile(4)
        if len(self.packetPrimaryHeader) != 4:
            return False

        # get Packet Data Length, unit: Octets
        packetDataLength0 = self.getBytesFromBinFile(2)

        # showBinaryLength = '{:016b}'.format(int.from_bytes(packetDataLength0, byteorder='big'))
        self.packetDataLength = int.from_bytes(packetDataLength0, byteorder='big')
        str0 = ("packetDataLength=%d|packetDataLength%%4=%d") % (self.packetDataLength ,  (self.packetDataLength + 6 + 1) % 4)
        getLogger("spacePacketCreator").info(str0)


    def preparePacketSecondaryHeader(self):
        # Datation Service
        # Octet Offset [6, 12)
        self.datationService = self.getBytesFromBinFile(6)

        # Fixed Ancillary Data Field
        # Octet Offset [12, 26)
        self.parseFixedAncillaryDataField()

        # Sub-commutation Ancillary Data Service Field
        # Octet Offset [26, 29)
        self.subCommutationAncillaryDataServiceField = self.getBytesFromBinFile(3)

        # Counters Service
        # Octet Offset [29, 37)
        self.countersService = self.getBytesFromBinFile(8)

        # Radar Configuration Support Service
        # Octet Offset [37, 65)
        # self.parseRadarConfigurationSupportService()
        data0 = self.getBytesFromBinFile(28)
        self.radarConfigurationSupportService.parseData(data0)

        # Radar Sample Count Service
        # Octet Offset [65, 67)
        radarSampleCountService = self.getBytesFromBinFile(2)
        numberOfQuads = int.from_bytes(radarSampleCountService, byteorder='big')
        self.NumberOfQuads = numberOfQuads

        # N/A
        # Octet Offset [67, 68)
        na = self.getBytesFromBinFile(1)
    
    # 
    def parseFixedAncillaryDataField(self):
        syncMarker = self.getBytesFromBinFile(4)
        dataTakeID = self.getBytesFromBinFile(4)
        eccNumber = self.getBytesFromBinFile(1)
        testMode = self.getBytesFromBinFile(1)
        instrumentConfigurationID = self.getBytesFromBinFile(4)
        testMode_int = int.from_bytes(testMode, byteorder='big')
        str0 = ("testMode_int=%s") % ('{:08b}'.format(testMode_int))
        getLogger("spacePacketCreator").info(str0)

    #
    def isEcho(self):
        return self.radarConfigurationSupportService.signalType == 0

    def getBytesFromBinFile(self, numOfBytes):
        return self.binFile.read(numOfBytes)
    

    def prepareUserDataFiled(self):

        # decode IE Huffmann Codes 
        iESignList, iEMCodeList = self.getIEMCode()
        self.alignData(16)
        
        # decode IO Huffmann Codes
        iOSignList, iOMCodeList = self.getIOorQOMCode()
        self.alignData(16)

        # decode QE Huffmann Codes 
        qESignList, qEMCodeList = self.getQEMCode()
        self.alignData(16)

        # decode QO Huffmann Codes 
        qOSignList, qOMCodeList = self.getIOorQOMCode()
        self.alignData(16)

        # 2 filler octets may be padded to make overall Space Packet length a multiple of 4 octets
        self.alignData(32)

        iEValueList = self.reconstructionFDBQA(iESignList, iEMCodeList)
        iOValueList = self.reconstructionFDBQA(iOSignList, iOMCodeList)
        qEValueList = self.reconstructionFDBQA(qESignList, qEMCodeList)
        qOValueList = self.reconstructionFDBQA(qOSignList, qOMCodeList)

        for i in range(len(iEValueList)):
            self.SampleValueI += [iEValueList[i], iOValueList[i]]
            self.sampleValueQ += [qEValueList[i], qOValueList[i]]

        # print("SampleValueI len:", len(self.SampleValueI), " read bits:", self.userDataCnt/8)


    def interceptUserDataBits(self, num):
        while self.hCodeBitsSize < num:
            self.fillHCodeByBinFile()

        bits = self.hCode >> (self.hCodeBitsSize - num)
        self.userDataCnt += num
        self.remainHCode(self.hCodeBitsSize - num)
        return bits


    def interceptHCodeFirstBit(self):
        return self.interceptUserDataBits(1)


    def fillHCodeByBinFile(self):
        hCode0 = int.from_bytes(self.getBytesFromBinFile(1), byteorder='big')
        self.hCode = self.hCode << 8
        self.hCode = self.hCode | hCode0
        self.hCodeBitsSize += 8

        

    def remainHCode(self, num):
        mask = 0xffff >> (16 - num)
        self.hCode = mask & self.hCode
        self.hCodeBitsSize = num
        

    def alignData(self, bitsLength):
        dummiesLength = bitsLength - self.userDataCnt % bitsLength
        if dummiesLength == bitsLength:
            return
        self.interceptUserDataBits(dummiesLength)


    def reconstructionFDBQA(self, signList, mCodeList):
        reslist0 = []
        for i in range(len(signList)):
            # sampleReconstruction(self, brc, thidx, sign, mCode)
            brcIndx = int(i/128)
            res = sampleReconstruction(
                    self.bitRateCodeList[brcIndx], 
                    self.thresholdIndexList[brcIndx], 
                    signList[i],
                    mCodeList[i])
            reslist0.append(res)

        return reslist0
            

    def saveTHIDX(self, thidx):
        self.thresholdIndexList.append(thidx)
    

    def saveBRC(self, brc):
        self.bitRateCodeList.append(brc)
    

    def getIEMCode(self):
        signList = []
        mCodeList = []
        while(1):
            mCodeQuantity = 128
            if (self.NumberOfQuads - len(signList)) / mCodeQuantity < 1:
                mCodeQuantity = self.NumberOfQuads - len(signList)

            bitRateCode = self.interceptUserDataBits(3)
            self.saveBRC(bitRateCode)
            signList0, mCodeList0 = self.huffmanDecode(mCodeQuantity, bitRateCode)
            signList += signList0
            mCodeList += mCodeList0
            if len(signList) >= self.NumberOfQuads:
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
            signList0, mCodeList0 = self.huffmanDecode(mCodeQuantity, bitRateCode)
            
            # print("hCode:", self.hCode, " hCodeSize:", self.hCodeBitsSize)
            signList += signList0
            mCodeList += mCodeList0
            i += 1

            if len(signList) >= self.NumberOfQuads:
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

            thidx0 = self.interceptUserDataBits(8)
            self.saveTHIDX(thidx0)

            bitRateCode = self.bitRateCodeList[i]
            signList0, mCodeList0 = self.huffmanDecode(mCodeQuantity, bitRateCode)
            
            # print("hCode:", self.hCode, " hCodeSize:", self.hCodeBitsSize)
            signList += signList0
            mCodeList += mCodeList0
            i += 1

            if len(signList) >= self.NumberOfQuads:
                break
        return signList, mCodeList
        

  
    def huffmanDecode(self, mCodeQuantity, bitRateCode):
        signList = []
        mCodeList = []
        decodeFunc = self.huffmanDecodeFuncDict[bitRateCode]

        # 
        for i in range(mCodeQuantity):
            sign, mCode = decodeFunc()

            if mCode == -1:
                print("ERROR|mCode is error!")
            # print("sign:", sign, " mCode:", mCode)
            signList.append(sign)
            mCodeList.append(mCode)
                       
        return signList, mCodeList
    
    
    # Raw Data -> Huffmann Decoding, Get Sample Code
    # BRC = 0时
    # Binary => M-Code
    # 0         0
    # 10        1
    # 110       2
    # 111       3   
    def huffmanDecodeCore4BRC0(self):
        mCode = -1
        sign = (-1) * self.interceptHCodeFirstBit()
        
        # 0
        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 0
            return sign, mCode
        
        # 10
        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 1
            return sign, mCode

        # 110
        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 2
            return sign, mCode
        
        mCode = 3
        return sign, mCode
    

    def huffmanDecodeCore4BRC1(self):
        mCode = -1
        sign = (-1) * self.interceptHCodeFirstBit()
        
        # 0
        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 0
            return sign, mCode
        
        # 10
        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 1
            return sign, mCode

        # 110
        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 2
            return sign, mCode
        
        # 1110
        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 3
            return sign, mCode

        mCode = 4
        return sign, mCode


    def huffmanDecodeCore4BRC2(self):
        mCode = -1
        sign = (-1) * self.interceptHCodeFirstBit()
        
        # 0
        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 0
            return sign, mCode
        
        # 10
        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 1
            return sign, mCode

        # 110
        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 2
            return sign, mCode
        
        # 1110
        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 3
            return sign, mCode

        # 11110
        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 4
            return sign, mCode

        # 111110
        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 5
            return sign, mCode

        mCode = 6
        return sign, mCode


    def huffmanDecodeCore4BRC3(self):
        mCode = -1
        sign = (-1) * self.interceptHCodeFirstBit()
        
        # 0
        bit0 = self.interceptHCodeFirstBit()
        bit1 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 0
            return sign, mCode
        
        if bit0 == 0:
            if bit1 == 0:
                mCode = 0
                return sign, mCode
            else:
                mCode = 1
                return sign, mCode

        if bit0 == 1:
            if bit1 == 0:
                mCode = 2
                return sign, mCode

        # 11xxxxx
        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 3
            return sign, mCode
        
        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 4
            return sign, mCode

        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 5
            return sign, mCode

        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 6
            return sign, mCode

        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 7
            return sign, mCode

        bit0 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            mCode = 8
            return sign, mCode

        mCode = 9
        return sign, mCode


    def huffmanDecodeCore4BRC4(self):
        mCode = -1
        sign = (-1) * self.interceptHCodeFirstBit()
        
        # 0xxxxxx
        bit0 = self.interceptHCodeFirstBit()
        bit1 = self.interceptHCodeFirstBit()
        if bit0 == 0:
            if bit1 == 0:
                mCode = 0
                return sign, mCode
            else:
                bit2 = self.interceptHCodeFirstBit()
                if bit2 == 0:
                    mCode = 1
                else:
                    mCode = 2
                return sign, mCode
        
        bit2 = self.interceptHCodeFirstBit()
        # 10xxxxxxx
        if bit1 == 0:
            if bit2 == 0:
                mCode = 3
            else:
                mCode = 4
            return sign, mCode

        bit3 = self.interceptHCodeFirstBit()
        # 110xxxxxx
        if bit2 == 0:
            if bit3 == 0:
                mCode = 5
            else:
                mCode = 6
            return sign, mCode
        
        # 111xxxxxx
        if bit3 == 0:
            mCode = 7
            return sign, mCode

        bit4 = self.interceptHCodeFirstBit()
        # 1111xxxxx
        if bit4 == 0:
            mCode = 8
            return sign, mCode

        bit5 = self.interceptHCodeFirstBit()
        # 11111xxxx
        if bit5 == 0:
            mCode = 9
            return sign, mCode

        # 111111xxx
        bit6 = self.interceptHCodeFirstBit()
        bit7 = self.interceptHCodeFirstBit()
        if bit6 == 0:
            if bit7 == 0:
                mCode = 10
            else:
                mCode = 11
            return sign, mCode

        # 1111111xx
        bit8 = self.interceptHCodeFirstBit()
        if bit7 == 0:
            if bit8 == 0:
                mCode = 12
            else:
                mCode = 13
            return sign, mCode

        # 11111111x
        if bit8 == 0:
            mCode = 14
        else:
            mCode = 15
        return sign, mCode



class SpacePacketCreator:
    def __init__(self, filePath):
        self.binFile = open(filePath, 'rb')
        self.spacePackets = []
        size = os.path.getsize(filePath)
        getLogger("spacePacketCreator").info("open file size:" + str(size))
    

    def createSpacekets(self):

        readDataSize = 0
        i = 0
        while(1):
            getLogger("spacePacketCreator").info("space packet index=%d|readDataSize=%dMB|%dB" % (i, readDataSize/1024/1024, readDataSize))
            spacePacket = SpacePacket(self.binFile)

            # Packet Primary Header
            ok = spacePacket.preparePacketPrimaryHeader()
            if ok == False:
                break
            
            # Packet Secondary Header
            spacePacket.preparePacketSecondaryHeader()

            i += 1
            readDataSize += spacePacket.packetDataLength + 1 + 6
            # 
            if not spacePacket.isEcho():
                getLogger("spacePacketCreator").warning("index=%d|type:%d" % (i, spacePacket.radarConfigurationSupportService.signalType))
                self.binFile.read(spacePacket.packetDataLength - 61)
                continue

            # User Data Field
            spacePacket.prepareUserDataFiled()

            # validate
            # Space Packet Length = Multiple of 4 Octets
            self.spacePackets.append(spacePacket)



    
if __name__ == "__main__":
    filePath = '/home/chao/work/NNSFC/Program/RawDataProcessor/data/S1A_IW_RAW__0SDV_20220315T061928_20220315T062001_042328_050BC0_43C6.SAFE/s1a-iw-raw-s-vh-20220315t061928-20220315t062001-042328-050bc0.dat'
    creator = SpacePacketCreator(filePath)
    creator.createSpacekets()

    # ReadFile()

    
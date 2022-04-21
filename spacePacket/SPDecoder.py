from utils.log import getLogger

from .reconstruction import sampleReconstruction 
from .radarConfigurationSupportService import RadarConfigurationSupportService 

#
class SPDecoder:
    def __init__(self, binFile):
        self.binFile = binFile
        self.hCode = 0
        self.hCodeBitsSize = 0
        self.userDataCnt = 0
        self.rcss = RadarConfigurationSupportService()
        self.huffmanDecodeFuncDict = {
            0: self.huffmanDecodeCore4BRC0,
            1: self.huffmanDecodeCore4BRC1,
            2: self.huffmanDecodeCore4BRC2,
            3: self.huffmanDecodeCore4BRC3,
            4: self.huffmanDecodeCore4BRC4,
            }


    # Get Packet Data Length: number of octets in packet data field-1
    # Packet Data Field consists of Packet Secondary Header and User Data Field
    # Octet Offset [0, 6)
    def preparePacketPrimaryHeader(self, packet):
        packet.primaryHeader = self.getBytesFromBinFile(4)
        if len(packet.primaryHeader) != 4:
            return False

        # get Packet Data Length, unit: Octets
        packetDataLength0 = self.getBytesFromBinFile(2)

        # showBinaryLength = '{:016b}'.format(int.from_bytes(packetDataLength0, byteorder='big'))
        packet.packetDataLength = int.from_bytes(packetDataLength0, byteorder='big')
        str0 = ("packetDataLength=%d|all packetDataLength%%4=%d") % (packet.packetDataLength ,  (packet.packetDataLength + 6 + 1) % 4)
        getLogger("spacePacketCreator").info(str0)


    def preparePacketSecondaryHeader(self, packet):
        # Datation Service
        # Octet Offset [6, 12)
        packet.datationService = self.getBytesFromBinFile(6)

        # Fixed Ancillary Data Field
        # Octet Offset [12, 26)
        self.parseFixedAncillaryDataField(packet)

        # Sub-commutation Ancillary Data Service Field
        # Octet Offset [26, 29)
        packet.subCommutationAncillaryDataServiceField = self.getBytesFromBinFile(3)

        # Counters Service
        # Octet Offset [29, 37)
        packet.countersService = self.getBytesFromBinFile(8)

        # Radar Configuration Support Service
        # Octet Offset [37, 65)
        # self.parseRadarConfigurationSupportService()
        data0 = self.getBytesFromBinFile(28)
        self.rcss.parseData(data0, packet)

        # Radar Sample Count Service
        # Octet Offset [65, 67)
        radarSampleCountService = self.getBytesFromBinFile(2)
        numberOfQuads = int.from_bytes(radarSampleCountService, byteorder='big')
        packet.NumberOfQuads = numberOfQuads

        # N/A
        # Octet Offset [67, 68)
        na = self.getBytesFromBinFile(1)
    
    # 
    def parseFixedAncillaryDataField(self, packet):
        packet.syncMarker = self.getBytesFromBinFile(4)
        packet.dataTakeID = self.getBytesFromBinFile(4)
        packet.eccNumber = self.getBytesFromBinFile(1)
        packet.testMode = self.getBytesFromBinFile(1)
        packet.instrumentConfigurationID = self.getBytesFromBinFile(4)
        testMode_int = int.from_bytes(packet.testMode, byteorder='big')
        getLogger("spacePacketCreator").info(("testMode_int=%s") % ('{:08b}'.format(testMode_int)))


    def getBytesFromBinFile(self, numOfBytes):
        return self.binFile.read(numOfBytes)
    

    def prepareUserDataFiled(self, packet):
        # decode IE Huffmann Codes 
        iESignList, iEMCodeList = self.getIEMCode(packet)
        self.alignData(16)
        
        # decode IO Huffmann Codes
        iOSignList, iOMCodeList = self.getIOorQOMCode(packet)
        self.alignData(16)

        # decode QE Huffmann Codes 
        qESignList, qEMCodeList = self.getQEMCode(packet)
        self.alignData(16)

        # decode QO Huffmann Codes 
        qOSignList, qOMCodeList = self.getIOorQOMCode(packet)
        self.alignData(16)

        # 2 filler octets may be padded to make overall Space Packet length a multiple of 4 octets
        self.alignData(32)

        iEValueList = self.reconstructionFDBQA(packet, iESignList, iEMCodeList)
        # print("iEValueList:", iEValueList[0:10])
        iOValueList = self.reconstructionFDBQA(packet, iOSignList, iOMCodeList)
        qEValueList = self.reconstructionFDBQA(packet, qESignList, qEMCodeList)
        qOValueList = self.reconstructionFDBQA(packet, qOSignList, qOMCodeList)

        for i in range(len(iEValueList)):
            packet.ISampleValue += [iEValueList[i], iOValueList[i]]
            packet.QSampleValue += [qEValueList[i], qOValueList[i]]


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


    def reconstructionFDBQA(self, packets, signList, mCodeList):
        reslist0 = []
        for i in range(len(signList)):
            # sampleReconstruction(self, brc, thidx, sign, mCode)
            brcIndx = int(i/128)
            res = sampleReconstruction(
                    packets.bitRateCodeList[brcIndx], 
                    packets.thresholdIndexList[brcIndx], 
                    signList[i],
                    mCodeList[i])
            reslist0.append(res)

        return reslist0
            

    def getIEMCode(self, packet):
        signList = []
        mCodeList = []
        while(1):
            mCodeQuantity = 128
            if (packet.NumberOfQuads - len(signList)) / mCodeQuantity < 1:
                mCodeQuantity = packet.NumberOfQuads - len(signList)
            bitRateCode = self.interceptUserDataBits(3)
            packet.saveBRC(bitRateCode)
            signList0, mCodeList0 = self.huffmanDecode(mCodeQuantity, bitRateCode)
            signList += signList0
            mCodeList += mCodeList0
            if len(signList) >= packet.NumberOfQuads:
                break
        return signList, mCodeList


    def getIOorQOMCode(self, packet):
        signList = []
        mCodeList = []
        i = 0
        while(1):
            mCodeQuantity = 128
            if (packet.NumberOfQuads - len(signList)) / 128 < 1:
                mCodeQuantity = packet.NumberOfQuads - len(signList)

            bitRateCode = packet.bitRateCodeList[i]
            signList0, mCodeList0 = self.huffmanDecode(mCodeQuantity, bitRateCode)
            
            # print("hCode:", self.hCode, " hCodeSize:", self.hCodeBitsSize)
            signList += signList0
            mCodeList += mCodeList0
            i += 1

            if len(signList) >= packet.NumberOfQuads:
                break
        return signList, mCodeList


    def getQEMCode(self, packet):
        signList = []
        mCodeList = []
        i = 0
        while(1):
            mCodeQuantity = 128
            if (packet.NumberOfQuads - len(signList)) / 128 < 1:
                mCodeQuantity = packet.NumberOfQuads - len(signList)

            thidx0 = self.interceptUserDataBits(8)
            packet.saveTHIDX(thidx0)

            bitRateCode = packet.bitRateCodeList[i]
            signList0, mCodeList0 = self.huffmanDecode(mCodeQuantity, bitRateCode)
            
            # print("hCode:", self.hCode, " hCodeSize:", self.hCodeBitsSize)
            signList += signList0
            mCodeList += mCodeList0
            i += 1

            if len(signList) >= packet.NumberOfQuads:
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

            signList.append(sign)
            mCodeList.append(mCode)
            # getLogger("spacePacketCreator").info("huffmanDecode|sign=%d, code=%d" % (sign, mCode))
                       
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
        sign = (-1) ** self.interceptHCodeFirstBit()
        
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
        sign = (-1) ** self.interceptHCodeFirstBit()
        
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
        sign = (-1) ** self.interceptHCodeFirstBit()
        
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
        sign = (-1) ** self.interceptHCodeFirstBit()
        
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
        sign = (-1) ** self.interceptHCodeFirstBit()
        
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
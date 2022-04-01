import os



# BAQDecode, Sample Value Reconstruction, Get Sample Value
# def BAQDecode():

# get SValue
# def getSValue(brc, thidx):
#     if brc == 0:
#         if thidx


def ReadFile():
    # filePath = '/home/chao/work/NNSFC/Program/RawDataProcessor/data/S1A_IW_RAW__0SDV_20220315T061928_20220315T062001_042328_050BC0_43C6.SAFE/s1a-iw-raw-s-vh-20220315t061928-20220315t062001-042328-050bc0-annot.dat'
    filePath = '/home/chao/work/NNSFC/Program/RawDataProcessor/data/S1A_IW_RAW__0SDV_20220315T061928_20220315T062001_042328_050BC0_43C6.SAFE/s1a-iw-raw-s-vh-20220315t061928-20220315t062001-042328-050bc0.dat'
    # NQ = 2863
    # IE Huffmann BRC = 000
    binFile = open(filePath, 'rb')
    size = os.path.getsize(filePath)
    for i in range(90):
        data = binFile.read(1)
        if i < 5:
            print("data:", data)
        # os.sys.stdout.buffer.write(data)
        # r_int = int.from_bytes(data, byteorder='big')  #将 byte转化为 int
        # b = '{:08b}'.format(r_int)
        # c = '{:08b}'.format(data >> 2)
        # if i == 1:
        #     print("i:%02d" % i, " b:", b, " c:",c)
            

    binFile.close()

class SpacePacketDecoder:
    def __init__(self, filePath):
        self.binFile = open(filePath, 'rb')
        self.hCode = 0
        self.hCodeBitsSize = 0
        self.hCodeInterceptCnt = 0
        self.readHCodeCnt = 0
        self.bitRateCodeList = []
        self.thresholdIndexList= []
        
        size = os.path.getsize(filePath)
        print('open file size:', size)
    
    # Get Packet Data Length: number of octets in packet data field -1
    # Packet Data Field consists of Packet Secondary Header and User Data Field
    # Octet Offset [0, 6)
    def preparePacketPrimaryHeader(self):
        packetPrimaryHeader = self.getBytesFromBinFile(4)
        # get Packet Data Length
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
        self.hCodeInterceptCnt += num
        self.remainHCode(self.hCodeBitsSize - num)
        return bits


    def interceptHCodeFirstBit(self):
        return self.interceptHCodeBits(1)


    def fillHCodeByBinFile(self):
        hCode0 = int.from_bytes(self.getBytesFromBinFile(1), byteorder='big')
        self.hCode = self.hCode << 8
        self.hCode = self.hCode | hCode0
        self.hCodeBitsSize += 8
        self.readHCodeCnt += 8
        


    def remainHCode(self, num):
        mask = 0xffff >> (16 - num)
        self.hCode = mask & self.hCode
        self.hCodeBitsSize = num
        

    def processHCodeDummies(self):
        dummiesLength = 16 - self.hCodeInterceptCnt % 16
        if dummiesLength == 16:
            return
        print("hCode:",self.hCode, " hCodeSize:", self.hCodeBitsSize, " dummiesLength:", dummiesLength, " self.readHCodeCnt:", self.readHCodeCnt, "self.hCodeInterceptCnt:", self.hCodeInterceptCnt)
        self.interceptHCodeBits(dummiesLength)

    def prepareUserDataFiled(self):

        # decode IE Huffmann Codes 
        iESignList, iEMCodeList = self.decodeIEHuffmannCodes()
        self.processHCodeDummies()

        # decode IO Huffmann Codes
        iOSignList, iOMCodeList = self.decodeIOorQOHuffmannCodes()
        self.processHCodeDummies()

        # decode QE
        qESignList, qEMCodeList = self.decodeQEHuffmannCodes()
        self.processHCodeDummies()

        # decode QO
        qOSignList, qOMCodeList = self.decodeIOorQOHuffmannCodes()
        self.processHCodeDummies()


    def saveTHIDX(self, thidx):
        self.thresholdIndexList.append(thidx)
    
    def saveBRC(self, brc):
        self.bitRateCodeList.append(brc)
    
    def decodeIEHuffmannCodes(self):
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


    def decodeIOorQOHuffmannCodes(self):
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
    

    def decodeQEHuffmannCodes(self):
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


if __name__ == "__main__":

    filePath = '/home/chao/work/NNSFC/Program/RawDataProcessor/data/S1A_IW_RAW__0SDV_20220315T061928_20220315T062001_042328_050BC0_43C6.SAFE/s1a-iw-raw-s-vh-20220315t061928-20220315t062001-042328-050bc0.dat'
    decoder = SpacePacketDecoder(filePath)
    decoder.preparePacketPrimaryHeader()
    decoder.preparePacketSecondaryHeader()
    decoder.prepareUserDataFiled()
    # ReadFile()
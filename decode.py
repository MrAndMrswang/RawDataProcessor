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

    def prepareUserDataFiled(self):
        # decode IE Huffmann Codes 
        for i in range(1):
            byte0 = self.getBytesFromBinFile(1)
            firstByte = int.from_bytes(byte0, byteorder='big')
            bitRateCode = firstByte >> 5
            showBinaryFirstByte = '{:08b}'.format(firstByte)
            print("showBinaryFirstByte:", showBinaryFirstByte, " bitRateCode:", bitRateCode, " firstByte:", firstByte)
            
            hCode = firstByte & 0b00011111
            hCodeBitsSize = 5
            # showBinaryHCode = '{:08b}'.format(hCode)
            # print("showBinaryHCode:", showBinaryHCode)

            signList, mCodeList = self.huffmanDecode(bitRateCode, hCode, hCodeBitsSize)

                
    def huffmanDecode(self, bitRateCode, hCode, hCodeBitsSize):
        if bitRateCode == 0:
                signList, mCodeList = self.huffmanDecode4BRC0(hCode, hCodeBitsSize)
        return signList, mCodeList
            

    # Raw Data -> Huffmann Decoding, Get Sample Code
    # BRC = 0时
    # Binary => M-Code
    # 0         0
    # 10        1
    # 110       2
    # 111       3     
    def huffmanDecode4BRC0(self, hCode, hCodeBitsSize):
        signList = []
        mCodeList = []
        for i in range(130):
            if hCodeBitsSize < 4:
                newByte0 = int.from_bytes(self.getBytesFromBinFile(1), byteorder='big')
                # print("newByte0:", '{:08b}'.format(newByte0))
                hCode = hCode << 8
                hCode = hCode | newByte0
                hCodeBitsSize += 8

            sign = 0
            mCode = -1
            mCodeLength = -1
            signFlag = (1 << hCodeBitsSize - 1)
            if hCode & signFlag == signFlag:
                sign = -1
            else:
                sign = 1

            haffmannOffset = (hCodeBitsSize - 1 - 3)

            haffmannMask0 = 0b100 << haffmannOffset
            haffmannCode0 = 0
            
            haffmannMask1 = 0b110 << haffmannOffset
            haffmannCode1 = 0b100 << haffmannOffset

            haffmannMask2 = 0b111 << haffmannOffset
            haffmannCode2 = 0b110 << haffmannOffset

            haffmannMask3 = haffmannMask2
            haffmannCode3 = 0b111 << haffmannOffset

            if hCode & haffmannMask0 == haffmannCode0:
                mCode = 0
                mCodeLength = 1
            if hCode & haffmannMask1 == haffmannCode1:
                mCode = 1
                mCodeLength = 2
            if hCode & haffmannMask2 == haffmannCode2:
                mCode = 2
                mCodeLength = 3
            if hCode & haffmannMask3 == haffmannCode3:
                mCode = 3
                mCodeLength = 3

            if mCode == -1 or sign == 0:
                print("ERROR|mCode is error!")
            # print("sign:", sign, " mCode:", mCode, " mCodeLength:", mCodeLength)
            hCodeBitsSize -= (1 + mCodeLength)
            mask = 0xffff >> (16 - hCodeBitsSize)
            hCode = mask & hCode
            mCodeList.append(mCode)
            signList.append(sign)
            print("list len:", len(mCodeList))
        return signList, mCodeList


if __name__ == "__main__":

    filePath = '/home/chao/work/NNSFC/Program/RawDataProcessor/data/S1A_IW_RAW__0SDV_20220315T061928_20220315T062001_042328_050BC0_43C6.SAFE/s1a-iw-raw-s-vh-20220315t061928-20220315t062001-042328-050bc0.dat'
    decoder = SpacePacketDecoder(filePath)
    decoder.preparePacketPrimaryHeader()
    decoder.preparePacketSecondaryHeader()
    decoder.prepareUserDataFiled()
    # ReadFile()
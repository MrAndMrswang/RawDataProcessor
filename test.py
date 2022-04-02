import os
from decode import SpacePacketDecoder


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

if __name__ == "__main__":

    filePath = '/home/chao/work/NNSFC/Program/RawDataProcessor/data/S1A_IW_RAW__0SDV_20220315T061928_20220315T062001_042328_050BC0_43C6.SAFE/s1a-iw-raw-s-vh-20220315t061928-20220315t062001-042328-050bc0.dat'
    decoder = SpacePacketDecoder(filePath)
    res = decoder.sampleReconstruction(2, 239, 1, 5)
    print("res:", res)

    res = decoder.sampleReconstruction(3, 3, -1, 9)
    print("res:", res)

    res = decoder.sampleReconstruction(3, 5, -1, 9)
    print("res:", res)


    # ReadFile()
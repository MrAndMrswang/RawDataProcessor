import os


# Raw Data -> Huffmann Decoding, Get Sample Code
# def HuffmanDecode():

# BAQDecode, Sample Value Reconstruction, Get Sample Value
# def BAQDecode():


def ReadFile():
    # filePath = '/home/chao/work/NNSFC/Program/RawDataProcessor/data/S1A_IW_RAW__0SDV_20220315T061928_20220315T062001_042328_050BC0_43C6.SAFE/s1a-iw-raw-s-vh-20220315t061928-20220315t062001-042328-050bc0-annot.dat'
    filePath = '/home/chao/work/NNSFC/Program/RawDataProcessor/data/S1A_IW_RAW__0SDV_20220315T061928_20220315T062001_042328_050BC0_43C6.SAFE/s1a-iw-raw-s-vh-20220315t061928-20220315t062001-042328-050bc0.dat'
    binFile = open(filePath, 'rb')
    size = os.path.getsize(filePath)
    for i in range(90):
        data = binFile.read(1)
        # os.sys.stdout.buffer.write(data)
        r_int = int.from_bytes(data, byteorder='big')  #将 byte转化为 int
        b = '{:08b}'.format(r_int)
        if i >= 65 or (i > 35 and i <38):
            print("i:%02d" % i, " b:", b)
            # print('data:', data, ' bin:', bin(data))

    binFile.close()

if __name__ == "__main__":
    ReadFile()
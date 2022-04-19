from http.client import NOT_FOUND
from numpy import NaN
from utils.log import getLogger
import math

# RadarConfigurationSupportService
# Octet Offset [37, 65)
class RadarConfigurationSupportService:
    def __init__(self):
        self.fref = 37.53472224 # MHz
        

    # Sampling Frequency fdec after Decimation [MHz]
    def getSamplingFrequency(self, data):
        # prefix
        list0 = [3, 8/3, NaN, 20/9, 16/9, 3/2, 4/3, 2/3, 12/7, 5/4, 6/13, 16/11]
        res = list0[data] * self.fref
        getLogger("verbose").info(("SamplingFrequency=%d") % data)
        return res


    # calc Tx Pulse Ramp Rate
    def getTXPRR(self, data):
        sign = data[0] >> 7
        value = bytes([data[0] & 0b01111111, data[1]])
        temp = int.from_bytes(value, byteorder='big')
        txprr = math.pow(-1, sign) * temp * (math.pow(self.fref, 2) / math.pow(2, 21))
        return txprr


    # TXPSFcode
    def getTXPSF(self, data):
        sign0 = data[0] >> 7
        value = bytes([data[0] & 0b01111111, data[1]])
        temp = int.from_bytes(value, byteorder='big')
        txpsf = self.TXPRR / (4 * self.fref) + math.pow(-1, sign0) * temp * self.fref / math.pow(2, 14)
        return txpsf
     

     # TXPL 
    def getTXPL(self, data):
        value = int.from_bytes(data, byteorder='big')
        txpl = value / self.fref # us
        return txpl


    def parseData(self, data):
        self.errorFlag = data[0] >> 7
        self.BAQMode = data[0] & 0b00011111

        # BAQ Block Length
        self.baqBlockLength = data[1]

        # Range Decimation
        self.SamplingFrequencyAfterDecimation = self.getSamplingFrequency(data[3])

        # Tx Pulse Ramp Rate [42, 44)
        self.TXPRR = self.getTXPRR(data[5:7])

        # Tx Pulse Start Frequency [44, 46)
        self.TXPSF = self.getTXPSF(data[7:9])

        # Tx Pulse Length [46, 49)
        self.TXPL = self.getTXPL(data[9:12])
        
        # Sampling Window Start Time [53, 56)
        self.SWST = int.from_bytes(data[16:19], byteorder='big')

        # Sampling Window Length [56, 59)
        self.SWL = int.from_bytes(data[19:22], byteorder='big')


        # SAS SSB Message [59, 62]
        # sasSSBMessage 

        # SES SSB Data 
        # calMode 

        # Signal Type
        self.signalType = data[26] >> 4

        # Swath Number
        self.swathNumber = data[27]

        getLogger("spacePacketCreator").info(
            ("errorFlag=%s|BAQMode=%d|baqBlockLength=%d|swst=%d|swl=%d|type=%d|swathNumber=%d|TXPL=%f|TXPSF=%f|FDec=%f") % 
            (self.errorFlag, self.BAQMode, self.baqBlockLength, self.SWST, self.SWL, self.signalType, self.swathNumber, self.TXPL, self.TXPSF, self.SamplingFrequencyAfterDecimation)
        )

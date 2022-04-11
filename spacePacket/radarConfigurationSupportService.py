from utils.log import getLogger

# RadarConfigurationSupportService
# Octet Offset [37, 65)
class RadarConfigurationSupportService:
    def __init__(self) -> None:
        pass
        
    def parseData(self, data):
        self.errorFlag = data[0] >> 7
        self.BAQMode = data[0] & 0b00011111

        # BAQ Block Length
        self.baqBlockLength = data[1]

        # [39, 53)
        
        # Sampling Window Start Time [53, 56)
        self.swst = int.from_bytes(data[16:19], byteorder='big')

        # Sampling Window Length [56, 59)
        self.swl = int.from_bytes(data[19:22], byteorder='big')


        # SAS SSB Message [59, 62]
        # sasSSBMessage 

        # SES SSB Data 
        # calMode 

        # Signal Type
        self.signalType = data[26] >> 4

        # Swath Number
        self.swathNumber = data[27]

        getLogger("spacePacketCreator").info(
            ("errorFlag=%s|BAQMode=%d|baqBlockLength=%d|swst=%d|swl=%d|type=%d|swathNumber=%d") % 
            (self.errorFlag, self.BAQMode, self.baqBlockLength, self.swst, self.swl, self.signalType, self.swathNumber)
        )

from .board_2x4hd import *

class BoardDDRC24(Board2x4HD):
    """ Extensions for Dirac version of 2x4HD """

    def __init__(self, transport):
        if (transport == "usbhid"):
            self._transport = TransportUSBHID(0x2752, 0x0044)
        else:
            super().__init__(transport)

    def getDiracStatus(self):
        # Send Dirac status check command
        resp = self._transport.write([0x05, 0xff, 0xe0, 0x01])
        # Validity checking
        if (resp[:3] != [0x05, 0xff, 0xe0]) or not (resp[3] in [0x00, 0x01]):
            raise RuntimeError("Received unexpected response: " + str(resp))
        # Return as boolean, 0x01 for off 0x00 for on (bypass?)
        return (resp[3] == 0x00)

    def setDiracStatus(self, status):
        # Send dirac command, 0x01 for off 0x00 for on (bypass?)
        self._transport.write([0x3f, 0x00 if status else 0x01])


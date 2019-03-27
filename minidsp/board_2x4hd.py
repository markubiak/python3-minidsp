from .transport_echo import *
from .transport_usbhid import *

# Interesting note: responses to set commands return length 1
# of the command used to set whatever value it was. However,
# the following bytes do contain the new values. Look into this.

class Board2x4HD():
    """ Commands for 2x4HD """

    def __init__(self, transport):
        if (transport == "usbhid"):
            self._transport = TransportUSBHID(0x2752, 0x0011)
        elif (transport == "echo"):
            self._transport = TransportEcho()
        else:
            raise RuntimeError("Provided transport " + transport + " is not a valid option")

    def _masterStatus(self):
        # Send master status check command
        resp = self._transport.write([0x05, 0xff, 0xda, 0x02])
        # Validity checking
        if (resp[:3] != [0x05, 0xff, 0xda]) or not (resp[4] in [0x00, 0x01]):
            raise RuntimeError("Received unexpected response: " + str(resp))
        # Return results as a tuple
        return {"volume": resp[3]*-0.5, "mute": (resp[4] == 0x01)}

    def getMute(self):
        # Get mute from master status
        return self._masterStatus()["mute"]

    def setMute(self, mute):
        # Send mute command
        self._transport.write([0x17, 0x01 if mute else 0x00])

    def getVolume(self):
        # Get volume from master status
        return self._masterStatus()["volume"]

    def setVolume(self, volume):
        # Integrity check
        if (volume > 0) or (volume < -127.5):
            raise RuntimeError("Volume out of bounds. Range: -127.5 to 0 (db)")
        # Send volume command
        self._transport.write([0x42, round(-2*volume)])

    def getInputSource(self):
        # Send input source check command
        resp = self._transport.write([0x05, 0xff, 0xd9, 0x01])
        # Validity checking
        if (resp[:3] != [0x05, 0xff, 0xd9]) or not (resp[3] in [0x00, 0x01, 0x02]):
            raise RuntimeError("Received unexpected response: " + str(resp))
        # Return the source string
        sources = ["analog", "toslink", "usb"]
        return sources[resp[3]]

    def setInputSource(self, source):
        # Integrity check
        if not (source in ["analog", "toslink", "usb"]):
            raise RuntimeError("Invalid input source provided")
        # Send input change command
        sources = {"analog": 0x00, "toslink": 0x01, "usb": 0x02}
        self._transport.write([0x34, sources[source]])

    def getConfig(self):
        # Send config check command
        resp = self._transport.write([0x05, 0xff, 0xd8, 0x01])
        # Validity checking
        if (resp[:3] != [0x05, 0xff, 0xd8]) or not (resp[3] in [0x00, 0x01, 0x02, 0x03]):
            raise RuntimeError("Received unexpected response: " + str(resp))
        # Return the source index (1-indexed)
        return resp[3] + 1

    def setConfig(self, config):
        # Integrity check
        if (config < 1) or (config > 4):
            raise RuntimeError("Config index out of range (should be 1-4)")
        # Send the config change command
        self._transport.write([0x25, config-1, 0x02])
        self._transport.write([0x05, 0xff, 0xe5, 0x01])
        self._transport.write([0x05, 0xff, 0xe0, 0x01])
        self._transport.write([0x05, 0xff, 0xda, 0x02])

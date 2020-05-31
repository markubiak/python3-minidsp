import struct
from .transport_echo import *
from .transport_usbhid import *

# Interesting note: responses to set commands return length 1
# of the command used to set whatever value it was. However,
# the following bytes do contain the new values. Look into this.


class Board2x4HD:
    """ Commands for 2x4HD """

    def __init__(self, transport):
        if transport == "usbhid":
            self._transport = TransportUSBHID(0x2752, 0x0011)
        elif transport == "echo":
            self._transport = TransportEcho()
        else:
            raise RuntimeError(
                "Provided transport " + transport + " is not a valid option"
            )

    def _masterStatus(self):
        status = {}
        # Send master status check command
        resp = self._transport.write([0x05, 0xFF, 0xDA, 0x02])
        # sometimes we get back other stuff from the card, and have to get past them
        # before we can get what we want...
        tries = 1
        while resp[:3] != [0x05, 0xFF, 0xDA]:
            if tries > 10:
                raise RuntimeError(
                    "Tried >10 times to get a valid response to master status! Crashing!"
                )
            # some known values that often come back are
            # ['0x5', '0xff', '0xd9', '0x02']
            # d9 is switching source; 02 is for example the usb input, so might as well process those
            if resp and (len(resp) > 2) and resp[2] == "0xd9":
                # throw it in just to be nice so we don't have to do it later
                status["source"] = ["analog", "toslink", "usb"][resp[3]]
            # try again
            tries += 1
            resp = self._transport.write([0x05, 0xFF, 0xDA, 0x02])

        # if we've made it here, some valid volume/mute information is likely...
        # and resp starts with [0x05, 0xFF, 0xDA]
        if resp[4] not in [0x00, 0x01]:
            raise RuntimeError(
                "Received unexpected response: bad mute value " + str(resp)
            )
        status["volume"] = resp[3] * -0.5
        status["mute"] = resp[4] == 0x01
        # add status
        if "source" not in status:
            status["source"] = self.getInputSource()
        return status

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
        self._transport.write([0x42, round(-2 * volume)])

    def getInputSource(self):
        # Send input source check command
        resp = self._transport.write([0x05, 0xFF, 0xD9, 0x01])
        # Validity checking
        tries = 1
        while resp[:3] != [0x05, 0xFF, 0xD9]:
            if tries > 10:
                raise RuntimeError(
                    "Tried >10 times to get a valid response to inputSource! Crashing!"
                )
            # could log what we DO get back here, but don't have a place to do that right now...
            resp = self._transport.write([0x05, 0xFF, 0xD9, 0x01])

        # if we've made it here, some valid source information is likely...
        # and resp starts with [0x05, 0xFF, 0xD9]
        if resp[3] not in [0x00, 0x01, 0x02]:
            raise RuntimeError(
                "Received unexpected response: bad source value " + str(resp)
            )
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
        resp = self._transport.write([0x05, 0xFF, 0xD8, 0x01])
        # Validity checking
        if (resp[:3] != [0x05, 0xFF, 0xD8]) or not (
            resp[3] in [0x00, 0x01, 0x02, 0x03]
        ):
            raise RuntimeError("Received unexpected response: " + str(resp))
        # Return the source index (1-indexed)
        return resp[3] + 1

    def setConfig(self, config):
        # Integrity check
        if (config < 1) or (config > 4):
            raise RuntimeError("Config index out of range (should be 1-4)")
        # Send the config change command
        self._transport.write([0x25, config - 1, 0x02])
        self._transport.write([0x05, 0xFF, 0xE5, 0x01])
        self._transport.write([0x05, 0xFF, 0xE0, 0x01])
        self._transport.write([0x05, 0xFF, 0xDA, 0x02])

    def getLevels(self):
        # get input levels on the DSP right now.
        # adapted from https://github.com/mrene/node-minidsp/
        command = [0x14, 0x00, 0x44, 0x02]
        resp = self._transport.write(command)
        # Validity checking
        if resp[:3] != [0x14, 0x00, 0x44]:
            raise RuntimeError("Received unexpected response: " + str(resp))
        # current levels are in the response in two 32bit low-endian floats
        # at index 3-7 and 8-11 inclusive; so unpack two nums...
        # no rounding or anything, so if sending down a json wire or something
        # you might want to trim
        return struct.unpack("<ff", bytes(resp[3:11]))

    def _setInputGain(self, input=0, gain=0):
        # input either 0 or 1; gain from -127.5 to +12
        if (gain > 12) or (gain < -127.5):
            raise RuntimeError("Gain out of bounds. Range: -127.5 to 12 (db)")

        if input not in (0, 1):
            raise RuntimeError("input should be either 0 or 1")
        # again, this is adapted from https://github.com/mrene/node-minidsp/
        # the node code has that last byte either at 0x1A or 0x1B, depending on input, so...
        command = [0x13, 0x80, 0x0, 0x1A + input]

        # pack the gain value into a little-endian 32bit bytes string
        # and add those 4 bytes to the command
        command += list(struct.pack("<f", gain))

        resp = self._transport.write(command)
        return resp

    def setGain(self, gain):
        # set input gain for both input channels; use the _setInputGain to set individual ones
        self._setInputGain(0, gain)
        self._setInputGain(1, gain)

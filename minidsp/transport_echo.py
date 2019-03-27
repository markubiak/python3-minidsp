class TransportEcho:
    """ Extremely simple class primarily for debugging """

    def __init__(self):
        print("TransportEcho init")

    def write(self, command):
        print("write to device:", [hex(x) for x in command])
        if (command[0] == 0x05):
            command[3] = 0x00
            command.append(0x00)
            return command
        else:
            return [command[0]]


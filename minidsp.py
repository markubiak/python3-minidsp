import argparse

import minidsp

boards = ['2x4HD', 'DDRC24']
controls = ['volume', 'mute', 'input', 'config', 'dirac']

def main():
    # argparse setup
    parser = argparse.ArgumentParser(
            description="Command and control for various MiniDSP boards")
    parser.add_argument('board', metavar='board', type=str,
            choices=boards,
            help="Board selection (" + ", ".join(boards) + ")")
    parser.add_argument('action', metavar='action', type=str,
            choices=['get', 'set'],
            help="Action (get, set)")
    parser.add_argument('control', type=str,
            help="Control (" + ", ".join(controls) + ")")
    parser.add_argument('value', type=str, nargs='?',
            help="Value to set, if action is 'set'")
    parser.add_argument('-t', '--transport', type=str,
            choices=['usbhid','echo'], default='usbhid',
            help="Transport method to use")
    args = parser.parse_args()

    # invalid configuration checking
    if args.action == 'set' and args.value is None:
        parser.error("A value must be provided when the action is 'set'")
    if args.board != 'DDRC24' and args.control == 'dirac':
        parser.error("Dirac control only applicable for DDRC24")

    # setup the board
    board = None
    if args.board == '2x4HD':
        board = minidsp.board_2x4hd.Board2x4HD(args.transport)
    elif args.board == 'DDRC24':
        board = minidsp.board_ddrc24.BoardDDRC24(args.transport)

    if args.action == 'get':
        if args.control == 'volume':
            print("Volume:", board.getVolume(), "dB")
        elif args.control == 'mute':
            print("Muted" if board.getMute() else "Unmuted")
        elif args.control == 'input':
            print(board.getInputSource())
        elif args.control == 'config':
            print("Config", board.getConfig())
        elif args.control == 'dirac':
            print("Dirac on" if board.getDiracStatus() else "Dirac off")
    elif args.action == 'set':
        if args.control == 'volume':
            try:
                volFloat = float(args.value)
            except:
                parser.error("Volume must be provided in db and without units ('-127.5' to '0')")
            board.setVolume(volFloat)
        elif args.control == 'mute':
            if args.value == 'on':
                board.setMute(True)
            elif args.value == 'off':
                board.setMute(False)
            else:
                parser.error("Mute must be set to 'on' or 'off'")
        elif args.control == 'input':
            board.setInputSource(args.value)
        elif args.control == 'config':
            board.setConfig(int(args.value))
        elif args.control == 'dirac':
            if args.value == 'on':
                board.setDiracStatus(True)
            elif args.value == 'off':
                board.setDiracStatus(False)
            else:
                parser.error("Dirac must be set to 'on' or 'off'")

if __name__ == '__main__':
    main()


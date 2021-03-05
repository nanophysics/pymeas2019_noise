import sys

from mp import pyboard_query

sys.path.insert(0, r"C:\data\scanner_pyb\software")

import scanner_pyb_2020  # pylint: disable=import-error,wrong-import-position

if __name__ == "__main__":
    board = pyboard_query.ConnectPyboard(hwtype=scanner_pyb_2020.HWTYPE_SCANNER_PYB_2020)
    scanner = scanner_pyb_2020.ScannerPyb2020(board=board)
    print(f'{board.quickref} with boards {scanner.boards_text}')
    boardA = scanner.boards[0]
    boardB = scanner.boards[1]

    scanner.reset(on=False)
    #boardB.set(19) # 2k2 resistor
    boardB.set(11) # short for basenoise

    # while True:
    #     scanner.reset()
    #     boardA.set(9)
    #     time.sleep(0.5)
    #     scanner.reset()
    #     time.sleep(0.5)

    # while True:
    #     scanner.reset()
    #     boardA.set(9)
    #     time.sleep(0.2)
    #     boardA.set(13)
    #     time.sleep(0.2)
    #     boardA.set(14)
    #     time.sleep(0.5)
    #     scanner.reset()
    #     time.sleep(0.5)

    # scanner.reset()
    # for board in scanner.boards:
    #     for relais in range(1, 21):
    #         print(f'board {board.id}, relais {relais}')
    #         scanner.reset()
    #         board.set(relais)
    #         time.sleep(0.1)

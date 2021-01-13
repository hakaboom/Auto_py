# -*- coding: utf-8 -*-
import time
#
# import cv2
# import numpy as np
# from Minicap import connect
#
# devices = connect('emulator-5554')
# devices.get_display_info()

import socket
import cv2
import sys
import numpy as np
import threading
import subprocess
from queue import Queue



flag = False
readBannerBytes = 0
bannerLength = 2
readFrameBytes = 0
frameBodyLengthRemaining = 0
frameBody = ''
banner = {
    'version': 0,
    'length': 0,
    'pid': 0,
    'realWidth': 0,
    'realHeight': 0,
    'virtualWidth': 0,
    'virtualHeight': 0,
    'orientation': 0,
    'quirks': 0
}
CMD = 'LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap'
shell = 'adb -s emulator-5554 shell {0} -n \'minicap\' -P '.format(CMD)
shell = shell + '1920x1080@1920x1080/0 -s'
raw_data = subprocess.run(shell, shell=True, stdout=subprocess.PIPE)
chunk = raw_data.stdout


cursor = 0
while cursor < len(chunk):
    if (readBannerBytes < bannerLength):
        if readBannerBytes == 0:
            banner['version'] = int(hex(chunk[cursor]), 16)
        elif readBannerBytes == 1:
            banner['length'] = bannerLength = int(hex(chunk[cursor]), 16)
        elif readBannerBytes >= 2 and readBannerBytes <= 5:
            banner['pid'] = int(hex(chunk[cursor]), 16)
        elif readBannerBytes == 23:
            banner['quirks'] = int(hex(chunk[cursor]), 16)

        cursor += 1
        readBannerBytes += 1

    elif readFrameBytes < 4:
        frameBodyLengthRemaining += (int(hex(chunk[cursor]), 16) << (readFrameBytes * 8))
        cursor += 1
        readFrameBytes += 1

    else:
        print(banner)
        if len(chunk) - cursor >= frameBodyLengthRemaining:
            frameBody = frameBody + chunk[cursor:(cursor + frameBodyLengthRemaining)]
            if hex(frameBody[0]) != '0xff' or hex(frameBody[1]) != '0xd8':
                print(("Frame body does not strt with JPEG header", frameBody[0], frameBody[1]))
                exit()
            img = np.array(bytearray(frameBody))
            img = cv2.imdecode(img, 1)
            cv2.imwrite('test.png', img)
            cursor += frameBodyLengthRemaining
            frameBodyLengthRemaining = 0
            readFrameBytes = 0
            frameBody = ''

        else:
            frameBody = bytes(list(frameBody) + list(chunk[cursor:len(chunk)]))
            print(type(frameBody))
            frameBodyLengthRemaining -= (len(chunk) - cursor)
            readFrameBytes += len(chunk) - cursor
            cursor = len(chunk)

# -*- coding: utf-8 -*-
import time
import socket
import sys
import os
import threading
import platform
import subprocess
from queue import Queue
from typing import Tuple,List

import cv2
import numpy as np
from Minicap import connect


# devices = connect('emulator-5562')
# devices.get_display_info()
def test():
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
    a=time.time()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 8000))
    shell = 'adb -s emulator-5562 shell LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P 1280x720@1280x720/0 2>&1'
    # subprocess.run(shell,shell=True)
    os.popen(shell)
    print(time.time()-a)
    while True:
        chunk = client_socket.recv(12000)
        if len(chunk) == 0:
            continue

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

                if readBannerBytes == bannerLength:
                    print(('banner', banner))

            elif readFrameBytes < 4:
                frameBodyLengthRemaining += (int(hex(chunk[cursor]), 16) << (readFrameBytes * 8))
                cursor += 1
                readFrameBytes += 1

            else:
                # if this chunk has data of next image
                if len(chunk) - cursor >= frameBodyLengthRemaining:
                    frameBody = frameBody + chunk[cursor:(cursor + frameBodyLengthRemaining)]
                    if hex(frameBody[0]) != '0xff' or hex(frameBody[1]) != '0xd8':
                        exit()
                    img = np.array(bytearray(frameBody))
                    img = cv2.imdecode(img, 1)
                    img = cv2.resize(img, (1280, 720))
                    cv2.imshow('img1', img)
                    cv2.imwrite('test1.png', img)
                    cursor += frameBodyLengthRemaining
                    client_socket.close()
                    return img
                else:
                    # else this chunk is still for the current image
                    frameBody = bytes(list(frameBody) + list(chunk[cursor:len(chunk)]))
                    frameBodyLengthRemaining -= (len(chunk) - cursor)
                    readFrameBytes += len(chunk) - cursor
                    cursor = len(chunk)


from adb import ADB

ADB()
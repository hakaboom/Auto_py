# -*- coding: utf-8 -*-
import time
import re
import sys
import cv2
import numpy as np
from core.run import Android
# from loguru import logger
#
# a = Android(device_id='emulator-5562', cap_method='minicap', touch_method='adbtouch')
# a = Android(device_id='192.168.1.175:5555', cap_method='minicap', touch_method='minitouch')

#
# a=cv2.imread("./tmp/emulator-5562.png", 1)
# print(type(a))
# print(np.ndarray)
class a:
    def __getattr__(self, item):
        print(item)

c = a()
print(c.b)
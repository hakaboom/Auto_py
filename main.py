# -*- coding: utf-8 -*-
import time
import re
import sys
from core.run import Android
# from loguru import logger
#
a = Android(device_id='emulator-5562', cap_method='minicap', touch_method='adbtouch')
# a = Android(device_id='192.168.50.201:5555', cap_method='minicap', touch_method='miniouch')
# logger.debug(13412)
while True:
    a.screenshot()

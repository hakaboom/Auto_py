# -*- coding: utf-8 -*-
import time
# import re
# import sys
import cv2
import re
import numpy as np
from core.utils.base import pprint
from core.run import Android
#
# device = Android(device_id='192.168.1.224:5555', touch_method='minitouch')
device = Android(device_id='emulator-5554', cap_method='adbcap')
while True:
    img = device.screenshot().imread()
    cv2.imshow('capture', img)
    if cv2.waitKey(25) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        exit(0)

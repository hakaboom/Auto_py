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
device = Android(device_id='192.168.1.224:5555', touch_method='minitouch')
for i in range(900000):
    device.click(1280, 720)
# device.click(200, 200)

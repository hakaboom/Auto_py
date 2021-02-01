# -*- coding: utf-8 -*-
# import time
# import re
# import sys
# import cv2
# import numpy as np
# from core.run import Android
# from loguru import logger
from coordinate_transform import Anchor, Point, Size

# a = Android(device_id='emulator-5562', cap_method='minicap', touch_method='adbtouch')
a = Anchor(dev={'width': 1280, 'height': 720},
           cur={'width': 2240, 'height': 720, 'left': 100}, orientation=1)

siz = a.transform(Size(100,200))
print(siz)
print(a.size(100,200))
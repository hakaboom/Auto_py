# -*- coding: utf-8 -*-
# import time
# import re
# import sys
import cv2
# import numpy as np
from core.cv.match_template import find_templates
from core.run import Android
# from loguru import logger
from coordinate_transform import Anchor, Point, Size, Rect

# a = Android(device_id='emulator-5562', cap_method='minicap', touch_method='adbtouch')
im_source = cv2.imread("./tmp/test1.png")
im_search = cv2.imread("./tmp/test2.png")
a = find_templates(im_source, im_search)
for i in a:
    print(i)
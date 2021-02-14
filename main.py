# -*- coding: utf-8 -*-
import time
# import re
# import sys
import cv2
import numpy as np
from core.cv.match_template import find_template
from core.run import Android
# from loguru import logger
from coordinate import Anchor, Point, Size, Rect

# a = Android(device_id='emulator-5562', cap_method='minicap', touch_method='adbtouch')

from core.cv.base_image import image
from core.cv.sift import SIFT
im_source = image('主界面.png').imread()
im_search = image('编队.png').imread()
sift = SIFT()
s = time.time()
for i in range(99999):
    sift.find_sift_narrow(im_search=im_search, im_source=im_source)
    # sift.find_sift(im_search=im_search, im_source=im_source)
print(time.time() - s)
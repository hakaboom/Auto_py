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

from core.cv.sift import SIFT


def cv_imread(file_path):
    return cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), -1)

im_source = cv_imread('./tmp/iphone.png')
im_search = cv_imread('./tmp/iphone.jpg')
# im_source = cv2.resize(im_source, (int(im_source.shape[1]/1.3), int(im_source.shape[0]/1.3)))


sift = SIFT()
start = time.time()
r = sift.find_sift(im_search=im_search, im_source=im_source)

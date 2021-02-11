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


im_source = cv_imread('./tmp/主界面1.png')
im_search = cv_imread('./tmp/编队.png')
sift = SIFT()
sift.find_sift(im_search=im_search, im_source=im_source)


# goodMatch = np.expand_dims(goodMatch, 1)
# img_out = cv2.drawMatchesKnn(psd_img_1, psd_kp1, psd_img_2, psd_kp2, goodMatch[:15], None, flags=2)



# from airtest.aircv.sift import find_sift
# im_source = cv_imread('./tmp/主界面1.png')
# im_search = cv_imread('./tmp/编队.png')
# find_sift(im_source=im_source, im_search=im_search)
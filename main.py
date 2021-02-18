# -*- coding: utf-8 -*-
import time
# import re
# import sys
import cv2
import numpy as np
from core.run import Android
from core.cv.base_image import image
from coordinate import Anchor, Point, Size, Rect
from core.cv.match_template import find_template, find_templates
from core.cv.sift import SIFT

# device = Android(device_id='emulator-5554', cap_method='minicap', touch_method='minitouch')
# Anchor = Anchor(dev={'width': 1920, 'height': 1080},
#                 cur={'width': 3400, 'height': 1440, 'left': 260, 'right': 260}, orientation=1)
#
# rect = Rect.init_width_point_size(Anchor.point(0, 0), Anchor.size(1920, 1080))
# img = image('emulator-5554.png')
#
# im_search = image('star.png').resize(62*1.33333, 43*1.33333)
# a = find_templates(im_source=img, im_search=im_search)

# sift = SIFT()
#
# im_search = image('star.png')
# img = image('test1.png')
# a = sift.find_sift(im_search=im_search, im_source=img)
# print(a)
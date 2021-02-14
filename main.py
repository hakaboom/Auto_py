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

a = Android(device_id='4bfeb217', cap_method='minicap', touch_method='adbtouch')
print(a.screenshot().imshow())
cv2.waitKey(0)
a.screenshot().save_2_path()
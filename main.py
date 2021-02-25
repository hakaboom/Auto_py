# -*- coding: utf-8 -*-
import time
# import re
# import sys
import cv2
import numpy as np
from core.run import Android


device = Android(device_id='emulator-5554', cap_method='minicap', touch_method='minitouch')
device.screenshot().save2path()
# from core.cv.base_image import image
#
#
# a = image(img='./core/cv/test_image/star.png')
# a.imshow()
# cv2.waitKey(0)

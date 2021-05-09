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
# device = Android(device_id='192.168.0.112:5555', cap_method='javacap')
# device.adb.install_app(filepath='D:\work\\铁道物语0.9.6（5.07无SDK）.apk')
# cv2.namedWindow('capture', cv2.WINDOW_KEEPRATIO)
# while True:
#     img = device.screenshot().imread()
#     cv2.imshow('capture', img)
#     if cv2.waitKey(25) & 0xFF == ord('q'):
#         cv2.destroyAllWindows()
#         exit(0)
from core.cv.base_image import IMAGE
from core.cv.keypoint_matching import SIFT, SURF, _CUDA_SURF
sift = SIFT()
surf = SURF()
cuda_surf = _CUDA_SURF()
im_search = IMAGE('./core/cv/test_image/star.png')
im_source = IMAGE('./core/cv/test_image/test1.png')

# a = surf.find_best(im_search=im_search, im_source=im_source)
# b = sift.find_best(im_search=im_search, im_source=im_source)
c = cuda_surf.find_best(im_search=im_search, im_source=im_source)
# cv2.waitKey(0)

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
from core.cv.keypoint_matching import SIFT, SURF, ORB, BRIEF, AKAZE, RootSIFT
from core.cv.match_template import match_template

sift = SIFT()
surf = SURF()
orb = ORB()
brief = BRIEF()
match = match_template()
akaze = AKAZE()
im_search = IMAGE('./core/cv/test_image/ship.png')
im_source = IMAGE('./core/cv/test_image/test1.png')
startTime = time.time()
for i in range(1):
    # a = surf.find_best(im_search=im_search, im_source=im_source)
    b = sift.find_all(im_search=im_search, im_source=im_source)
    # c = orb.find_all(im_search=im_search, im_source=im_source, threshold=0.1)
    # d = brief.find_all(im_search=im_search, im_source=im_source)
    # e = match.find_templates(im_search=im_search, im_source=im_source, rgb=False)
    # f = akaze.find_all(im_search=im_search, im_source=im_source)
    # im_source.crop_image(c["rect"]).imshow()
    # cv2.waitKey(0)
    print('--------------------')

endTime = time.time()
print('useTime={time:.1f}ms'.format(time=(endTime - startTime) * 1000))

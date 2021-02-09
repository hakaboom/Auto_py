# -*- coding: utf-8 -*-
import time
# import re
# import sys
import cv2
import numpy as np
from core.cv.match_template import find_template
from core.run import Android
# from loguru import logger
from coordinate_transform import Anchor, Point, Size, Rect

# a = Android(device_id='emulator-5562', cap_method='minicap', touch_method='adbtouch')


def cv_imread(file_path):
    return cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), -1)


psd_img_1 = cv_imread('./tmp/主界面1.png')
psd_img_2 = cv_imread('./tmp/编队.png')
sift = cv2.SIFT_create()
psd_kp1, psd_des1 = sift.detectAndCompute(psd_img_1, None)
psd_kp2, psd_des2 = sift.detectAndCompute(psd_img_2, None)

# 4) Flann特征匹配
FLANN_INDEX_KDTREE = 1
index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
search_params = dict(checks=50)

flann = cv2.FlannBasedMatcher(index_params, search_params)
matches = flann.knnMatch(psd_des1, psd_des2, k=2)
goodMatch = []
for m, n in matches:
    # goodMatch是经过筛选的优质配对，如果2个配对中第一匹配的距离小于第二匹配的距离的1/2，基本可以说明这个第一配对是两幅图像中独特的，不重复的特征点,可以保留。
    if m.distance < 0.45*n.distance:
        goodMatch.append(m)
# 增加一个维度
goodMatch = np.expand_dims(goodMatch, 1)
print(goodMatch[:20])

img_out = cv2.drawMatchesKnn(psd_img_1, psd_kp1, psd_img_2, psd_kp2, goodMatch[:15], None, flags=2)

cv2.imshow('image', img_out)
cv2.waitKey(0)
cv2.destroyAllWindows()
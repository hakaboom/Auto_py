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

# device = Android(device_id='192.168.1.192:5555', cap_method='adbcap')
# device.adb.install_app(filepath='E:\工作文件夹\铁道物语\sdk\\铁道0.9.5（4.17）.apk')

# device = Android(device_id='192.168.1.193:5555', cap_method='adbcap')
# device.adb.install_app(filepath='E:\sdk\\铁道0.9.5（4.17）.apk')



# print(device.adb.sdk_version(), device.adb.abi_version())
# device = Android(device_id='emulator-5554', cap_method='javacap')
# device.screenshot().save2path()
# cv2.namedWindow('capture', cv2.WINDOW_KEEPRATIO)
# while True:
#     img = device.screenshot().imread()
#     cv2.imshow('capture', img)
#     if cv2.waitKey(25) & 0xFF == ord('q'):
#         cv2.destroyAllWindows()
#         exit(0)

if __name__ == '__main__':
    from core.cv.base_image import image
    from core.cv.sift import SIFT
    sift = SIFT()
    im_search = image('./tmp/test4.png')
    img = image('./tmp/test1.png')
    a = sift.find_sift(im_search=im_search, im_source=img)
    print(a)
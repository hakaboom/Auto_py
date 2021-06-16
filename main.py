# -*- coding: utf-8 -*-
import time


from baseImage import IMAGE
from image_registration import SIFT, SURF, ORB, BRIEF, AKAZE, RootSIFT, match_template

orb = ORB()
match = match_template()
im_search = IMAGE('./core/cv/test_image/star.png')
im_source = IMAGE('./core/cv/test_image/test1.png')
startTime = time.time()
for i in range(1):
    orb.find_all(im_search=im_search, im_source=im_source, threshold=0.1)
    print('--------------------')

endTime = time.time()
print('useTime={time:.1f}ms'.format(time=(endTime - startTime) * 1000))

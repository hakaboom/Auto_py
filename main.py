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
device = Android(device_id='emulator-5554', touch_method='maxtouch')
device.click(100, 100)
# device.click(200, 200)

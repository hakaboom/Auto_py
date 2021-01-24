# -*- coding: utf-8 -*-
import time
import re
from core.run import Android
from typing import Union, Tuple
#
# a = Android(device_id='emulator-5554', cap_method='minicap', touch_method='adbtouch')
a = Android(device_id='192.168.50.201:5555', cap_method='minicap', touch_method='miniouch')
# a.screenshot()
a.click(100, 100, duration=2000)
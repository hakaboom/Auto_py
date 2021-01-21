# -*- coding: utf-8 -*-
import time
import socket
import re
from core.run import Android
a = Android(device_id='emulator-5562', minicap=False)
b = time.time()
for i in range(100):
    a.minitouch.click(680, 490)
print(time.time()- b)

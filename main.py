# -*- coding: utf-8 -*-
import time
import threading
import subprocess
from core.run import Android

a = Android(device_id='emulator-5562',minicap=False)
x=165
y=148
a.touch.down(x,y)
time.sleep(0.05)
a.touch.up(x,y)


# -*- coding: utf-8 -*-
import time
from core.run import Android
from typing import Union, Tuple
#
# a = Android(device_id='127.0.0.1:62001', cap_method='minicap')
a = Android(device_id='emulator-5554', cap_method='minicap')
a.screenshot()
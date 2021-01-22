# -*- coding: utf-8 -*-

from core.run import Android
from typing import Union, Tuple

a = Android(device_id='emulator-5562')
a.adb.get_process_status(name='com.bilibili.azurlane')
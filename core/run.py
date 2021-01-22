#! usr/bin/python
# -*- coding:utf-8 -*-
from core.adb import ADB
from core.minicap import Minicap
from core.base_touch import Touch as ADBTOUCH
from core.minitouch import Minitouch
from core.constant import TOUCH_METHOD, CAP_METHOD

from typing import Union, Tuple


class Android(object):
    """不应该暴露adb接口出来???"""
    def __init__(self, device_id=None, adb_path=None, host='127.0.0.1', port=5037,
                 touch_method: str = 'minitouch', cap_method: str = 'minicap'):
        self.adb = ADB(device_id, adb_path, host, port)
        # cap mode
        if cap_method == 'minicap':
            self.minicap = Minicap(self.adb)
            self.cap_method = CAP_METHOD.MINICAP
        else:
            self.cap_method = CAP_METHOD.ADBCAP
        # touch mode
        if touch_method == 'minitouch':
            self.minitouch = Minitouch(self.adb)
            self.touch_method = TOUCH_METHOD.MINITOUCH
        else:
            self.adbtouch = ADBTOUCH()
            self.touch_method = TOUCH_METHOD.ADBTOUCH

    def screenshot(self, Rect: Tuple[int, int, int, int] = None):
        if self.cap_method == CAP_METHOD.MINICAP:
            return self.minicap.screenshot()
        elif self.cap_method == CAP_METHOD.ADBCAP:
            return self.adb.screenshot(Rect)

    def down(self, x: int, y: int, index: int = 0, pressure: int = 50):
        if self.touch_method == TOUCH_METHOD.MINITOUCH:
            return self.minitouch.down(x, y, index, pressure)
        elif self.touch_method == TOUCH_METHOD.ADBTOUCH:
            return self.adbtouch.down(x, y, index)

    def up(self, x: int, y: int, index: int = 0):
        if self.touch_method == TOUCH_METHOD.MINITOUCH:
            return self.minitouch.up(index=index)
        elif self.touch_method == TOUCH_METHOD.ADBTOUCH:
            return self.adbtouch.up(x, y, index)

    def sleep(self, duration: int = 50):
        if self.touch_method == TOUCH_METHOD.MINITOUCH:
            return self.minitouch.sleep(duration)
        elif self.touch_method == TOUCH_METHOD.ADBTOUCH:
            return self.adbtouch.sleep(duration)

    def click(self, x: int, y: int, index: int = 0, duration: int = 20):
        if self.touch_method == TOUCH_METHOD.MINITOUCH:
            return self.minitouch.click(x, y, index=index, duration=duration)
        elif self.touch_method == TOUCH_METHOD.ADBTOUCH:
            return self.adbtouch.click(x, y, index=index, duration=duration)


class _system(Android):
    def screen_on(self):
        pass

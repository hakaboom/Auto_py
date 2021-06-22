# -*- coding: utf-8 -*-
from core.cap_methods.base_cap import BaseCap


class AdbCap(BaseCap):
    def __init__(self, adb):
        super(AdbCap, self).__init__(adb)

    def get_frame(self):
        return self.adb.screenshot()

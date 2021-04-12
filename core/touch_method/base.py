# -*- coding: utf-8 -*-
from core.utils.base import pprint
from core.adb import ADB


class transform(object):
    def __init__(self, adb: ADB):
        self.size_info = adb.get_display_info()

    def transform(self, x, y):
        x, y = self.ori_transform(x, y)
        x, y = self.transform_xy(x, y)
        return x, y

    def ori_transform(self, x, y):
        w, h = self.size_info['width'], self.size_info['height']
        if self.size_info['orientation'] == 0:
            x, y = x, y
        elif self.size_info['orientation'] == 1:
            x, y = w - y, x
        elif self.size_info['orientation'] == 2:
            x, y = w - x, h - y
        elif self.size_info['orientation'] == 3:
            x, y = y, h - x
        return x, y

    def transform_xy(self, x, y):
        return x, y

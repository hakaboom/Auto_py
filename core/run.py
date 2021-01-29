#! usr/bin/python
# -*- coding:utf-8 -*-
import time
from core.adb import ADB
from core.minicap import Minicap
from core.base_touch import Touch as ADBTOUCH
from core.minitouch import Minitouch
from core.constant import TOUCH_METHOD, CAP_METHOD
from core.Javecap import Javacap
from core.utils.base import initLogger
from core.image import image as tmp_image
from loguru import logger
from typing import Union, Tuple

# 初始化loguru
initLogger()


class Android(object):
    def __init__(self, device_id=None, adb_path=None, host='127.0.0.1', port=5037,
                 touch_method: str = 'minitouch', cap_method: str = 'minicap'):
        self.adb = ADB(device_id, adb_path, host, port)
        # cap mode
        if cap_method == 'minicap':
            self.minicap = Minicap(self.adb)
            self.cap_method = CAP_METHOD.MINICAP
        elif cap_method == 'javacap':
            self.javacap = Javacap(self.adb)
            self.cap_method = CAP_METHOD.JAVACAP
        elif cap_method == 'adbcap':
            self.cap_method = CAP_METHOD.ADBCAP
        else:
            raise ValueError("please choice cap_method ('minicap','javacap','adbcap')")
        # touch mode
        if touch_method == 'minitouch':
            self.minitouch = Minitouch(self.adb)
            self.touch_method = TOUCH_METHOD.MINITOUCH
        elif touch_method == 'adbtouch':
            self.adbtouch = ADBTOUCH(self.adb)
            self.touch_method = TOUCH_METHOD.ADBTOUCH
        else:
            raise ValueError("please choice touch_method ('minitouch','adbtouch')")
        self.tmp_image = tmp_image(self.adb, capFunction=self.screenshot)

    def screenshot(self):
        stamp = time.time()
        if self.cap_method == CAP_METHOD.MINICAP:
            img_data, socket_time = self.minicap.get_frame()
        elif self.cap_method == CAP_METHOD.JAVACAP:
            img_data = self.javacap.get_frame_from_stream()
        elif self.cap_method == CAP_METHOD.ADBCAP:
            img_data = self.adb.screenshot()
        # 图片写入到缓存中
        self.tmp_image.set_tmpImage(img_data)
        logger.info("screenshot time={:.2f}ms,size=({},{},{}) path='{}'", (time.time() - stamp)*1000,
                    *self.tmp_image.details)
        return self.tmp_image

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

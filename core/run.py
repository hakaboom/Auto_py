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
from core.cv.base_image import image as Image
from core.constant import ADB_CAP_LOCAL_PATH
from loguru import logger
from typing import Union, Tuple

# 初始化loguru
initLogger()


class Android(object):
    def __init__(self, device_id=None, adb_path=None, host='127.0.0.1', port=5037,
                 touch_method: str = TOUCH_METHOD.MINITOUCH,
                 cap_method: str = CAP_METHOD.MINICAP):
        self.adb = ADB(device_id, adb_path, host, port)
        # cap mode
        self.cap_method = cap_method
        self.minicap = Minicap(self.adb)
        self.javacap = Javacap(self.adb)
        # touch mode
        self.touch_method = touch_method
        self.minitouch = Minitouch(self.adb)
        self.adbtouch = ADBTOUCH(self.adb)
        self.tmp_image = Image(self.adb)

    def screenshot(self):
        stamp = time.time()
        if self.cap_method == CAP_METHOD.MINICAP:
            img_data, socket_time = self.minicap.get_frame()
        elif self.cap_method == CAP_METHOD.JAVACAP:
            img_data = self.javacap.get_frame_from_stream()
        elif self.cap_method == CAP_METHOD.ADBCAP:
            img_data = self.adb.screenshot()
        # 图片写入到缓存中
        self.tmp_image.imwrite(img_data)
        logger.info("screenshot time={:.2f}ms,size=({},{}) path='{}'", (time.time() - stamp)*1000,
                    *self.tmp_image.shape, self.tmp_image.path)
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

    def get_cap_path(self):
        """获取当前截图路径"""
        return self.tmp_image.path


class _system(Android):
    def screen_on(self):
        pass

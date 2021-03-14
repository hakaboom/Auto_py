#! usr/bin/python
# -*- coding:utf-8 -*-
import time
from core.adb import ADB
from core.minicap import Minicap
from core.touch_method.event_touch import Touch as EVENTTOUCH
from core.touch_method.minitouch import Minitouch
from core.constant import TOUCH_METHOD, CAP_METHOD
from core.Javecap import Javacap
from core.utils.base import initLogger
from core.cv.base_image import image as Image
from core.cv.sift import SIFT
from core.constant import ADB_CAP_REMOTE_PATH
from loguru import logger

# 初始化loguru
initLogger()


class Android(object):
    def __init__(self, device_id=None, adb_path=None, host='127.0.0.1', port=5037,
                 touch_method: str = TOUCH_METHOD.MINITOUCH,
                 cap_method: str = CAP_METHOD.MINICAP):
        self.adb = ADB(device_id, adb_path, host, port)
        self._display_info = {}
        self.tmp_image = Image(path=ADB_CAP_REMOTE_PATH.format(self.adb.get_device_id(decode=True)))
        # cap mode
        if cap_method == 'minicap':
            self.cap_method = CAP_METHOD.MINICAP
        elif cap_method == 'javacap':
            self.cap_method = CAP_METHOD.JAVACAP
        else:
            self.cap_method = CAP_METHOD.ADBCAP
        self.minicap = Minicap(self.adb)
        self.javacap = Javacap(self.adb)
        # touch mode
        if touch_method == 'minitouch':
            self.touch_method = TOUCH_METHOD.MINITOUCH
        else:
            self.touch_method = TOUCH_METHOD.ADBTOUCH

        self.minitouch = Minitouch(self.adb)
        self.EVENTTOUCH = EVENTTOUCH(self.adb)
        # matching mode
        self.sift = SIFT()

    def screenshot(self):
        stamp = time.time()
        img_data = None
        if self.cap_method == CAP_METHOD.MINICAP:
            img_data = self.minicap.get_frame()
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
            return self.EVENTTOUCH.down(x, y, index)

    def up(self, x: int, y: int, index: int = 0):
        if self.touch_method == TOUCH_METHOD.MINITOUCH:
            return self.minitouch.up(index=index)
        elif self.touch_method == TOUCH_METHOD.ADBTOUCH:
            return self.EVENTTOUCH.up(x, y, index)

    def sleep(self, duration: int = 50):
        if self.touch_method == TOUCH_METHOD.MINITOUCH:
            return self.minitouch.sleep(duration)
        elif self.touch_method == TOUCH_METHOD.ADBTOUCH:
            return self.EVENTTOUCH.sleep(duration)

    def click(self, x: int, y: int, index: int = 0, duration: int = 20):
        if self.touch_method == TOUCH_METHOD.MINITOUCH:
            logger.info('[minitouch]index={}, x={}, y={}', index, x, y)
            return self.minitouch.click(x, y, index=index, duration=duration)
        elif self.touch_method == TOUCH_METHOD.ADBTOUCH:
            logger.info('[adbTouch]index={}, x={}, y={}', index, x, y)
            return self.EVENTTOUCH.click(x, y, index=index, duration=duration)

    def display_info(self):
        if not self._display_info:
            self._display_info = self.get_display_info()

    def get_display_info(self):
        if self.cap_method == CAP_METHOD.MINICAP:
            try:
                return self.minicap.get_display_info()
            except RuntimeError:
                # Even if minicap execution fails, use adb instead
                return self.adb.get_display_info()
        return self.adb.get_display_info()

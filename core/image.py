#! usr/bin/python
# -*- coding:utf-8 -*-
from core.constant import ADB_CAP_NAME

import cv2
import numpy as np
from loguru import logger
from typing import Callable

class _image(object):
    def __init__(self,cap_fun: Callable):
        self._tmp_path = ADB_CAP_NAME.format(self.adb.get_device_id().replace(':', '_'))
        self._tmp_image_data = None  # 图像文件缓存

    def __getattr__(self, item):
        if item == '_tmp_image_data':
            if not self._tmp_image_data:
        return self._tmp_image_data

    def set_tmpImage(self, data):
        type_data = type(data)
        if type_data == np.ndarray:
            pass

        self._tmp_image_data = data

    def clean_tmp(self):
        self._tmp_image_data = None

    def save_as_png(self):
        if self._tmp_image_data:
            cv2.imwrite(self._tmp_path, self._tmp_image_data)
        raise ValueError('no image_data in tmp')


class image(_image):
    pass
#! usr/bin/python
# -*- coding:utf-8 -*-
from core.constant import ADB_CAP_NAME

import cv2
import time
import numpy as np
from loguru import logger


class _image(object):
    def __init__(self, adb, capFunction=None):
        self._tmp_path = ADB_CAP_NAME.format(adb.get_device_id().replace(':', '_'))
        self._tmp_image_data = None  # 图像文件缓存
        # self._capFunction = capFunction

    def read_tmp(self) -> np.ndarray:
        """读取缓存"""
        if type(self._tmp_image_data) == np.ndarray:
            return self._tmp_image_data
        else:
            logger.error('没有缓存')

    def set_tmpImage(self, data):
        """为缓存填充图片信息"""
        img_type = type(data)
        if img_type == np.ndarray:
            pass
        elif img_type == bytes:
            data = self.bytes2img(data)
        else:
            raise ValueError('unknown img_data type:{}'.format(img_type))
        logger.debug('写入缓存 type={}', img_type)
        self._tmp_image_data = data

    def clean_tmp(self):
        """清除缓存"""
        self._tmp_image_data = None

    def save_as_png(self):
        """
        根据_tmp_image_data的类型转换后保存为图片
        :return: None
        """
        img_type = type(self._tmp_image_data)
        if img_type == np.ndarray:
            img = self._tmp_image_data
        elif img_type == bytes:
            img = self.bytes2img(self._tmp_image_data)
        else:
            raise TypeError('unknown img_data type:{}'.format(img_type))
        cv2.imwrite(self._tmp_path, img)

    @staticmethod
    def bytes2img(b) -> np.ndarray:
        """bytes转换成cv2可读取格式"""
        img = np.array(bytearray(b))
        img = cv2.imdecode(img, 1)
        return img

    @property
    def details(self):
        """获取图片的长,宽,深度,信息"""
        shape = self.read_tmp().shape
        width, height, row = shape
        if width > height:
            width, height = height, width
        return width, height, row, self._tmp_path


class image(_image):
    pass

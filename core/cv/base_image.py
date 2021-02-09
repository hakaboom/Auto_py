#! usr/bin/python
# -*- coding:utf-8 -*-
import cv2
import time
from core.constant import ADB_CAP_REMOTE_PATH
from core.cv.thresholding import otsu, bgr2gray
from typing import Tuple, Union
import numpy as np
from loguru import logger
"""cv2无法读取中文路径"""


class _image(object):
    def __init__(self, adb=None):
        self._tmp_path = adb and ADB_CAP_REMOTE_PATH.format(adb.get_device_id().replace(':', '_')) or './tmp/'
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

    def imwrite(self):
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
    def details(self) -> Tuple[int, int, int, str]:
        """获取图片的长,宽,深度,信息"""
        shape = self.read_tmp().shape
        width, height, rows = shape
        if width > height:
            width, height = height, width
        return width, height, rows, self._tmp_path

    @property
    def path(self):
        return self._tmp_path


class cv(object):
    """操作image类,返回新的图片对象"""
    def __init__(self, img: np.ndarray):
        self.image = img.copy()

    def imshow(self, title: str = 'show', flag: bool = False):
        """以GUI显示图片"""
        cv2.namedWindow(title, cv2.WINDOW_NORMAL)
        cv2.imshow(title, self.image)
        if not flag:
            cv2.waitKey(0)
        cv2.destroyAllWindows()

    def imwrite(self, filename: str, params=None):
        cv2.imwrite(filename, self.image, params)


class image(_image):
    def show(self, title: str = 'show', flag: bool = False):
        """以GUI显示图片"""
        cv2.namedWindow(title, cv2.WINDOW_KEEPRATIO)
        cv2.imshow(title, self.read_tmp())
        if not flag:
            cv2.waitKey(0)
        cv2.destroyAllWindows()

    def rotate(self, angle: int = 90, clockwise: bool = True):
        """
        旋转图片

        Args:
            angle: 旋转角度
            clockwise: True-顺时针旋转, False-逆时针旋转
        """
        img = self.read_tmp().copy()
        if clockwise:
            angle = 360 - angle
        rows, cols, _ = img.shape
        center = (cols / 2, rows / 2)
        mask = img.copy()
        mask[:, :] = 255
        M = cv2.getRotationMatrix2D(center, angle, 1)
        top_right = np.array((cols, 0)) - np.array(center)
        bottom_right = np.array((cols, rows)) - np.array(center)
        top_right_after_rot = M[0:2, 0:2].dot(top_right)
        bottom_right_after_rot = M[0:2, 0:2].dot(bottom_right)
        new_width = max(int(abs(bottom_right_after_rot[0] * 2) + 0.5), int(abs(top_right_after_rot[0] * 2) + 0.5))
        new_height = max(int(abs(top_right_after_rot[1] * 2) + 0.5), int(abs(bottom_right_after_rot[1] * 2) + 0.5))
        offset_x, offset_y = (new_width - cols) / 2, (new_height - rows) / 2
        M[0, 2] += offset_x
        M[1, 2] += offset_y
        dst = cv2.warpAffine(img, M, (new_width, new_height))
        return cv(img=dst)

    def crop_image(self, rect):
        """区域范围截图"""
        img = self.read_tmp()
        width, height, rows, __ = self.details
        if isinstance(rect, (list, tuple)) and len(rect) == 4:
            if rect[0] > height or rect[1] > width or rect[0] + rect[2] > height or rect[1] + rect[3] > width:
                raise OverflowError('Rect不能超出屏幕 {}'.format(rect))
            height, width = img.shape[:2]
            # 获取在图像中的实际有效区域：
            x_min, y_min, x_max, y_max = [int(i) for i in rect]
            x_min, y_min = max(0, x_min), max(0, y_min)
            x_min, y_min = min(width - 1, x_min), min(height - 1, y_min)
            x_max, y_max = max(0, x_max), max(0, y_max)
            x_max, y_max = min(width - 1, x_max), min(height - 1, y_max)

            # 返回剪切的有效图像+左上角的偏移坐标：
            img_crop = img[y_min:y_max, x_min:x_max]
            return cv(img=img_crop)

    def binarization(self):
        img = self.read_tmp()
        img = bgr2gray(img)
        gray_img = otsu(img)
        return cv(img=gray_img)

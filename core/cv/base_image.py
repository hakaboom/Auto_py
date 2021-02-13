#! usr/bin/python
# -*- coding:utf-8 -*-
import cv2
import time
from core.constant import ADB_CAP_REMOTE_PATH
from coordinate import Rect
from core.cv.thresholding import otsu
from core.cv.utils import read_image, bgr_2_gray
from core.utils.base import auto_increment
from typing import Tuple, Union
import numpy as np
from loguru import logger


class _image(object):
    def __init__(self, img, flags=cv2.IMREAD_COLOR, adb=None):
        self.tmp_path = adb and ADB_CAP_REMOTE_PATH.format(adb.get_device_id().replace(':', '_')) or './tmp/'
        self.image_data = None
        # self._capFunction = capFunction
        self.imwrite(img, flags)

    def imread(self) -> np.ndarray:
        return self.image_data

    def imwrite(self, img, flags: int = cv2.IMREAD_COLOR):
        if type(img) == str:
            self.image_data = read_image('{}{}'.format(self.tmp_path, img), flags)
        elif isinstance(img, np.ndarray):
            self.image_data = img
        elif isinstance(img, image):
            self.image_data = img.imread().copy()
        else:
            raise ValueError('unknown image, type:{}, image={} '.format(type(img), img))

    def clean_image(self):
        """清除缓存"""
        self.image_data = None

    @property
    def shape(self):
        return self.imread().shape[:2]

    @property
    def path(self):
        return self.tmp_path


class image(_image):
    SHOW_INDEX = auto_increment()

    def imshow(self, title: str = None):
        """以GUI显示图片"""
        title = str(title or self.SHOW_INDEX())
        cv2.namedWindow(title, cv2.WINDOW_KEEPRATIO)
        cv2.imshow(title, self.imread())
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

    def rotate(self, angle: int = 90, clockwise: bool = True):
        """
        旋转图片

        Args:
            angle: 旋转角度
            clockwise: True-顺时针旋转, False-逆时针旋转
        """
        img = self.imread()
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
        self.imwrite(cv2.warpAffine(img, M, (new_width, new_height)))
        return self

    def crop_image(self, rect):
        """区域范围截图"""
        img = self.imread()
        height, width = self.shape
        if isinstance(rect, (list, tuple)) and len(rect) == 4:
            rect = Rect(*rect)
        elif isinstance(rect, Rect):
            pass
        else:
            raise ValueError('unknown rect: type={}, rect={}'.format(type(rect), rect))
        if not Rect(0, 0, width, height).contains(rect):
            raise OverflowError('Rect不能超出屏幕 {}'.format(rect))
        # 获取在图像中的实际有效区域：
        x_min, y_min = rect.tl.x, rect.tl.y
        x_max, y_max = rect.br.x, rect.br.y
        x_min, y_min = max(0, x_min), max(0, y_min)
        x_min, y_min = min(width - 1, x_min), min(height - 1, y_min)
        x_max, y_max = max(0, x_max), max(0, y_max)
        x_max, y_max = min(width - 1, x_max), min(height - 1, y_max)

        return image(img[y_min:y_max, x_min:x_max])

    def binarization(self):
        img = self.imread()
        img = bgr_2_gray(img)
        return image(otsu(img))

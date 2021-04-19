# -*- coding: utf-8 -*-
import os
import cv2
import itertools
from core.utils.coordinate import Rect
import numpy as np


def generate_result(rect, confi):
    """Format the result: 定义图像识别结果格式."""
    ret = dict(rect=rect, confidence=confi)
    return ret


def check_file(fileName: str):
    """check file in path"""
    return os.path.isfile('{}'.format(fileName))


def check_image_valid(image):
    """检查图像是否有效"""
    if image is not None and image.any():
        return True
    else:
        return False


def read_image(filename: str, flags: int = cv2.IMREAD_COLOR):
    """cv2.imread的加强版"""
    if check_file(filename) is False:
        raise IOError('File not found, path:{}'.format(filename))
    img = cv2.imdecode(np.fromfile(filename, dtype=np.uint8), flags)
    if check_image_valid(img):
        return img
    else:
        raise BaseException('cv2 decode Error, path:{}, flage={}', filename, flags)


def bytes_2_img(byte) -> np.ndarray:
    """bytes转换成cv2可读取格式"""
    img = cv2.imdecode(np.array(bytearray(byte)), 1)
    if img is None:
        raise ValueError('decode bytes to image error \n\'{}\''.format(byte))
    return img


def bgr_2_gray(img):
    b = img[:, :, 0].copy()
    g = img[:, :, 1].copy()
    r = img[:, :, 2].copy()

    gray_img = 0.2126 * r + 0.7152 * g + 0.0722 * b
    gray_img = gray_img.astype(np.uint8)

    return gray_img


def create_similar_rect(x, y, w, h):
    x = [x, x + 1, x - 1]
    y = [y, y + 1, y - 1]
    w = [w, w + 1, w - 1]
    h = [h, h + 1, h - 1]
    t = []
    for i in itertools.product(*[range(3) for k in range(4)]):
        if (i[2] == 2 and i[3] == 1) or (i[2] == 1 and i[3] == 2):
            pass
        else:
            t.append(Rect(x=x[i[0]], y=y[i[1]], width=w[i[2]], height=h[i[3]]))
    return t


def img_mat_rgb_2_gray(img_mat):
    """
    Turn img_mat into gray_scale, so that template match can figure the img data.
    "print(type(im_search[0][0])")  can check the pixel type.
    """
    assert isinstance(img_mat[0][0], np.ndarray), "input must be instance of np.ndarray"
    return cv2.cvtColor(img_mat, cv2.COLOR_BGR2GRAY)
#! usr/bin/python
# -*- coding:utf-8 -*-
""" opencv matchTemplate"""
import cv2
import time
import numpy as np
from coordinate import Rect


def cal_rgb_confidence(img_src_rgb, img_sch_rgb):
    src_bgr = cv2.split(img_src_rgb)
    sch_bgr = cv2.split(img_sch_rgb)
    # 计算BGR三通道的confidence，存入bgr_confidence:
    bgr_confidence = [0, 0, 0]
    for i in range(3):
        res_temp = cv2.matchTemplate(src_bgr[i], sch_bgr[i], cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res_temp)
        bgr_confidence[i] = max_val
    return min(bgr_confidence)


def find_template(im_source, im_search, threshold: int = 0.85, mode=cv2.TM_CCOEFF_NORMED):
    """
    模板匹配
    :param im_source: 待匹配图像
    :param im_search: 待匹配模板
    :param threshold: 匹配度
    :param mode: 识别模式
    :return: None or Rect
    """
    # 模板匹配取得res矩阵
    res = cv2.matchTemplate(im_source, im_search, mode)
    # 找到最佳匹配项
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    h, w = im_search.shape[:2]
    # 求可信度
    img_crop = im_source[max_loc[1]:max_loc[1] + h, max_loc[0]: max_loc[0] + w]
    confidence = cal_rgb_confidence(img_crop, im_search)
    # 如果可信度小于threshold,则返回None
    if confidence < threshold:
        return None
    # 求取位置
    x, y = max_loc
    rect = Rect(x=x, y=y, width=w, height=h)

    return rect, confidence


def find_templates(im_source, im_search, threshold: int = 0.9, mode=cv2.TM_CCOEFF_NORMED, max_count=10):
    # 模板匹配取得res矩阵
    res = cv2.matchTemplate(im_source, im_search, mode)

    result = []
    h, w = im_search.shape[:2]

    while True:
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        img_crop = im_source[max_loc[1]:max_loc[1] + h, max_loc[0]: max_loc[0] + w]
        confidence = rgb_confidence(img_crop, im_search)

        if confidence < threshold or len(result) > max_count:
            break
        x, y = max_loc
        rect = Rect(x=x, y=y, width=w, height=h)
        result.append(rect)
        # 屏蔽最优结
        cv2.rectangle(res, (int(max_loc[0] - 1), int(max_loc[1] - 1)),
                      (int(max_loc[0] + 1), int(max_loc[1] + 1)), (0, 0, 0), -1)
    return result if result else None


if __name__ == '__main__':
    def cv_imread(file_path):
        return cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), -1)

    im_source = cv_imread('./tmp/主界面1.png')
    im_search = cv_imread('./tmp/编队.png')
    h, w, _ = im_search.shape
    h, w = int(h * (540 / 1080)), int(w * (540 / 1080))
    im_search = cv2.resize(im_search, (w, h), interpolation=cv2.INTER_LANCZOS4)

    request = find_template(im_search=im_search, im_source=im_source)
    print(request)
    cv2.waitKey(0)

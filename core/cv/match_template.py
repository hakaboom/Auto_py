#! usr/bin/python
# -*- coding:utf-8 -*-
""" opencv matchTemplate"""
import cv2
import time
from core.cv.base_image import check_detection_input
from core.cv.utils import generate_result, img_mat_rgb_2_gray
from core.utils.coordinate import Rect


def cal_rgb_confidence(img_src_rgb, img_sch_rgb):
    img_sch_rgb = cv2.copyMakeBorder(img_sch_rgb, 10, 10, 10, 10, cv2.BORDER_REPLICATE)
    # 转HSV强化颜色的影响
    img_src_rgb = cv2.cvtColor(img_src_rgb, cv2.COLOR_BGR2HSV)
    img_sch_rgb = cv2.cvtColor(img_sch_rgb, cv2.COLOR_BGR2HSV)
    src_bgr, sch_bgr = cv2.split(img_src_rgb), cv2.split(img_sch_rgb)
    # 计算BGR三通道的confidence，存入bgr_confidence:
    bgr_confidence = [0, 0, 0]
    for i in range(3):
        res_temp = cv2.matchTemplate(src_bgr[i], sch_bgr[i], cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res_temp)
        bgr_confidence[i] = max_val
    print(bgr_confidence)
    return min(bgr_confidence)


def find_template(im_source, im_search, threshold: float = 0.85, mode=cv2.TM_CCOEFF_NORMED):
    """
    模板匹配
    :param im_source: 待匹配图像
    :param im_search: 待匹配模板
    :param threshold: 匹配度
    :param mode: 识别模式
    :return: None or Rect
    """
    start = time.time()
    im_source, im_search = check_detection_input(im_source, im_search)
    # 模板匹配取得res矩阵
    res = _get_template_result_matrix(im_source, im_search)
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
    print('[tpl]{Rect}, confidence={confidence}, time={time:.2f}'.format(confidence=confidence, Rect=rect,
                                                                time=(time.time() - start)*1000))
    return generate_result(rect, confidence)


def find_templates(im_source, im_search, threshold: float = 0.9, max_count=10):
    """
    模板匹配
    :param im_source: 待匹配图像
    :param im_search: 待匹配模板
    :param threshold: 匹配度
    :param mode: 识别模式
    :param max_count: 最多匹配数量
    :return: None or Rect
    """
    start = time.time()
    im_source, im_search = check_detection_input(im_source, im_search)
    # 模板匹配取得res矩阵
    res = _get_template_result_matrix(im_source, im_search)
    result = []
    h, w = im_search.shape[:2]

    while True:
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        img_crop = im_source[max_loc[1]:max_loc[1] + h, max_loc[0]: max_loc[0] + w]
        confidence = cal_rgb_confidence(img_crop, im_search)
        if confidence < threshold or len(result) > max_count:
            break
        x, y = max_loc
        rect = Rect(x=x, y=y, width=w, height=h)
        result.append(generate_result(rect, confidence))
        # 屏蔽最优结
        cv2.rectangle(res, (int(max_loc[0] - 1), int(max_loc[1] - 1)),
                      (int(max_loc[0] + 1), int(max_loc[1] + 1)), (0, 0, 0), -1)
    if result:
        print('[tpls] find counts:{counts}, time={time:.2f}{result}ms'.format(counts=len(result),
                                                                              time=(time.time() - start)*1000,
              result=''.join(['\n\t{}, confidence={}'.format(x['rect'], x['confidence']) for x in result])))
    return result if result else None


def _get_template_result_matrix(im_source, im_search):
    """求取模板匹配的结果矩阵."""
    # 灰度识别: cv2.matchTemplate( )只能处理灰度图片参数
    s_gray, i_gray = img_mat_rgb_2_gray(im_search), img_mat_rgb_2_gray(im_source)
    return cv2.matchTemplate(i_gray, s_gray, cv2.TM_CCOEFF_NORMED)


if __name__ == '__main__':
    from core.cv.base_image import image
    from core.utils.coordinate import Anchor,  Rect
    from core.cv.match_template import find_templates
    Anchor = Anchor(dev={'width': 1920, 'height': 1080},
                    cur={'width': 3400, 'height': 1440, 'left': 260, 'right': 260}, orientation=1)

    rect = Rect.init_width_point_size(Anchor.point(0, 0), Anchor.size(1920, 1080))
    img = image('emulator-5554.png')
    #
    im_search = image('star.png').resize(62 * 1.33333, 43 * 1.33333)
    a = find_templates(im_source=img, im_search=im_search)
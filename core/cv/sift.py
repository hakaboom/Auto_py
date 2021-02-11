# -*- coding: utf-8 -*-
"""
1。 建立高斯差分金字塔
2。 确认关键点
"""
import cv2
import numpy as np
from core.cv.match_template import cal_rgb_confidence
from coordinate import Rect, Size


class SIFT(object):

    FLANN_INDEX_KDTREE = 0
    FILTER_RATIO = 0.5

    def __init__(self):
        # 创建SIFT实例
        self.sift = cv2.SIFT_create()
        # 指定待处理核密度树的数量
        index_params = dict(algorithm=self.FLANN_INDEX_KDTREE, trees=5)
        # 指定递归遍历的次数. 值越高结果越准确，但是消耗的时间也越多
        search_params = dict(checks=50)
        self.flann = cv2.FlannBasedMatcher(index_params, search_params)

    def find_sift(self, im_source, im_search, threshold:int = 0.8):
        """基于FlannBasedMatcher的SIFT实现"""
        # 第一步: 获取特征点集并匹配出特征点对
        kp_sch, kp_src, good = self.get_key_points(im_search=im_search, im_source=im_source)
        # 第二步：根据匹配点对(good),提取出来识别区域:
        if len(good) == 0:
            # 没有匹配点,直接返回None
            return None
        elif len(good) >= 5:
            # 匹配点大于5,使用单矩阵映射求出目标区域
            rect = self._many_good_pts(im_source, im_search, kp_sch, kp_src, good)
        # 第三步：根据识别区域，通过模板匹配,求出结果可信度，并将结果进行返回:
        x_min, y_min = rect.tl.x, rect.tl.y
        x_max, y_max = rect.br.x, rect.br.y
        target_img = im_source[y_min:y_max, x_min:x_max]
        h, w = im_search.shape[:2]
        sch_size = Size(width=w, height=h)
        if sch_size < rect.size:
            # 如果模板比目标区域小则：缩小截取的图像, 缩小成模板的大小
            im_search = cv2.resize(im_search, (rect.width, rect.height), interpolation=cv2.INTER_LANCZOS4)
        elif sch_size > rect.size:
            # 如果模板比目标区域大则：缩小模板的图像, 缩小成目标区域大小
            target_img = cv2.resize(target_img, (w, h), interpolation=cv2.INTER_LANCZOS4)

        confidence = self._cal_sift_confidence(resize_img=target_img, im_search=im_search)
        print(confidence)

    def get_keypoints_and_descriptors(self, image):
        """获取图像特征点和描述符."""
        keypoints, descriptors = self.sift.detectAndCompute(image, None)
        return keypoints, descriptors

    def match_keypoints(self, des_sch, des_src):
        """Match descriptors (特征值匹配)."""
        # 匹配两个图片中的特征点集，k=2表示每个特征点取出2个最匹配的对应点:
        return self.flann.knnMatch(des_sch, des_src, k=2)

    def get_key_points(self, im_source, im_search):
        """计算所以特征点,并匹配"""
        kp_sch, des_sch = self.get_keypoints_and_descriptors(image=im_search)
        kp_src, des_src = self.get_keypoints_and_descriptors(image=im_source)
        matches = self.match_keypoints(des_sch=des_sch, des_src=des_src)
        good = []
        for m, n in matches:
            if m.distance < self.FILTER_RATIO * n.distance:
                good.append(m)
        return kp_sch, kp_src, good

    def _many_good_pts(self, im_source, im_search, kp_sch, kp_src, good) -> Rect:
        sch_pts, img_pts = np.float32([kp_sch[m.queryIdx].pt for m in good]).reshape(
            -1, 1, 2), np.float32([kp_src[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        M, mask = cv2.findHomography(sch_pts, img_pts, cv2.RANSAC, 5.0)
        matches_mask = mask.ravel().tolist()
        # 计算四个角矩阵变换后的坐标，也就是在大图中的目标区域的顶点坐标:
        h, w = im_search.shape[:2]
        h_s, w_s = im_source.shape[:2]
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, M)

        # trans numpy arrary to python list: [(a, b), (a1, b1), ...]
        def cal_rect_pts(dst):
            return [tuple(npt[0]) for npt in dst.astype(int).tolist()]

        pypts = cal_rect_pts(dst)
        # 注意：虽然4个角点有可能越出source图边界，但是(根据精确化映射单映射矩阵M线性机制)中点不会越出边界
        lt, br = pypts[0], pypts[2]
        middle_point = int((lt[0] + br[0]) / 2), int((lt[1] + br[1]) / 2)
        # 考虑到算出的目标矩阵有可能是翻转的情况，必须进行一次处理，确保映射后的“左上角”在图片中也是左上角点：
        x_min, x_max = min(lt[0], br[0]), max(lt[0], br[0])
        y_min, y_max = min(lt[1], br[1]), max(lt[1], br[1])
        # 挑选出目标矩形区域可能会有越界情况，越界时直接将其置为边界：
        # 超出左边界取0，超出右边界取w_s-1，超出下边界取0，超出上边界取h_s-1
        # 当x_min小于0时，取0。  x_max小于0时，取0。
        x_min, x_max = int(max(x_min, 0)), int(max(x_max, 0))
        # 当x_min大于w_s时，取值w_s-1。  x_max大于w_s-1时，取w_s-1。
        x_min, x_max = int(min(x_min, w_s - 1)), int(min(x_max, w_s - 1))
        # 当y_min小于0时，取0。  y_max小于0时，取0。
        y_min, y_max = int(max(y_min, 0)), int(max(y_max, 0))
        # 当y_min大于h_s时，取值h_s-1。  y_max大于h_s-1时，取h_s-1。
        y_min, y_max = int(min(y_min, h_s - 1)), int(min(y_max, h_s - 1))
        return Rect(x=x_min, y=y_min, width=(x_max-x_min), height=(y_max-y_min))

    def _cal_sift_confidence(self, im_search, resize_img):
        confidence = cal_rgb_confidence(img_src_rgb=im_search, img_sch_rgb=resize_img)
        confidence = (1 + confidence) / 2
        return confidence
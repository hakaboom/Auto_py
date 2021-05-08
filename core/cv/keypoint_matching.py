#! usr/bin/python
# -*- coding:utf-8 -*-
import cv2
from core.cv.keypoint_base import KeypointMatch


class SIFT(KeypointMatch):
    # SIFT识别特征点匹配，参数设置:
    FLANN_INDEX_KDTREE = 0

    def __init__(self):
        super(SIFT, self).__init__()
        # 创建SIFT实例
        self.detector = cv2.SIFT_create(edgeThreshold=10)
        # 指定待处理核密度树的数量
        index_params = dict(algorithm=self.FLANN_INDEX_KDTREE, trees=5)
        # 指定递归遍历的次数. 值越高结果越准确，但是消耗的时间也越多
        search_params = dict(checks=50)
        self.flann = cv2.FlannBasedMatcher(index_params, search_params)

    def get_keypoints_and_descriptors(self, image):
        """获取图像特征点和描述符."""
        keypoints, descriptors = self.detector.detectAndCompute(image, None)
        return keypoints, descriptors

    def match_keypoints(self, des_sch, des_src):
        """Match descriptors (特征值匹配)."""
        # 匹配两个图片中的特征点集，k=2表示每个特征点取出2个最匹配的对应点:
        return self.flann.knnMatch(des_sch, des_src, k=2)


class SURF(KeypointMatch):
    # https://docs.opencv.org/master/d5/df7/classcv_1_1xfeatures2d_1_1SURF.html

    # 方向不变性:0检测/1不检测
    UPRIGHT = 0
    # 检测器仅保留其hessian大于hessianThreshold的要素,值越大,获得的关键点就越少
    HESSIAN_THRESHOLD = 400
    # SURF识别特征点匹配:
    FLANN_INDEX_KDTREE = 0

    def __init__(self):
        super(SURF, self).__init__()
        self.detector = cv2.xfeatures2d.SURF_create(self.HESSIAN_THRESHOLD, upright=self.UPRIGHT)
        # 指定待处理核密度树的数量
        index_params = dict(algorithm=self.FLANN_INDEX_KDTREE, trees=5)
        # 指定递归遍历的次数. 值越高结果越准确，但是消耗的时间也越多
        search_params = dict(checks=50)
        self.flann = cv2.FlannBasedMatcher(index_params, search_params)

    def get_keypoints_and_descriptors(self, image):
        """获取图像特征点和描述符."""
        keypoints, descriptors = self.detector.detectAndCompute(image, None)
        return keypoints, descriptors

    def match_keypoints(self, des_sch, des_src):
        """Match descriptors (特征值匹配)."""
        # 匹配两个图片中的特征点集，k=2表示每个特征点取出2个最匹配的对应点:
        return self.flann.knnMatch(des_sch, des_src, k=2)

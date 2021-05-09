#! usr/bin/python
# -*- coding:utf-8 -*-
import cv2
from core.cv.keypoint_base import KeypointMatch
from core.cv.base_image import IMAGE


class ORB(KeypointMatch):
    # ORB识别特征点匹配，参数设置:
    FLANN_INDEX_KDTREE = 0

    def __init__(self):
        super(ORB, self).__init__()
        # 创建ORB实例
        self.detector = cv2.ORB_create()


class SIFT(KeypointMatch):
    METHOD_NAME = "SIFT"
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
    METHOD_NAME = "SURF"
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


class _CUDA_SURF(KeypointMatch):
    # https://docs.opencv.org/master/db/d06/classcv_1_1cuda_1_1SURF__CUDA.html
    METHOD_NAME = 'CUDA_SURF'
    # 方向不变性:0检测/1不检测
    UPRIGHT = 0
    # 检测器仅保留其hessian大于hessianThreshold的要素,值越大,获得的关键点就越少
    HESSIAN_THRESHOLD = 400
    # SURF识别特征点匹配:
    FLANN_INDEX_KDTREE = 0

    def __init__(self):
        super(_CUDA_SURF, self).__init__()
        self.detector = cv2.cuda.SURF_CUDA_create(self.HESSIAN_THRESHOLD)
        self.flann = cv2.cuda.DescriptorMatcher_createBFMatcher(cv2.NORM_L2)

    def check_detection_input(self, im_source, im_search):
        im_source = IMAGE(im_source)
        im_search = IMAGE(im_search)
        im_source.transform_gpu()
        im_search.transform_gpu()
        self.check_image(im_source)
        self.check_image(im_search)
        return im_source, im_search

    def check_image(self, image):
        # https://stackoverflow.com/questions/42492060/surf-cuda-error-while-computing-descriptors-and-keypoints
        # https://github.com/opencv/opencv_contrib/blob/master/modules/xfeatures2d/src/surf.cuda.cpp#L151
        # SURF匹配特征点时,无法处理长宽太小的图片
        # (9 + 6 * 0) << nOctaves-1
        def calcSize(octave, layer):
            HAAR_SIZE0 = 9
            HAAR_SIZE_INC = 6
            # return '{}{}'.format((HAAR_SIZE0 + HAAR_SIZE_INC * layer), octave)
            return (HAAR_SIZE0 + HAAR_SIZE_INC * layer) << octave

        min_size = int(calcSize(self.detector.nOctaves - 1, 0))
        if image.shape[0] - min_size < 0 or image.shape[1] - min_size < 0:
            if image.shape[0] <= image.shape[1]:
                percent = min_size / image.shape[0]
                height = min_size
                width = int(image.shape[1] * percent)
            else:
                percent = min_size / image.shape[1]
                height = int(image.shape[0] * percent)
                width = min_size
            image.resize(width, height)
        layer_height = image.shape[0] >> (self.detector.nOctaves - 1)
        layer_width = image.shape[1] >> (self.detector.nOctaves - 1)
        min_margin = ((calcSize((self.detector.nOctaves - 1), 2) >> 1) >> (self.detector.nOctaves - 1)) + 1
        if layer_height - 2 * min_margin < 0 or layer_width - 2 * min_margin < 0:
            # print(layer_height, layer_width, min_margin, image.shape)
            if image.shape[0] <= image.shape[1]:
                height = (2 * min_margin + 1 << (self.detector.nOctaves - 1))
                width = int(image.shape[1] * height / image.shape[0])
            else:
                width = (2 * min_margin + 1 << (self.detector.nOctaves - 1))
                height = int(image.shape[0] * width / image.shape[1])
            image.resize(width, height)

    def get_keypoints_and_descriptors(self, image):
        """获取图像特征点和描述符."""
        keypoints, descriptors = self.detector.detectWithDescriptors(image, None)
        return keypoints, descriptors

    def get_key_points(self, im_source, im_search):
        """计算所有特征点,并匹配"""
        im_source, im_search = im_source.rgb_2_gray(), im_search.rgb_2_gray()
        kp_sch, des_sch = self.get_keypoints_and_descriptors(image=im_search)
        kp_src, des_src = self.get_keypoints_and_descriptors(image=im_source)
        matches = self.match_keypoints(des_sch=des_sch, des_src=des_src)
        good = []
        for m, n in matches:
            if m.distance < self.FILTER_RATIO * n.distance:
                good.append(m)
        kp_sch = cv2.cuda_SURF_CUDA.downloadKeypoints(self.detector, kp_sch)
        kp_src = cv2.cuda_SURF_CUDA.downloadKeypoints(self.detector, kp_src)
        return kp_sch, kp_src, good

    def match_keypoints(self, des_sch, des_src):
        """Match descriptors (特征值匹配)."""
        # 匹配两个图片中的特征点集，k=2表示每个特征点取出2个最匹配的对应点:
        return self.flann.knnMatch(des_sch, des_src, k=2)
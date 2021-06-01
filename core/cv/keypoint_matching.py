#! usr/bin/python
# -*- coding:utf-8 -*-
import cv2
from core.cv.keypoint_base import KeypointMatch
from core.cv.base_image import IMAGE
from core.error import SurfCudaError
from loguru import logger


class _ORB(KeypointMatch):
    METHOD_NAME = "ORB"

    def __init__(self):
        super(_ORB, self).__init__()
        # 创建ORB实例
        self.detector = cv2.ORB_create(nfeatures=5000)
        self.descriptor = cv2.xfeatures2d.BEBLID_create(0.75)

    def create_matcher(self):
        # https://github.com/iago-suarez/beblid-opencv-demo
        self.matcher = cv2.DescriptorMatcher_create(cv2.DescriptorMatcher_BRUTEFORCE_HAMMING)

    def get_key_points(self, im_source, im_search):
        """计算所有特征点,并匹配"""
        im_source, im_search = im_source.imread(), im_search.imread()
        kp_sch, des_sch = self.get_keypoints_and_descriptors(image=im_search)
        kp_src, des_src = self.get_keypoints_and_descriptors(image=im_source)
        matches = self.match_keypoints(des_sch=des_sch, des_src=des_src)
        good = []
        # 出现过matches对中只有1个参数的情况,会导致遍历的时候造成报错
        for v in matches:
            if len(v) == 2:
                if v[0].distance < self.FILTER_RATIO * v[1].distance:
                    good.append(v[0])
        return kp_sch, kp_src, good

    def get_keypoints_and_descriptors(self, image):
        keypoints = self.detector.detect(image, None)
        keypoints, descriptors = self.descriptor.compute(image, keypoints)
        return keypoints, descriptors


class SIFT(KeypointMatch):
    METHOD_NAME = "SIFT"
    # SIFT识别特征点匹配，参数设置:
    FLANN_INDEX_KDTREE = 0

    def __init__(self):
        super(SIFT, self).__init__()
        # 创建SIFT实例
        self.detector = cv2.SIFT_create(edgeThreshold=10)


class _SURF(KeypointMatch):
    # https://docs.opencv.org/master/d5/df7/classcv_1_1xfeatures2d_1_1SURF.html
    METHOD_NAME = "SURF"
    # 方向不变性:0检测/1不检测
    UPRIGHT = 0
    # 检测器仅保留其hessian大于hessianThreshold的要素,值越大,获得的关键点就越少
    HESSIAN_THRESHOLD = 400
    # SURF识别特征点匹配:
    FLANN_INDEX_KDTREE = 0

    def __init__(self):
        super(_SURF, self).__init__()
        self.detector = cv2.xfeatures2d.SURF_create(self.HESSIAN_THRESHOLD, upright=self.UPRIGHT)


class BRIEF(KeypointMatch):
    METHOD_NAME = "BRIEF"

    def __init__(self):
        super(BRIEF, self).__init__()
        # Initiate FAST detector
        self.star = cv2.xfeatures2d.StarDetector_create()
        # Initiate BRIEF extractor
        self.detector = cv2.xfeatures2d.BriefDescriptorExtractor_create()

    def create_matcher(self):
        self.matcher = cv2.BFMatcher_create(cv2.NORM_L1)

    def get_keypoints_and_descriptors(self, image):
        # find the keypoints with STAR
        kp = self.star.detect(image, None)
        # compute the descriptors with BRIEF
        keypoints, descriptors = self.detector.compute(image, kp)
        return keypoints, descriptors


class AKAZE(KeypointMatch):
    METHOD_NAME = "AKAZE"

    def __init__(self):
        super(AKAZE, self).__init__()
        # Initiate AKAZE detector
        self.detector = cv2.AKAZE_create()
        # create BFMatcher object:
        self.matcher = cv2.BFMatcher(cv2.NORM_L1)


class _CUDA_SURF(KeypointMatch):
    # https://docs.opencv.org/master/db/d06/classcv_1_1cuda_1_1SURF__CUDA.html
    METHOD_NAME = 'CUDA_SURF'
    # 方向不变性:True检测/False不检测
    UPRIGHT = False
    # 检测器仅保留其hessian大于hessianThreshold的要素,值越大,获得的关键点就越少
    HESSIAN_THRESHOLD = 400
    # SURF识别特征点匹配:
    FLANN_INDEX_KDTREE = 0

    def __init__(self):
        super(_CUDA_SURF, self).__init__()
        self.detector = cv2.cuda.SURF_CUDA_create(self.HESSIAN_THRESHOLD, _extended=True, _upright=self.UPRIGHT,
                                                  _nOctaveLayers=4)
        self.matcher = cv2.cuda.DescriptorMatcher_createBFMatcher(cv2.NORM_L2)

    def check_detection_input(self, im_source, im_search):
        im_source = IMAGE(im_source)
        im_search = IMAGE(im_search)
        im_source.transform_gpu()
        im_search.transform_gpu()
        im_source, im_search = self.check_image_size(im_source, im_search)
        return im_source, im_search

    def check_image_size(self, im_source, im_search):
        try:
            self._check_image_size(im_source)
            self._check_image_size(im_search)
        except SurfCudaError as err:
            logger.error('image size is to small: {}', err)
            return None, None
        return im_source, im_search

    def _check_image_size(self, image):
        # https://stackoverflow.com/questions/42492060/surf-cuda-error-while-computing-descriptors-and-keypoints
        # https://github.com/opencv/opencv_contrib/blob/master/modules/xfeatures2d/src/surf.cuda.cpp#L151
        # SURF匹配特征点时,无法处理长宽太小的图片
        # (9 + 6 * 0) << nOctaves-1

        def calc_size(octave, layer):
            HAAR_SIZE0 = 9
            HAAR_SIZE_INC = 6
            # return '{}{}'.format((HAAR_SIZE0 + HAAR_SIZE_INC * layer), octave)
            return (HAAR_SIZE0 + HAAR_SIZE_INC * layer) << octave

        min_size = int(calc_size(self.detector.nOctaves - 1, 0))
        layer_height = image.size[0] >> (self.detector.nOctaves - 1)
        layer_width = image.size[1] >> (self.detector.nOctaves - 1)
        min_margin = ((calc_size((self.detector.nOctaves - 1), 2) >> 1) >> (self.detector.nOctaves - 1)) + 1

        if image.size[0] - min_size < 0 or image.size[1] - min_size < 0:
            raise SurfCudaError(image)
        if layer_height - 2 * min_margin < 0 or layer_width - 2 * min_margin < 0:
            raise SurfCudaError(image)

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
        # print('{}:kp_sch={}，kp_src={}, good={}'.format(self.METHOD_NAME,
        # str(len(kp_sch)), str(len(kp_src)), str(len(good))))
        # cv2.namedWindow(str(len(kp_src) + 3), cv2.WINDOW_KEEPRATIO)
        # cv2.imshow(str(len(kp_src)+1), cv2.drawKeypoints(im_source.download(), kp_src, im_source.download(),
        #                                                  color=(255, 0, 255)))
        # cv2.imshow(str(len(kp_src)+2), cv2.drawKeypoints(im_search.download(), kp_sch, im_search.download(),
        #                                                  color=(255, 0, 255)))
        # cv2.imshow(str(len(kp_src)+3), cv2.drawMatches(im_search.download(), kp_sch, im_source.download(), kp_src,
        #                                            good, None, flags=2))
        # cv2.waitKey(0)
        return kp_sch, kp_src, good


class _CUDA_ORB(KeypointMatch):
    METHOD_NAME = 'CUDA_ORB'

    def __init__(self):
        super(_CUDA_ORB, self).__init__()
        self.detector = cv2.cuda_ORB.create(nfeatures=5000)

    def check_detection_input(self, im_source, im_search):
        im_source = IMAGE(im_source)
        im_search = IMAGE(im_search)
        im_source.transform_gpu()
        im_search.transform_gpu()
        return im_source, im_search

    def create_matcher(self):
        # https://github.com/iago-suarez/beblid-opencv-demo
        # self.matcher = cv2.DescriptorMatcher_create(cv2.DescriptorMatcher_BRUTEFORCE_HAMMING)
        self.matcher = cv2.cuda_DescriptorMatcher.createBFMatcher(cv2.NORM_HAMMING)

    def get_keypoints_and_descriptors(self, image):
        # https://github.com/prismai/opencv_contrib/commit/d7d6360fceb5881d596be95b03568d4dcdb7236d
        keypoints, descriptors = self.detector.detectAndComputeAsync(image, None)
        keypoints = self.detector.convert(keypoints)
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
        return kp_sch, kp_src, good


if cv2.cuda.getCudaEnabledDeviceCount() > 0:
    class SURF(_CUDA_SURF):
        pass

    class ORB(_CUDA_ORB):
        pass
else:
    class SURF(_SURF):
        pass

    class ORB(_ORB):
        pass

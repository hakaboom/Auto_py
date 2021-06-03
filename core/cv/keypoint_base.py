#! usr/bin/python
# -*- coding:utf-8 -*-
import time
import cv2
import numpy as np
from core.cv.utils import create_similar_rect, generate_result
from core.cv.match_template import match_template
from core.utils.coordinate import Rect, Point, Size
from core.cv.base_image import IMAGE
from loguru import logger


class KeypointMatch(object):
    FLANN_INDEX_KDTREE = 0
    FILTER_RATIO = 0.59
    METHOD_NAME = 'KeypointMatch'

    def __init__(self, threshold=0.8):
        self.threshold = threshold
        self.matcher = None
        self.create_matcher()

    def create_matcher(self):
        index_params = {'algorithm': self.FLANN_INDEX_KDTREE, 'tree': 5}
        # 指定递归遍历的次数. 值越高结果越准确，但是消耗的时间也越多
        search_params = {'checks': 50}
        self.matcher = cv2.FlannBasedMatcher(index_params, search_params)

    def find_best(self, img_source, img_search, threshold=0.8):
        """基于FlannBasedMatcher的SIFT实现"""
        threshold = threshold or self.threshold
        start_time = time.time()
        img_source, img_search = self.check_detection_input(img_source, img_search)
        if not img_source or not img_search:
            return None
        # 第一步: 获取特征点集并匹配出特征点对
        kp_sch, kp_src, good = self.get_key_points(img_search=img_search, img_source=img_source)
        self.show_keypoints_and_descriptors(img_search, img_source, kp_sch, kp_src, good)
        # 第二步：根据匹配点对(good),提取出来识别区域:
        rect = self.extract_good_points(img_source, img_search, kp_sch, kp_src, good)
        if not rect:
            return None
        # 第三步,通过识别矩阵周围+-1像素的矩阵,求出结果可信度，并且返回最大精准度的范围
        confidences = []
        similar_rect = create_similar_rect(rect.x, rect.y, rect.width, rect.height)
        h, w = img_search.size
        for i in similar_rect:
            # cv2.matchTemplate 目标和模板长宽不能一大一小
            try:
                target_img = img_source.crop_image(i)
                target_img.resize(w, h)
                confidences.append(self._cal_confidence(resize_img=target_img, img_search=img_search))
            except:
                pass
        # 提取最大值
        if confidences:
            confidence = max(confidences)
            rect = similar_rect[confidences.index(confidence)]
        else:
            confidence = 0
        best_match = generate_result(rect=rect, confi=confidence)
        logger.info('[{method_name}]:{Rect}, confidence=(max={max_confidence:.5f},min={min_confidence:.5f}), '
                    'time={time:.1f}ms, kp_sch={kp_sch}, kp_src={kp_src}, good={good}',
                    max_confidence=max(confidences), min_confidence=min(confidences),
                    Rect=rect, time=(time.time() - start_time) * 1000, method_name=self.METHOD_NAME,
                    kp_sch=len(kp_sch), kp_src=len(kp_src), good=len(good))
        return best_match if confidence > threshold else None

    @staticmethod
    def check_detection_input(img_source, img_search):
        if not isinstance(img_source, IMAGE):
            img_source = IMAGE(img_source)
        if not isinstance(img_search, IMAGE):
            img_search = IMAGE(img_search)
        return img_source, img_search

    def extract_good_points(self, img_source, img_search, kp_sch, kp_src, good):
        if len(good) in [0, 1]:
            # origin_result = self._handle_one_good_points(im_source, im_search, kp_src, kp_sch, good)
            return None
        elif len(good) in [2, 3]:
            if len(good) == 2:
                # 匹配点对为2，根据点对求出目标区域，据此算出可信度：
                origin_result = self._handle_two_good_points(img_source, img_search, kp_src, kp_sch, good)
            else:
                origin_result = self._handle_three_good_points(img_source, img_search, kp_sch, kp_src, good)
            if isinstance(origin_result, dict):
                return None
            else:
                return origin_result
        else:
            # 匹配点大于4,使用单矩阵映射求出目标区域
            return self._many_good_pts(img_source, img_search, kp_sch, kp_src, good)

    def get_key_points(self, img_source, img_search):
        """计算所有特征点,并匹配"""
        img_source, img_search = img_source.imread(), img_search.imread()
        kp_sch, des_sch = self.get_keypoints_and_descriptors(image=img_search)
        kp_src, des_src = self.get_keypoints_and_descriptors(image=img_source)
        matches = self.match_keypoints(des_sch=des_sch, des_src=des_src)
        good = []
        for m, n in matches:
            if m.distance < self.FILTER_RATIO * n.distance:
                good.append(m)
        return kp_sch, kp_src, good

    def get_keypoints_and_descriptors(self, image):
        keypoints, descriptors = self.detector.detectAndCompute(image, None)
        return keypoints, descriptors

    def match_keypoints(self, des_sch, des_src):
        """Match descriptors (特征值匹配)."""
        # 匹配两个图片中的特征点集，k=2表示每个特征点取出2个最匹配的对应点:
        return self.matcher.knnMatch(des_sch, des_src, 2)

    def _handle_one_good_points(self, img_source, img_search, kp_src, kp_sch, good):
        """sift匹配中只有一对匹配的特征点对的情况."""
        """此方法当前废弃"""
        # 取出该点在图中的位置
        sch_point = Point(int(kp_sch[0].pt[0]), int(kp_sch[0].pt[1]))
        src_point = Point(int(kp_src[good[0].trainIdx].pt[0]), int(kp_src[good[0].trainIdx].pt[1]))
        # 求出模板原点在匹配图像上的坐标
        offset_point = src_point - sch_point
        rect = Rect.create_by_point_size(offset_point, Size(img_search.shape[1], img_search.shape[0]))
        logger.debug('rect={},sch={}, src={}, offset={}', rect, sch_point, src_point, offset_point)
        return rect

    def _handle_two_good_points(self, img_source, img_search, kp_src, kp_sch, good):
        """处理两对特征点的情况."""
        pts_sch1 = int(kp_sch[good[0].queryIdx].pt[0]), int(kp_sch[good[0].queryIdx].pt[1])
        pts_sch2 = int(kp_sch[good[1].queryIdx].pt[0]), int(kp_sch[good[1].queryIdx].pt[1])
        pts_src1 = int(kp_src[good[0].trainIdx].pt[0]), int(kp_src[good[0].trainIdx].pt[1])
        pts_src2 = int(kp_src[good[1].trainIdx].pt[0]), int(kp_src[good[1].trainIdx].pt[1])

        return self._two_good_points(pts_sch1, pts_sch2, pts_src1, pts_src2, img_search, img_source)

    def _handle_three_good_points(self, img_source, img_search, kp_sch, kp_src, good):
        """处理三对特征点的情况."""
        # 拿出sch和src的两个点(点1)和(点2点3的中点)，
        # 然后根据两个点原则进行后处理(注意ke_sch和kp_src以及queryIdx和trainIdx):
        pts_sch1 = int(kp_sch[good[0].queryIdx].pt[0]), int(kp_sch[good[0].queryIdx].pt[1])
        pts_sch2 = int((kp_sch[good[1].queryIdx].pt[0] + kp_sch[good[2].queryIdx].pt[0]) / 2), int(
            (kp_sch[good[1].queryIdx].pt[1] + kp_sch[good[2].queryIdx].pt[1]) / 2)
        pts_src1 = int(kp_src[good[0].trainIdx].pt[0]), int(kp_src[good[0].trainIdx].pt[1])
        pts_src2 = int((kp_src[good[1].trainIdx].pt[0] + kp_src[good[2].trainIdx].pt[0]) / 2), int(
            (kp_src[good[1].trainIdx].pt[1] + kp_src[good[2].trainIdx].pt[1]) / 2)
        return self._two_good_points(pts_sch1, pts_sch2, pts_src1, pts_src2, img_search, img_source)

    @staticmethod
    def _find_homography(sch_pts, src_pts):
        """多组特征点对时，求取单向性矩阵."""
        try:
            M, mask = cv2.findHomography(sch_pts, src_pts, cv2.RANSAC, 5.0)
        except Exception:
            import traceback
            traceback.print_exc()
            raise Exception("OpenCV error in _find_homography()...")
        else:
            if mask is None:
                raise Exception("In _find_homography(), find no mask...")
            else:
                return M, mask

    def _many_good_pts(self, img_source, img_search, kp_sch, kp_src, good) -> Rect:
        sch_pts, img_pts = np.float32([kp_sch[m.queryIdx].pt for m in good]).reshape(
            -1, 1, 2), np.float32([kp_src[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        # M是转化矩阵
        M, mask = self._find_homography(sch_pts, img_pts)
        matches_mask = mask.ravel().tolist()
        # 从good中间筛选出更精确的点(假设good中大部分点为正确的，由ratio=0.7保障)
        selected = [v for k, v in enumerate(good) if matches_mask[k]]

        # 针对所有的selected点再次计算出更精确的转化矩阵M来
        sch_pts, img_pts = np.float32([kp_sch[m.queryIdx].pt for m in selected]).reshape(
            -1, 1, 2), np.float32([kp_src[m.trainIdx].pt for m in selected]).reshape(-1, 1, 2)
        M, mask = self._find_homography(sch_pts, img_pts)
        # 计算四个角矩阵变换后的坐标，也就是在大图中的目标区域的顶点坐标:
        h, w = img_search.shape[:2]
        h_s, w_s = img_source.shape[:2]
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, M)

        # trans numpy arrary to python list: [(a, b), (a1, b1), ...]

        def cal_rect_pts(_dst):
            return [tuple(npt[0]) for npt in np.rint(_dst).astype(np.float).tolist()]

        pypts = cal_rect_pts(dst)
        # pypts四个值按照顺序分别是: 左上,左下,右下,右上
        # 注意：虽然4个角点有可能越出source图边界，但是(根据精确化映射单映射矩阵M线性机制)中点不会越出边界
        lt, br = pypts[0], pypts[2]
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
        return Rect(x=x_min, y=y_min, width=(x_max - x_min), height=(y_max - y_min))

    def _cal_confidence(self, img_search, resize_img):
        confidence = match_template.cal_rgb_confidence(img_src_rgb=img_search, img_sch_rgb=resize_img)
        confidence = (1 + confidence) / 2
        return confidence

    def _two_good_points(self, pts_sch1, pts_sch2, pts_src1, pts_src2, img_search, img_source):
        """返回两对匹配特征点情形下的识别结果."""
        # 先算出中心点(在im_source中的坐标)：
        middle_point = [int((pts_src1[0] + pts_src2[0]) / 2), int((pts_src1[1] + pts_src2[1]) / 2)]
        pypts = []
        # 如果特征点同x轴或同y轴(无论src还是sch中)，均不能计算出目标矩形区域来，此时返回值同good=1情形
        if pts_sch1[0] == pts_sch2[0] or pts_sch1[1] == pts_sch2[1] or pts_src1[0] == pts_src2[0] or pts_src1[1] == \
                pts_src2[1]:
            confidence = 0.5
            return {'result': middle_point, 'rectangle': pypts, 'confidence': confidence}
        # 计算x,y轴的缩放比例：x_scale、y_scale，从middle点扩张出目标区域:(注意整数计算要转成浮点数结果!)
        h, w = img_search.size[:2]
        h_s, w_s = img_source.size[:2]
        x_scale = abs(1.0 * (pts_src2[0] - pts_src1[0]) / (pts_sch2[0] - pts_sch1[0]))
        y_scale = abs(1.0 * (pts_src2[1] - pts_src1[1]) / (pts_sch2[1] - pts_sch1[1]))
        # 得到scale后需要对middle_point进行校正，并非特征点中点，而是映射矩阵的中点。
        sch_middle_point = int((pts_sch1[0] + pts_sch2[0]) / 2), int((pts_sch1[1] + pts_sch2[1]) / 2)
        middle_point[0] = middle_point[0] - int((sch_middle_point[0] - w / 2) * x_scale)
        middle_point[1] = middle_point[1] - int((sch_middle_point[1] - h / 2) * y_scale)
        middle_point[0] = max(middle_point[0], 0)  # 超出左边界取0  (图像左上角坐标为0,0)
        middle_point[0] = min(middle_point[0], w_s - 1)  # 超出右边界取w_s-1
        middle_point[1] = max(middle_point[1], 0)  # 超出上边界取0
        middle_point[1] = min(middle_point[1], h_s - 1)  # 超出下边界取h_s-1

        # 计算出来rectangle角点的顺序：左上角->左下角->右下角->右上角， 注意：暂不考虑图片转动
        # 超出左边界取0, 超出右边界取w_s-1, 超出下边界取0, 超出上边界取h_s-1
        x_min, x_max = int(max(middle_point[0] - (w * x_scale) / 2, 0)), int(
            min(middle_point[0] + (w * x_scale) / 2, w_s - 1))
        y_min, y_max = int(max(middle_point[1] - (h * y_scale) / 2, 0)), int(
            min(middle_point[1] + (h * y_scale) / 2, h_s - 1))
        # 目标矩形的角点按左上、左下、右下、右上的点序：(x_min,y_min)(x_min,y_max)(x_max,y_max)(x_max,y_min)
        pts = np.float32([[x_min, y_min], [x_min, y_max], [x_max, y_max], [x_max, y_min]]).reshape(-1, 1, 2)
        for npt in pts.astype(int).tolist():
            pypts.append(tuple(npt[0]))
        return Rect(x=x_min, y=y_min, width=(x_max - x_min), height=(y_max - y_min))

    def show_keypoints_and_descriptors(self, img_search, img_source, kp_sch, kp_src, good):
        img_source, img_search = IMAGE(img_source), IMAGE(img_search)
        print('{}:kp_sch={}，kp_src={}, good={}'.format(self.METHOD_NAME,
                                                       str(len(kp_sch)), str(len(kp_src)), str(len(good))))
        cv2.namedWindow(str(len(good) + 1), cv2.WINDOW_KEEPRATIO)
        img_search, img_source = img_search.imread(), img_source.imread()
        cv2.imshow(str(len(good)), cv2.drawMatches(img_search, kp_sch, img_source, kp_src, good, None, flags=2))
        cv2.imshow(str(len(good) + 1), cv2.drawKeypoints(img_source, kp_src, img_source, color=(255, 0, 255)))
        cv2.imshow(str(len(good) + 2), cv2.drawKeypoints(img_search, kp_sch, img_search, color=(255, 0, 255)))
        cv2.waitKey(0)


if __name__ == '__main__':
    from core.cv.base_image import IMAGE
    from core.cv.keypoint_matching import SIFT, SURF, ORB, BRIEF, AKAZE
    from core.cv.match_template import match_template

    sift = SIFT()
    surf = SURF()
    orb = ORB()
    brief = BRIEF()
    match = match_template()
    akaze = AKAZE()
    im_search = IMAGE('./core/cv/test_image/ship.png')
    im_source = IMAGE('./core/cv/test_image/test1.png')
    startTime = time.time()
    for i in range(100):
        # a = surf.find_best(img_search=im_search, img_source=im_source)
        # b = sift.find_best(img_search=im_search, img_source=im_source)
        c = orb.find_best(img_search=im_search, img_source=im_source)
        # d = brief.find_best(img_search=im_search, img_source=im_source)
        # e = match.find_template(img_search=im_search, img_source=im_source)
        # f = akaze.find_best(img_search=im_search, img_source=im_source)
        # im_source.crop_image(c["rect"]).imshow()
        # cv2.waitKey(0)

    endTime = time.time()
    print('useTime={time:.1f}ms'.format(time=(endTime - startTime) * 1000))

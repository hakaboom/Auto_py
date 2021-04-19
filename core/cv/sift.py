# -*- coding: utf-8 -*-
"""
需要解决的问题:
    SIFT 获取图像特征点和描述符时间太长
"""
import time
import cv2
import numpy as np
from numpy import ndarray
from core.cv.utils import create_similar_rect, generate_result
from core.cv.base_image import check_detection_input
from core.cv.match_template import cal_rgb_confidence
from core.utils.coordinate import Rect, Size


class SIFT(object):
    FLANN_INDEX_KDTREE = 0
    FILTER_RATIO = 0.59
    ONE_POINT_CONFI = 0.5

    def __init__(self):
        # 创建SIFT实例
        self.sift = cv2.SIFT_create()
        # 指定待处理核密度树的数量
        index_params = dict(algorithm=self.FLANN_INDEX_KDTREE, trees=5)
        # 指定递归遍历的次数. 值越高结果越准确，但是消耗的时间也越多
        search_params = dict(checks=50)
        self.flann = cv2.FlannBasedMatcher(index_params, search_params)

    def find_sift(self, im_source, im_search, threshold: int = 0.8):
        """基于FlannBasedMatcher的SIFT实现"""
        start_time = time.time()
        im_source, im_search = check_detection_input(im_source, im_search)
        # 第一步: 获取特征点集并匹配出特征点对 (最耗时的一段)
        kp_sch, kp_src, good = self.get_key_points(im_search=im_search, im_source=im_source)
        # 第二步：根据匹配点对(good),提取出来识别区域:
        rect = self.extract_good_points(im_source, im_search, kp_sch, kp_src, good, threshold)
        if not rect:
            return None
        # 第三步,通过识别矩阵周围+-1像素的矩阵,求出结果可信度，并且返回最大精准度的范围
        confidences = []
        similar_rect = create_similar_rect(rect.x, rect.y, rect.width, rect.height)
        h, w = im_search.shape[:2]
        for i in similar_rect:
            # cv2.matchTemplate 目标和模板长宽不能一大一小
            target_img = im_source[i.tl.y:i.br.y, i.tl.x:i.br.x]
            target_img = cv2.resize(target_img, (w, h))
            confidences.append(self._cal_sift_confidence(resize_img=target_img, im_search=im_search))
        # 提取最大值
        if confidences:
            confidence = max(confidences)
            rect = similar_rect[confidences.index(confidence)]
        else:
            confidence = 0
        best_match = generate_result(rect=rect, confi=confidence)
        print('[sift]:{Rect}, confidence=(max={max_confidence:.5f},min={min_confidence:.5f}), time={time:.1f}ms'.
              format(max_confidence=max(confidences), min_confidence=min(confidences),
                     Rect=rect, time=(time.time() - start_time)*1000))
        return best_match if confidence > threshold else None

    def extract_good_points(self, im_source, im_search, kp_sch, kp_src, good, threshold):
        if len(good) == 0:
            # 没有匹配点,直接返回None
            return None
        elif len(good) == 1:
            # 匹配点对为1，可信度赋予设定值，并直接返回:
            origin_result = self._handle_one_good_points(kp_src, good, threshold)
            return None
        elif len(good) == 2:
            # 匹配点对为2，根据点对求出目标区域，据此算出可信度：
            origin_result = self._handle_two_good_points(im_source, im_search, kp_src, kp_sch, good)
            if isinstance(origin_result, dict):
                return None
            else:
                return origin_result
        elif len(good) == 3:
            # 匹配点对为3，取出点对，求出目标区域，据此算出可信度：
            origin_result = self._handle_three_good_points(im_source, im_search, kp_sch, kp_src, good)
            if isinstance(origin_result, dict):
                return None
            else:
                return origin_result
        else:
            # 匹配点大于4,使用单矩阵映射求出目标区域
            return self._many_good_pts(im_source, im_search, kp_sch, kp_src, good)

    def get_keypoints_and_descriptors(self, image):
        """获取图像特征点和描述符."""
        keypoints, descriptors = self.sift.detectAndCompute(image, None)
        return keypoints, descriptors

    def match_keypoints(self, des_sch, des_src):
        """Match descriptors (特征值匹配)."""
        # 匹配两个图片中的特征点集，k=2表示每个特征点取出2个最匹配的对应点:
        return self.flann.knnMatch(des_sch, des_src, k=2)

    def get_key_points(self, im_source, im_search):
        """计算所有特征点,并匹配"""
        kp_sch, des_sch = self.get_keypoints_and_descriptors(image=im_search)
        kp_src, des_src = self.get_keypoints_and_descriptors(image=im_source)
        matches = self.match_keypoints(des_sch=des_sch, des_src=des_src)
        good = []
        for m, n in matches:
            if m.distance < self.FILTER_RATIO * n.distance:
                good.append(m)
        # img = cv2.drawMatchesKnn(im_search, kp_sch, im_source, kp_src, np.expand_dims(good, 1), None, flags=2)
        # img = cv2.drawMatchesKnn(im_search, kp_sch, im_source, kp_src, matches, None, flags=2)
        # cv2.namedWindow('test', cv2.WINDOW_KEEPRATIO)
        # cv2.imshow('test', img)
        # cv2.waitKey(0)
        return kp_sch, kp_src, good

    def _handle_one_good_points(self, kp_src, good, threshold):
        """sift匹配中只有一对匹配的特征点对的情况."""
        # 识别中心即为该匹配点位置:
        middle_point = int(kp_src[good[0].trainIdx].pt[0]), int(kp_src[good[0].trainIdx].pt[1])
        confidence = self.ONE_POINT_CONFI
        # 单个特征点对,识别区域无效化:
        pypts = [middle_point for i in range(4)]
        return None if confidence > threshold else middle_point

    def _handle_two_good_points(self, im_source, im_search, kp_src, kp_sch, good):
        """处理两对特征点的情况."""
        pts_sch1 = int(kp_sch[good[0].queryIdx].pt[0]), int(kp_sch[good[0].queryIdx].pt[1])
        pts_sch2 = int(kp_sch[good[1].queryIdx].pt[0]), int(kp_sch[good[1].queryIdx].pt[1])
        pts_src1 = int(kp_src[good[0].trainIdx].pt[0]), int(kp_src[good[0].trainIdx].pt[1])
        pts_src2 = int(kp_src[good[1].trainIdx].pt[0]), int(kp_src[good[1].trainIdx].pt[1])

        return self._two_good_points(pts_sch1, pts_sch2, pts_src1, pts_src2, im_search, im_source)

    def _handle_three_good_points(self, im_source, im_search, kp_sch, kp_src, good):
        """处理三对特征点的情况."""
        # 拿出sch和src的两个点(点1)和(点2点3的中点)，
        # 然后根据两个点原则进行后处理(注意ke_sch和kp_src以及queryIdx和trainIdx):
        pts_sch1 = int(kp_sch[good[0].queryIdx].pt[0]), int(kp_sch[good[0].queryIdx].pt[1])
        pts_sch2 = int((kp_sch[good[1].queryIdx].pt[0] + kp_sch[good[2].queryIdx].pt[0]) / 2), int(
            (kp_sch[good[1].queryIdx].pt[1] + kp_sch[good[2].queryIdx].pt[1]) / 2)
        pts_src1 = int(kp_src[good[0].trainIdx].pt[0]), int(kp_src[good[0].trainIdx].pt[1])
        pts_src2 = int((kp_src[good[1].trainIdx].pt[0] + kp_src[good[2].trainIdx].pt[0]) / 2), int(
            (kp_src[good[1].trainIdx].pt[1] + kp_src[good[2].trainIdx].pt[1]) / 2)
        return self._two_good_points(pts_sch1, pts_sch2, pts_src1, pts_src2, im_search, im_source)

    @staticmethod
    def _find_homography(sch_pts, src_pts):
        """多组特征点对时，求取单向性矩阵."""
        try:
            M, mask = cv2.findHomography(sch_pts, src_pts, cv2.RANSAC, 5.0)
        except Exception:
            import traceback
            traceback.print_exc()
            raise BaseException("OpenCV error in _find_homography()...")
        else:
            if mask is None:
                raise BaseException("In _find_homography(), find no mask...")
            else:
                return M, mask

    def _many_good_pts(self, im_source, im_search, kp_sch, kp_src, good) -> Rect:
        sch_pts, img_pts = np.float32([kp_sch[m.queryIdx].pt for m in good]).reshape(
            -1, 1, 2), np.float32([kp_src[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        M, mask = self._find_homography(sch_pts, img_pts)
        # 计算四个角矩阵变换后的坐标，也就是在大图中的目标区域的顶点坐标:
        h, w = im_search.shape[:2]
        h_s, w_s = im_source.shape[:2]
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, M)

        # trans numpy arrary to python list: [(a, b), (a1, b1), ...]
        def cal_rect_pts(dst):
            return [tuple(npt[0]) for npt in np.rint(dst).astype(np.float).tolist()]

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

    def _cal_sift_confidence(self, im_search, resize_img):
        confidence = cal_rgb_confidence(img_src_rgb=im_search, img_sch_rgb=resize_img)
        confidence = (1 + confidence) / 2
        return confidence

    def _two_good_points(self, pts_sch1, pts_sch2, pts_src1, pts_src2, im_search, im_source):
        """返回两对匹配特征点情形下的识别结果."""
        # 先算出中心点(在im_source中的坐标)：
        middle_point = [int((pts_src1[0] + pts_src2[0]) / 2), int((pts_src1[1] + pts_src2[1]) / 2)]
        pypts = []
        # 如果特征点同x轴或同y轴(无论src还是sch中)，均不能计算出目标矩形区域来，此时返回值同good=1情形
        if pts_sch1[0] == pts_sch2[0] or pts_sch1[1] == pts_sch2[1] or pts_src1[0] == pts_src2[0] or pts_src1[1] == \
                pts_src2[1]:
            confidence = self.ONE_POINT_CONFI
            return dict(result=middle_point, rectangle=pypts, confidence=confidence)
        # 计算x,y轴的缩放比例：x_scale、y_scale，从middle点扩张出目标区域:(注意整数计算要转成浮点数结果!)
        h, w = im_search.shape[:2]
        h_s, w_s = im_source.shape[:2]
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


if __name__ == '__main__':
    from core.cv.base_image import image
    from core.cv.sift import SIFT
    sift = SIFT()
    im_search = image('star.png')
    img = image('test1.png')
    a = sift.find_sift(im_search=im_search, im_source=img)
    print(a)
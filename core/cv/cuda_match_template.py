import cv2
from core.cv.match_template import match_template
from core.cv.base_image import image


class cuda_match_template(match_template):
    def __init__(self):
        super(cuda_match_template, self).__init__()
        self.matcher = cv2.cuda.createTemplateMatching(cv2.CV_8U, cv2.TM_CCOEFF_NORMED)

    @staticmethod
    def check_detection_input(im_source, im_search):
        im_source = image(im_source)
        im_search = image(im_search)
        im_source.transform_gpu()
        im_search.transform_gpu()
        return im_source, im_search

    def _get_template_result_matrix(self, im_source, im_search):
        """求取模板匹配的结果矩阵."""
        s_gray, i_gray = im_search.rgb_2_gray(), im_source.rgb_2_gray()
        res = self.matcher.match(i_gray, s_gray)
        return res.download()

    def cuda_cal_rgb_confidence(self, img_src_rgb, img_sch_rgb):
        img_src_rgb, img_sch_rgb = img_src_rgb.download(), img_sch_rgb.download()
        img_sch_rgb = cv2.cuda.copyMakeBorder(img_sch_rgb, 10, 10, 10, 10, cv2.BORDER_REPLICATE)
        # 转HSV强化颜色的影响
        img_src_rgb = cv2.cuda.cvtColor(img_src_rgb, cv2.COLOR_BGR2HSV)
        img_sch_rgb = cv2.cuda.cvtColor(img_sch_rgb, cv2.COLOR_BGR2HSV)
        src_bgr, sch_bgr = cv2.cuda.split(img_src_rgb), cv2.cuda.split(img_sch_rgb)
        # 计算BGR三通道的confidence，存入bgr_confidence:
        bgr_confidence = [0, 0, 0]
        for i in range(3):
            res_temp = self.matcher.match(sch_bgr[i], src_bgr[i]).download()
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res_temp)
            bgr_confidence[i] = max_val
        return min(bgr_confidence)

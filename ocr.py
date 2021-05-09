# -*- coding: utf-8 -*-
import requests
import json
import pybase64
import cv2
import numpy as np
from core.cv.base_image import IMAGE
from core.utils.base import pprint
from core.utils.coordinate import Rect, Point


class jsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, bytes):
            return str(obj, encoding='utf-8')
        return json.JSONEncoder.default(self, obj)


def encodeImage(img):
    imgRaw = IMAGE(img).imread()
    imgBase64 = cv2.imencode('.png', imgRaw)[1]
    image_data = pybase64.b64encode(imgBase64)
    return image_data


class OCR(object):
    headers = {"Content-type": "application/json"}
    url = 'http://127.0.0.1:12345/'
    url_model = {
        "general": "ocr/paddle/general",
        "general_basic": "ocr/paddle/general_basic",
    }

    def __init__(self, lang='en', model='general_basic', scores=0.8):
        self.lang = lang
        self.model = model
        self.scores = scores

    def getText(self, img, lang='', scores=None):
        post_data = {
            'image': encodeImage(img),
            'lang': lang or self.lang
        }
        url = '{url}{model}'.format(url=self.url, model=self.url_model[self.model])
        ret = requests.post(url=url, headers=self.headers, data=json.dumps(post_data, cls=jsonEncoder))
        if ret.status_code == 200:
            text = json.loads(ret.text)
            ocr = text['ocr']
            if ocr:
                result = self._ret_general(text['ocr'], scores)
                if result:
                    return result
        return None

    def _ret_general_basic(self, ret, scores=None):
        if ret['scores'] >= (scores or self.scores):
            return ret['text']
        else:
            return None

    def _ret_general(self, ret, scores):
        lst = []
        scores = scores or self.scores
        for value in ret:
            if value['scores'] >= scores:
                lst.append({
                    'txts': value['txts'],
                    'rect': Rect.create_by_2_point(Point(*value['boxes'][0]), Point(*value['boxes'][2]))
                })
        return lst

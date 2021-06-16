# -*- coding: utf-8 -*-
import requests
import json
import pybase64
import cv2
import numpy as np
from functools import wraps
from baseImage import IMAGE, Rect, Point
from requests import exceptions
from core.error import OcrError
from loguru import logger


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


def when_http_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exceptions.ConnectTimeout:
            logger.error('ocr服务器连接超时')
            raise OcrError
    return wrapper


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

    @when_http_error
    def getText(self, img, lang='', scores=None):
        post_data = {
            'image': encodeImage(img),
            'lang': lang or self.lang
        }
        url = '{url}{model}'.format(url=self.url, model=self.url_model[self.model])
        ret = requests.post(url=url, headers=self.headers, timeout=30,
                            data=json.dumps(post_data, cls=jsonEncoder))
        result = None

        if ret.status_code == 200:
            ret = ret.json()
            if ret.get('ocr'):
                if self.model == 'general_basic':
                    result = self._ret_general_basic(ret['ocr'], scores)
                elif self.model == 'general':
                    result = self._ret_general(ret['ocr'], scores)

        return result if result else None

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

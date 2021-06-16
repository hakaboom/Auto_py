# -*- coding: utf-8 -*-
from image_registration import *
from ocr import OCR
from core.utils.base import pprint

ocr = OCR(lang='ch', model='general')
pprint(ocr.getText(img='./tmp/test4.png'))


#! usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
from loguru import logger as loguru
from core.constant import filter_level


def initLogger():
    loguru.remove()  # 清除自带的
    loguru.add(sys.stdout, format="<green>{time:YYYY-MM-dd HH:mm:ss.SSS}</green> <red>|</red> "
                                  "<level><b>{level}</b></level>     <red>|</red> "
                                  "<cyan>{name}</cyan><red>:</red>"
                                  "<cyan>{function}</cyan><red>:</red>"
                                  "<cyan>{line}</cyan> <red>-</red> "
                                  "<level>{message}</level>",
               colorize=True, filter=filter_level)


class auto_increment(object):
    def __init__(self):
        self._val = 0

    def __call__(self):
        self._val += 1
        return self._val

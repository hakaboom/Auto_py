#! usr/bin/python
# -*- coding:utf-8 -*-
import sys
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



# -*- coding: utf-8 -*-

from .constant import YOSEMITE_APK, YOSEMITE_PACKAGE
from loguru import logger
from core.adb import ADB


class Yosemite(object):
    def __init__(self, adb:ADB):
        self.adb = adb
        self.install_apk()

    def install_apk(self, apk_path:str = YOSEMITE_APK, package = YOSEMITE_PACKAGE):
        if package in self.adb.list_app():
            logger.info('yosemite is install')
        else:
            self.adb.install_app(apk_path, replace=True, install_options=['-t', '-g'])
#! usr/bin/python
# -*- coding:utf-8 -*-
from core.adb import ADB
from core.minicap import Minicap
from core.base_touch import Touch
from core.minitouch import Minitouch

class Android(object):
    """不应该暴露adb接口出来???"""
    def __init__(self, device_id=None, adb_path=None, host='127.0.0.1', port=5037, minicap: bool = True,
                 minitouch: bool = True):
        self.adb = ADB(device_id, adb_path, host, port)
        if minicap:
            self.minicap = Minicap(self.adb)
        if minitouch:
            self.minitouch = Minitouch(self.adb)

    def screencap(self):
        return self.minicap.screencap()



#! usr/bin/python
# -*- coding:utf-8 -*-
from core.adb import ADB
from core.minicap import _Minicap


class Android(object):
    """不应该暴露adb接口出来???"""
    def __init__(self, device_id=None, adb_path=None, host='127.0.0.1', port=5037):
        self.adb = ADB(device_id, adb_path, host, port)
        self.minicap = _Minicap(self.adb)

    def screencap(self):
        return self.minicap.screencap()



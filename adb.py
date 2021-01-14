# -*- coding: utf-8 -*-
import os
import re
import sys
import time
import random
import platform
import warnings
import subprocess
import threading
from typing import Optional

from loguru import logger

THISPATH = os.path.dirname(os.path.realpath(__file__))
STATICPATH = os.path.join(THISPATH, "static")
DEFAULT_ADB_PATH = {
    "Windows": os.path.join(STATICPATH, "adb", "windows", "adb.exe"),
    "Darwin": os.path.join(STATICPATH, "adb", "mac", "adb"),
    "Linux": os.path.join(STATICPATH, "adb", "linux", "adb"),
    "Linux-x86_64": os.path.join(STATICPATH, "adb", "linux", "adb"),
    "Linux-armv7l": os.path.join(STATICPATH, "adb", "linux_arm", "adb"),
}

class ADB(object):
    """adb object class"""
    status_devices = 'devices'
    status_offline = 'offline'

    def __init__(self, device_id=None, adb_path=None, host=None, port=None):
        self.device_id = device_id
        self.adb_path = adb_path or self.builtin_adb_path()
        self._set_cmd_options(host, port)
        print(self.adb_path)

    def builtin_adb_path(self):
        """adb路径"""
        system = platform.system()
        machine = platform.machine()
        adb_path = DEFAULT_ADB_PATH.get('{}-{}'.format(system, machine))
        if not adb_path:
            adb_path = DEFAULT_ADB_PATH.get(system)
        if not adb_path:
            raise RuntimeError("No adb executable supports this platform({}-{}).".format(system, machine))

        # overwrite uiautomator adb
        if "ANDROID_HOME" in os.environ:
            del os.environ["ANDROID_HOME"]
        return adb_path

    def _set_cmd_options(self, host: str = '127.0.0.1', port: int = 5037):
        """设置adb服务器"""
        self.host = host
        self.port = port
        self.cmd_options = [self.adb_path]
        if self.host not in ("localhost", "127.0.0.1"):
            self.cmd_options += ['-H', self.host]
        if self.port != 5037:
            self.cmd_options += ['-P', str(self.port)]

    def start_cmd(self, cmds, devices=True):
        if devices:
            if not self.device_id:
                raise logger.error('please set device_id first')
            cmd_options = self.cmd_options + ['-s', self.devices_id]
        else:
            cmd_options = self.cmd_options

        cmds = cmd_options + split_cmd(cmds)

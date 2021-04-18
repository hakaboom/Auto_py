#! usr/bin/python
# -*- coding:utf-8 -*-
import os
import time
import threading
from core.adb import ADB
from core.utils.nbsp import NonBlockingStreamReader


class Rotation(object):
    def __init__(self, adb: ADB):
        self.adb = adb
        self.event = threading.Event()

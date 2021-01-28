# -*- coding: utf-8 -*-
# https://github.com/AirtestProject/Airtest/blob/master/airtest/core/android/javacap.py
# 使用网易的yosemite实现
import socket
import struct
from core.constant import JAC_LOCAL_NAME, JAC_CAP_PATH
from core.yosemite import Yosemite
from core.utils.nbsp import NonBlockingStreamReader
from loguru import logger

import cv2
import numpy as np


class Javacap(Yosemite):

    APP_PKG = "com.netease.nie.yosemite"
    SCREENCAP_SERVICE = "com.netease.nie.yosemite.Capture"
    RECVTIMEOUT = None

    def __init__(self, adb):
        super(Javacap, self).__init__(adb)
        self.JAC_LOCAL_NAME = JAC_LOCAL_NAME.format(self.adb.get_device_id())
        self.JAC_CAP_PATH = JAC_CAP_PATH.format(self.adb.get_device_id().replace(':', '_'))
        self.frame_gen = None

    def _setup_stream_server(self):
        self.adb.set_forward('localabstract:%s' % self.JAC_LOCAL_NAME)
        apkpath = self.adb.path_app(self.APP_PKG)
        cmds = ["CLASSPATH=" + apkpath, 'exec', 'app_process', '/system/bin', self.SCREENCAP_SERVICE,
                "--scale", "100", "--socket", "%s" % self.JAC_LOCAL_NAME, "-lazy", "2>&1"]
        proc = self.adb.start_shell(cmds)
        nbsp = NonBlockingStreamReader(proc.stdout, print_output=True, name="javacap_sever")
        while True:
            line = nbsp.readline(timeout=5.0)
            if line is None:
                raise RuntimeError("javacap server setup timeout")
            if b"Capture server listening on" in line:
                break
            if b"Address already in use" in line:
                raise RuntimeError("javacap server setup error: %s" % line)
        return proc, nbsp

    def get_frames(self):
        proc, nbsp = self._setup_stream_server()
        localport = self.adb.get_forward_port(self.JAC_LOCAL_NAME)
        s = socket.socket()
        s.connect((self.adb.host, localport))
        t = s.recv(24)
        # javacap header
        logger.debug(struct.unpack("<2B5I2B", t))

        stopping = False
        while not stopping:
            s.send(b"1")
            # recv frame header, count frame_size
            if self.RECVTIMEOUT is not None:
                header = s.recv_with_timeout(4, self.RECVTIMEOUT)
            else:
                header = s.recv(4)
            if header is None:
                logger.error("javacap header is None")
                # recv timeout, if not frame updated, maybe screen locked
                stopping = yield None
            else:
                frame_size = struct.unpack("<I", header)[0]
                frame_data = s.recv(frame_size)
                stopping = yield frame_data

        logger.debug("javacap stream ends")
        s.close()
        nbsp.kill()
        proc.kill()
        self.adb.remove_forward("tcp:%s" % localport)

    def get_frame_from_stream(self):
        if self.frame_gen is None:
            self.frame_gen = self.get_frames()
        return self.frame_gen.send(None)

    def screenshot(self):
        screen = self.get_frame_from_stream()
        nparr = np.frombuffer(screen, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        cv2.imwrite(self.JAC_CAP_PATH, img)
        logger.info('%s screencap' % self.adb.get_device_id())
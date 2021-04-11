#! usr/bin/python
# -*- coding:utf-8 -*-
import json
import re
import time
import struct
from loguru import logger
from core.adb import ADB
from core.constant import (TEMP_HOME, MNC_HOME, MNC_CMD, MNC_SO_HOME,
                           MNC_LOCAL_NAME, MNC_INSTALL_PATH, MNC_SO_INSTALL_PATH)
from core.utils.safesocket import SafeSocket
from core.utils.nbsp import NonBlockingStreamReader
from core.utils.snippet import reg_cleanup
from typing import Tuple


class _Minicap(object):
    """minicap模块"""
    RECVTIMEOUT = None

    def __init__(self, adb: ADB):
        """
        :param adb: adb instance of android device
        """
        self.adb = adb
        self.MNC_LOCAL_NAME = MNC_LOCAL_NAME.format(self.adb.get_device_id())
        self.MNC_PORT = 0
        self.quirk_flag = 0
        self.display_info = None
        self.proc, self.nbsp = None, None
        # 开启服务
        self.install()
        self.start_server()

    def install(self):
        """
        check if minicap and minicap.so installed

        :return:
            None
        """
        if not self.adb.check_file(TEMP_HOME, 'minicap'):
            logger.error('{} minicap is not install in {}', self.adb.device_id, self.adb.get_device_id())
            self.push_target_mnc()
        if not self.adb.check_file(TEMP_HOME, 'minicap.so'):
            logger.error('{} minicap.so is not install in {}', self.adb.device_id, self.adb.get_device_id())
            self.push_target_mnc_so()
        logger.info('{} minicap and minicap.so is install', self.adb.device_id)

    def start_server(self):
        """
        command adb shell {MNC_CMD} -P 1920x1080@1920x1080/0 开启minicap服务
        """
        self.set_minicap_port()
        # 如果之前服务在运行,则销毁
        self.adb.kill_process(name=MNC_HOME)
        params, display_info = self._get_params()
        proc = self.adb.start_shell([MNC_CMD, "-n '%s'" % self.MNC_LOCAL_NAME, '-P',
                                     '%dx%d@%dx%d/%d 2>&1' % params])

        nbsp = NonBlockingStreamReader(proc.stdout, print_output=True, name='minicap_server')
        while True:
            line = nbsp.readline(timeout=5.0)
            if line is None:
                raise RuntimeError("minicap server setup timeout")
            if b"Server start" in line:
                break

        if proc.poll() is not None:
            raise RuntimeError('minicap server quit immediately')
        reg_cleanup(proc.kill)
        time.sleep(.5)
        self.proc = proc
        self.nbsp = nbsp
        return proc

    def close_server(self):
        """close server"""
        self.adb.kill_process(name=MNC_HOME)
        if self.proc:
            self.proc.kill()
            self.adb.close_proc_pipe(self.proc)
        if self.nbsp:
            self.nbsp.kill()
        self.adb.remove_forward('tcp:{}'.format(self.MNC_PORT))
        self.MNC_PORT = 0
        self.quirk_flag = 0
        self.display_info = None
        self.proc, self.nbsp = None, None
        logger.info('minicap ends')

    def _get_params(self):
        display_info = self.adb.get_display_info()
        real_width = display_info['width']
        real_height = display_info['height']
        real_rotation = display_info['rotation']

        if self.quirk_flag & 2 and real_rotation in (90, 270):
            params = real_height, real_width, real_height, real_width, 0
        else:
            params = real_width, real_height, real_width, real_height, real_rotation

        return params, display_info

    def set_minicap_port(self):
        """
        command forward to minicap
        :return:
        """
        self.adb.set_forward('localabstract:%s' % self.MNC_LOCAL_NAME)
        self.MNC_PORT = self.adb.get_forward_port(self.MNC_LOCAL_NAME)
        if not self.MNC_PORT:
            raise logger.error('minicap port not set: local_name{}', self.MNC_LOCAL_NAME)
        logger.info("minicap start in port:{}", self.MNC_PORT)

    def push_target_mnc(self):
        """ push specific minicap """
        mnc_path = MNC_INSTALL_PATH.format(self.adb.abi_version())
        # push and grant
        self.adb.push(mnc_path, MNC_HOME)
        time.sleep(1)
        self.adb.start_shell(['chmod', '755', MNC_HOME])
        logger.info('minicap installed in {}', MNC_HOME)

    def push_target_mnc_so(self):
        """ push specific minicap.so (they should work together) """
        mnc_so_path = MNC_SO_INSTALL_PATH.format(self.adb.sdk_version(), self.adb.abi_version())
        # push and grant
        self.adb.push(mnc_so_path, MNC_SO_HOME)
        time.sleep(1)
        self.adb.start_shell(['chmod', '755', MNC_SO_HOME])
        logger.info('minicap.so installed in {}', MNC_SO_HOME)

    def get_display_info(self):
        """
        get display info by minicap
        command adb shell minicap -i
        :return:
            display information
        """
        display_info = self.adb.raw_shell([MNC_CMD, '-i'])
        match = re.compile(r'({.*})', re.DOTALL).search(display_info)
        display_info = match.group(0) if match else display_info
        display_info = json.loads(display_info)
        display_info["orientation"] = display_info["rotation"] / 90
        # 针对调整过手机分辨率的情况
        actual = self.adb.shell("dumpsys window displays")
        arr = re.findall(r'cur=(\d+)x(\d+)', actual)
        if len(arr) > 0:
            display_info['physical_width'] = display_info['width']
            display_info['physical_height'] = display_info['height']
            # 通过 adb shell dumpsys window displays | find "cur="
            # 获取到的分辨率是实际分辨率，但是需要的是非实际的
            if display_info["orientation"] in [1, 3]:
                display_info['width'] = int(arr[0][1])
                display_info['height'] = int(arr[0][0])
            else:
                display_info['width'] = int(arr[0][0])
                display_info['height'] = int(arr[0][1])
        return display_info


class Minicap(_Minicap):
    def get_frame(self):
        s = SafeSocket()
        s.connect((self.adb.host, self.MNC_PORT))
        t = s.recv(24)
        # minicap header
        global_headers = struct.unpack("<2B5I2B", t)
        # Global header binary format https://github.com/openstf/minicap#global-header-binary-format
        ori, self.quirk_flag = global_headers[-2:]

        if self.quirk_flag & 2 and ori not in (0, 1, 2):
            stopping = True
            logger.error("quirk_flag found:{}, going to resetup", self.quirk_flag)
        else:
            stopping = False

        if not stopping:
            s.send(b"1")
            if self.RECVTIMEOUT is not None:
                header = s.recv_with_timeout(4, self.RECVTIMEOUT)
            else:
                header = s.recv(4)
            if header is None:
                logger.error("minicap header is None")
            else:
                frame_size = struct.unpack("<I", header)[0]
                frame_data = s.recv(frame_size)
                s.close()
                return frame_data

        logger.info('get_frame ends')
        s.close()
        self.close_server()
        return None

    def get_frame_adb(self):
        """
        通过adb获取minicap的图片数据
        :return:
             接收到的图片bytes数据
        """
        stamp = time.time()
        raw_data = self.adb.raw_shell([MNC_CMD, "-n '%s'" % self.MNC_LOCAL_NAME, '-P',
                                       '%dx%d@%dx%d/%d -s 2>&1' % (
                                           self.display_info['width'], self.display_info['height'],
                                           self.display_info['width'], self.display_info['height'],
                                           self.display_info['rotation'])], ensure_unicode=False)
        jpg_data = raw_data.split(b"for JPG encoder" + self.adb.line_breaker)[-1]
        jpg_data = jpg_data.replace(self.adb.line_breaker, b"\n")
        return jpg_data, (time.time() - stamp) * 1000

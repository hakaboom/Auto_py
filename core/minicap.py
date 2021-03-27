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
    def __init__(self, adb: ADB, projection=None):
        """
        :param adb: adb instance of android device
        """
        self.adb = adb
        self.projection = projection  # (width, height)
        self.HOME = TEMP_HOME
        self.MNC_HOME = MNC_HOME
        self.MNC_SO_HOME = MNC_SO_HOME
        self.MNC_CMD = MNC_CMD
        self.MNC_PORT = None
        self.MNC_LOCAL_NAME = MNC_LOCAL_NAME.format(self.adb.get_device_id())
        self.install()
        self.set_minicap_port()
        self.display_info = self.get_display_info()
        self.quirk_flag = 0
        self.frame_gen = None

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

    def close_server(self):
        self.adb.remove_forward(self.MNC_LOCAL_NAME)
        self.adb.kill_process(name=self.MNC_HOME)

    def install(self):
        """
        check if minicap and minicap.so installed

        :return:
            None
        """
        if not self.adb.check_file(self.HOME, 'minicap'):
            logger.error('{} minicap is not install in {}', self.adb.device_id, self.adb.get_device_id())
            self._push_target_mnc()
        if not self.adb.check_file(self.HOME, 'minicap.so'):
            logger.error('{} minicap.so is not install in {}', self.adb.device_id, self.adb.get_device_id())
            self._push_target_mnc_so()
        logger.info('{} minicap and minicap.so is install', self.adb.device_id)

    def _push_target_mnc(self):
        """ push specific minicap """
        mnc_path = MNC_INSTALL_PATH.format(self.adb.abi_version())
        # push and grant
        self.adb.push(mnc_path, self.MNC_HOME)
        time.sleep(1)
        self.adb.start_shell(['chmod', '755', self.MNC_HOME])
        logger.info('minicap installed in {}', self.MNC_HOME)

    def _push_target_mnc_so(self):
        """ push specific minicap.so (they should work together) """
        mnc_so_path = MNC_SO_INSTALL_PATH.format(self.adb.sdk_version(), self.adb.abi_version())
        # push and grant
        self.adb.push(mnc_so_path, self.MNC_SO_HOME)
        time.sleep(1)
        self.adb.start_shell(['chmod', '755', self.MNC_SO_HOME])
        logger.info('minicap.so installed in {}', self.MNC_SO_HOME)

    def get_display_info(self):
        """
        get display info by minicap
        command adb shell minicap -i
        :return:
            display information
        """
        display_info = self.adb.raw_shell([self.MNC_CMD, '-i'])
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

    def _get_stream(self):
        proc, nbsp = self.start_projection_server()
        s = SafeSocket()
        s.connect((self.adb.host, self.MNC_PORT))
        t = s.recv(24)
        # minicap header
        global_headers = struct.unpack("<2B5I2B", t)
        # Global header binary format https://github.com/openstf/minicap#global-header-binary-format
        ori, self.quirk_flag = global_headers[-2:]

        if self.quirk_flag & 2 and ori in (1, 3):
            stopping = True
            logger.debug("quirk_flag found, going to resetup")
        else:
            stopping = False
        yield stopping

        while not stopping:
            s.send(b"1")
            if self.RECVTIMEOUT is not None:
                header = s.recv_with_timeout(4, self.RECVTIMEOUT)
            else:
                header = s.recv(4)
            if header is None:
                logger.error("minicap header is None")
                stopping = yield None
            else:
                frame_size = struct.unpack("<I", header)[0]
                frame_data = s.recv(frame_size)
                stopping = yield frame_data

        logger.debug('minicap stream ends')
        s.close()
        nbsp.kill()
        proc.kill()
        self.adb.remove_forward('tcp:{}'.format(self.MNC_PORT))
        self.adb.close_proc_pipe(proc)

    def get_stream(self):
        gen = self._get_stream()

        stopped = next(gen)
        if stopped:
            try:
                next(gen)
            except StopIteration:
                pass
            gen = self._get_stream()
            next(gen)
        return gen

    def _get_params(self, projection=None):
        display_info = self.adb.get_display_info()
        real_width = display_info['width']
        real_height = display_info['height']
        real_rotation = display_info['rotation']

        projection = projection or self.projection
        if projection:
            proj_width, proj_height = self.zoom_projecion_size()
        else:
            proj_width, proj_height = real_width, real_height

        if self.quirk_flag & 2 and real_rotation in (90, 270):
            params = real_height, real_width, proj_height, proj_width, 0
        else:
            params = real_width, real_height, proj_width, proj_height, real_rotation

        return params, display_info

    def zoom_projecion_size(self):
        display_info = self.adb.get_display_info()
        real_width = display_info['width']
        real_height = display_info['height']
        new_width, new_height = 640, 360
        if real_width > real_height:
            new_width, new_height = new_height, new_width
        if real_width <= new_width and real_height <= new_height:
            pass
        if (1.0 * real_width / new_width) > (1.0 * real_height / new_height):
            scale = 1.0 * real_width / new_height
        else:
            scale = 1.0 * real_height / new_height
        print(real_width, real_height)
        return int(real_width / scale), int(real_height / scale)

    def start_projection_server(self):
        """
        command adb shell {self.MNC_CMD} -P 1920x1080@1920x1080/0 开启minicap服务
        """
        params, display_info = self._get_params(True)
        proc = self.adb.start_shell([self.MNC_CMD, "-n '%s'" % self.MNC_LOCAL_NAME, '-P',
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
        return proc, nbsp


class Minicap(_Minicap):
    def get_frame_from_stream(self):
        """和直播串流一样有延迟"""
        if self.frame_gen is None:
            self.frame_gen = self.get_stream()
        return next(self.frame_gen)

    def get_frame(self):
        param, display_info = self.get_display_info()
        raw_data = self.adb.start_shell([self.MNC_CMD, "-n '%s'" % self.MNC_LOCAL_NAME, '-P',
                                        '%dx%d@%dx%d/%d 2>&1' % (display_info['width'], display_info['height'],
                                                                 display_info['width'], display_info['height'],
                                                                 display_info['rotation'])])


    # @staticmethod
    # def bytes2img(b):
    #     """bytes转换成cv2可读取格式"""
    #     img = np.array(bytearray(b))
    #     img = cv2.imdecode(img, 1)
    #     return img
    #
    # def screenshot(self):
    #     # 获取当前帧,cv2转换成图片并写入文件
    #     frameBody, socket_time = self._get_frame()
    #     stamp = time.time()
    #     img = self.bytes2img(frameBody)
    #     cv2.imwrite(self.MNC_CAP_REMOTE_PATH, img)
    #
    #     write_time = (time.time() - stamp) * 1000
    #     logger.info(
    #         "screenshot: socket_time={:.2f}ms, write_time={:.2f}ms,time={:.2f}ms size=({width}x{height}), path={})",
    #         socket_time, write_time, socket_time + write_time, self.MNC_CAP_PATH,
    #         width=self.display_info['width'], height=self.display_info['height'])

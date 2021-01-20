#! usr/bin/python
# -*- coding:utf-8 -*-
import re
import json
import time
import socket


from core.adb import ADB

import cv2
import numpy as np
from loguru import logger


class Minicap(object):
    """minicap模块"""

    # 所有参数都要加上device_id
    def __init__(self, adb: ADB):
        """

        :param adb: adb instance of android device
        """
        self.adb = adb
        self.HOME = '/data/local/tmp'
        self.MNC_HOME = '/data/local/tmp/minicap'
        self.MNC_SO_HOME = '/data/local/tmp/minicap.so'
        self.MNC_CMD = 'LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap'
        self.MNC_LOCAL_NAME = 'minicap_%s' % self.adb.get_device_id()
        self.MNC_CAP_PATH = 'temp_%s.png' % self.adb.get_device_id()
        self._abi_version = self.adb.abi_version().rstrip()
        self._sdk_version = self.adb.sdk_version().rstrip()
        self.set_minicap_port()
        self.start_mnc_server()

    def set_minicap_port(self):
        """
        command forward to minicap
        :return:
        """
        self._is_mnc_install()
        self.adb.set_forward('localabstract:%s' % self.MNC_LOCAL_NAME)
        index = self.adb._local_in_forwards(remote='localabstract:%s' % self.MNC_LOCAL_NAME)
        if not index[0]:
            raise logger.error('minicap port not set: local_name{}', self.MNC_LOCAL_NAME)
        self.MNC_PORT = int(re.compile(r'tcp:(\d+)').findall(self.adb._forward_local_using[index[1]]['local'])[0])

    def _push_target_mnc(self):
        """ push specific minicap """

        mnc_path = "./static/stf_libs/{}/minicap".format(self._abi_version)
        # logger.debug('target minicap path: ' + mnc_path)
        # push and grant
        self.adb.start_cmd(['push', mnc_path, self.MNC_HOME])
        self.adb.start_shell(['chmod', '777', self.MNC_HOME])
        logger.debug('minicap installed in {}', self.MNC_HOME)

    def _push_target_mnc_so(self):
        """ push specific minicap.so (they should work together) """
        mnc_so_path = "./static/stf_libs/minicap-shared/aosp/libs/android-{sdk}/{abi}/minicap.so".format(sdk=self._sdk_version,abi=self._abi_version)
        # logger.debug('target minicap.so url: ' + mnc_so_path)
        # push and grant
        self.adb.start_cmd(['push', mnc_so_path, self.MNC_SO_HOME])
        self.adb.start_shell(['chmod', '777', self.MNC_SO_HOME])
        logger.debug('minicap.so installed in {}', self.MNC_SO_HOME)

    def _is_mnc_install(self):
        """
        check if minicap and minicap.so installed

        :return:
            None
        """
        if not self.adb.check_file(self.HOME, 'minicap'):
            logger.error('minicap is not install in {}', self.adb.get_device_id())
            self._push_target_mnc()
        if not self.adb.check_file(self.HOME, 'minicap.so'):
            logger.error('minicap.so is not install in {}', self.adb.get_device_id())
            self._push_target_mnc_so()
        logger.info('minicap and minicap.so is install')

    def get_display_info(self):
        """
        command adb shell minicap -i
        :return:
            display information
        """
        display_info = self.adb.raw_shell([self.MNC_CMD, '-i'])
        match = re.compile(r'({.*})', re.DOTALL).search(display_info)
        display_info = match.group(0) if match else display_info
        display_info = json.loads(display_info)
        display_info["orientation"] = display_info["rotation"] / 90
        # adb获取分辨率
        wm_size = self.adb.raw_shell(['wm', 'size'])
        wm_size = re.findall(r'Physical size: (\d+)x(\d+)\r', wm_size)
        if len(wm_size) > 0:
            display_info['physical_width'] = display_info['width']
            display_info['physical_height'] = display_info['height']
            display_info['width'] = int(wm_size[0][0])
            display_info['height'] = int(wm_size[0][1])
        # adb方式获取DPI
        wm_dpi = self.adb.raw_shell(['wm', 'density'])
        wm_dpi = re.findall(r'Physical density: (\d+)\r', wm_dpi)
        if len(wm_dpi) > 0:
            display_info['dpi'] = int(wm_dpi[0])
        logger.debug('display_info {}', display_info)
        # if display_info['height'] > display_info['width']:
        #     display_info['height'],display_info['width'] = display_info['width'], display_info['height']
        return display_info

    def start_mnc_server(self):
        """
        command adb shell {self.MNC_CMD} -P 1920x1080@1920x1080/0 开启minicap服务
        :return:
            None
        """
        display_info = self.get_display_info()
        self.display_info = display_info
        self.adb.start_shell([self.MNC_CMD, "-n '%s'" % self.MNC_LOCAL_NAME, '-P',
                              '%dx%d@%dx%d/%d 2>&1' % (display_info['width'], display_info['height'],
                                                       display_info['width'], display_info['height'],
                                                       display_info['rotation'])])
        time.sleep(1)
        logger.info('%s minicap server is running' % self.adb.get_device_id())

    def screencap(self):
        """
        通过socket读取minicap的图片数据,并且通过cv2生成图片
        :return:
            cv2.img
        """
        readBannerBytes = 0
        bannerLength = 2
        readFrameBytes = 0
        frameBodyLengthRemaining = 0
        frameBody = ''
        banner = {
            'version': 0,
            'length': 0,
            'pid': 0,
            'realWidth': 0,
            'realHeight': 0,
            'virtualWidth': 0,
            'virtualHeight': 0,
            'orientation': 0,
            'quirks': 0
        }
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', self.MNC_PORT))
        self.adb.start_shell([self.MNC_CMD, "-n '{}' -s 2>&1".format(self.MNC_LOCAL_NAME)])
        width, height = self.display_info['width'], self.display_info['height']
        while True:
            chunk = client_socket.recv(24000)  # 调大可用加快速度,但是24000以上基本就没有差距了
            if len(chunk) == 0:
                continue

            cursor = 0
            while cursor < len(chunk):
                if readBannerBytes < bannerLength:
                    if readBannerBytes == 0:
                        banner['version'] = int(hex(chunk[cursor]), 16)
                    elif readBannerBytes == 1:
                        banner['length'] = bannerLength = int(hex(chunk[cursor]), 16)
                    elif 2 <= readBannerBytes <= 5:
                        banner['pid'] = int(hex(chunk[cursor]), 16)
                    elif readBannerBytes == 23:
                        banner['quirks'] = int(hex(chunk[cursor]), 16)

                    cursor += 1
                    readBannerBytes += 1

                elif readFrameBytes < 4:
                    frameBodyLengthRemaining += (int(hex(chunk[cursor]), 16) << (readFrameBytes * 8))
                    cursor += 1
                    readFrameBytes += 1

                else:
                    # if this chunk has data of next image
                    if len(chunk) - cursor >= frameBodyLengthRemaining:
                        frameBody = frameBody + chunk[cursor:(cursor + frameBodyLengthRemaining)]
                        if hex(frameBody[0]) != '0xff' or hex(frameBody[1]) != '0xd8':
                            exit()
                        img = np.array(bytearray(frameBody))
                        img = cv2.imdecode(img, 1)
                        img = cv2.resize(img, (width, height))
                        cv2.imwrite(self.MNC_CAP_PATH, img)
                        client_socket.close()
                        logger.info('%s screencap' % self.adb.get_device_id())
                        return img
                    else:
                        # else this chunk is still for the current image
                        frameBody = bytes(list(frameBody) + list(chunk[cursor:len(chunk)]))
                        frameBodyLengthRemaining -= (len(chunk) - cursor)
                        readFrameBytes += len(chunk) - cursor
                        cursor = len(chunk)

# -*- coding: utf-8 -*-
import socket
import time
import struct
import subprocess
import platform
import re
import json

import cv2
import numpy
from loguru import logger

DEFAULT_CHARSET = 'utf-8'
# installer
MNC_HOME = '/data/local/tmp/minicap'
MNC_SO_HOME = '/data/local/tmp/minicap.so'
TEMP_PIC_ANDROID_PATH = '/data/local/tmp/screenCap_temp.png'

# system
# 'Linux', 'Windows' or 'Darwin'.
SYSTEM_NAME = platform.system()
NEED_SHELL = SYSTEM_NAME != 'Windows'
ADB_EXECUTOR = 'adb'


def is_device_connected(device_id):
    """ return True if device connected, else return False """
    try:
        device_name = subprocess.check_output([ADB_EXECUTOR, '-s', device_id, 'shell', 'getprop', 'ro.product.model'])
        device_name = device_name.decode(DEFAULT_CHARSET).replace('\n', '').replace('\r', '')
        logger.info('device {} online'.format(device_name))
    except subprocess.CalledProcessError:
        return False
    return True


class _BaseClient(object):
    """ install minicap for android devices """

    def __init__(self, device_id, port=8000):
        assert is_device_connected(device_id)

        self.device_id = device_id
        self.minicap_port = port
        self.abi = self.get_abi()
        self.sdk = self.get_sdk()
        if self.is_mnc_installed():
            logger.info('minicap already existed in {}'.format(device_id))
        else:
            self.push_target_mnc()
            self.push_target_mnc_so()

    def get_abi(self):
        """ get abi (application binary interface) """
        abi = subprocess.getoutput('{} -s {} shell getprop ro.product.cpu.abi'.format(ADB_EXECUTOR, self.device_id))
        logger.info('device {} abi is {}'.format(self.device_id, abi))
        return abi

    def get_sdk(self):
        """ get sdk version """
        sdk = subprocess.getoutput('{} -s {} shell getprop ro.build.version.sdk'.format(ADB_EXECUTOR, self.device_id))
        logger.info('device {} sdk is {}'.format(self.device_id, sdk))
        return sdk

    def push_target_mnc(self):
        """ push specific minicap """
        mnc_path = './android/{}/bin/minicap'.format(self.abi)
        logger.info('target minicap path: ' + mnc_path)

        # push and grant
        subprocess.run([ADB_EXECUTOR, '-s', self.device_id, 'push', mnc_path, MNC_HOME], stdout=subprocess.DEVNULL)
        subprocess.run([ADB_EXECUTOR, '-s', self.device_id, 'shell', 'chmod', '777', MNC_HOME])
        logger.info('minicap installed in {}'.format(MNC_HOME))

    def push_target_mnc_so(self):
        """ push specific minicap.so (they should work together) """
        mnc_so_path = './android/{}/lib/android-{}/minicap.so'.format(self.abi, self.sdk)
        logger.info('target minicap.so url: ' + mnc_so_path)

        # push and grant
        subprocess.run([ADB_EXECUTOR, '-s', self.device_id, 'push', mnc_so_path, MNC_SO_HOME],
                       stdout=subprocess.DEVNULL)
        subprocess.run([ADB_EXECUTOR, '-s', self.device_id, 'shell', 'chmod', '777', MNC_SO_HOME])
        logger.info('minicap.so installed in {}'.format(MNC_SO_HOME))

    def is_installed(self, name):
        """ check if is existed in /data/local/tmp """
        return bool(subprocess.check_output([
            ADB_EXECUTOR, '-s', self.device_id, 'shell',
            'find', '/data/local/tmp', '-name', name])
        )

    def is_mnc_installed(self):
        """ check if minicap installed """
        return self.is_installed('minicap') and self.is_installed('minicap.so')


class _Minicap(_BaseClient):
    CMD = 'LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap'

    def __init__(self, device_id, port):
        super().__init__(device_id)
        self.minicap_port = self.set_minicap_port(port)
        self.display_id = 0
        self.projection = None
        self.quirk_flag = 0
        self.display_info = {}

    def set_minicap_port(self, port):
        port = port or self.minicap_port
        ret = subprocess.run([ADB_EXECUTOR, '-s', self.device_id, 'forward', 'tcp:{}'.format(port),
                              'localabstract:minicap'], stderr=subprocess.PIPE)
        stderr = str(ret.stderr, encoding='utf-8')
        if stderr.find('cannot bind') > -1:
            logger.info('adb.exe: error: cannot bind listener:cannot bind to port:{}',port)
            port += 1
            return self.set_minicap_port(port)
        logger.info('minicap open in {}'.format(port))

    def get_display_info(self):
        """
        按照Airtest的写了,但是好像不知道为什么minicap获取后还要用adb获取
        :return:
            display information
        """
        if self.display_id:
            shell = 'adb -s {1} shell {2} -d {3} -i'.format(ADB_EXECUTOR, self.device_id, self.CMD, self.display_id)
            display_info = subprocess.run(shell, shell=True, stdout=subprocess.PIPE)
        else:
            shell = 'adb -s {0} shell {1} -i'.format(self.device_id, self.CMD)
            display_info = subprocess.run(shell, shell=True, stdout=subprocess.PIPE)
        display_info = str(display_info.stdout, encoding='utf-8')
        match = re.compile(r'({.*})', re.DOTALL).search(display_info)
        display_info = match.group(0) if match else display_info
        display_info = json.loads(display_info)
        display_info["orientation"] = display_info["rotation"] / 90
        # adb方式获取分辨率
        wm_size = subprocess.run([ADB_EXECUTOR, '-s', self.device_id, 'shell', 'wm', 'size'], stdout=subprocess.PIPE)
        wm_size_stdout = str(wm_size.stdout, encoding='utf-8')
        wm_size_arr = re.findall(r'Physical size: (\d+)x(\d+)\r', wm_size_stdout)
        logger.info('display_size {}', wm_size_arr)
        if len(wm_size_arr) > 0:
            display_info['physical_width'] = display_info['width']
            display_info['physical_height'] = display_info['height']
            display_info['width'] = wm_size_arr[0][0]
            display_info['height'] = wm_size_arr[0][1]
        # adb方式获取DPI
        wm_dpi = subprocess.run([ADB_EXECUTOR, '-s', self.device_id, 'shell', 'wm', 'density'], stdout=subprocess.PIPE)
        wm_dpi_stdout = str(wm_dpi.stdout, encoding='utf-8')
        wm_dpi_arr = re.findall(r'Physical density: (\d+)\r', wm_dpi_stdout)
        logger.info('display_dpi {}', wm_dpi_arr)
        if len(wm_dpi_arr) > 0:
            display_info['dpi'] = wm_dpi_arr[0]

        logger.info('display_info {}', display_info)
        self.display_info = display_info
        return display_info

    def get_frame(self):
       pass

    def _get_params(self, projection=None):
        display_info = self.display_info or self.get_display_info()
        real_width = display_info["width"]
        real_height = display_info["height"]
        real_rotation = display_info["rotation"]
        # 优先去传入的projection
        projection = projection or self.projection
        if projection:
            proj_width, proj_height = projection
        else:
            proj_width, proj_height = real_width, real_height

        if self.quirk_flag & 2 and real_rotation in (90, 270):
            params = real_height, real_width, proj_height, proj_width, 0
        else:
            params = real_width, real_height, proj_width, proj_height, real_rotation

        return (params, display_info)


class Device(_Minicap):
    pass


def connect(device_id, port=8000):
    return Device(device_id, port)


# -*- coding: utf-8 -*-
import re
import sys
import time
import socket
from typing import Tuple
from loguru import logger
from core.adb import ADB
from core.constant import (TEMP_HOME, MNT_HOME, MNT_LOCAL_NAME, MNT_INSTALL_PATH)
from core.utils.nbsp import NonBlockingStreamReader
from core.utils.safesocket import SafeSocket
from core.utils.snippet import str2byte, get_std_encoding
from core.utils.base import pprint
from .base import transform


class _Minitouch(transform):
    """
    minitouch模块
    """

    def __init__(self, adb: ADB):
        """
        :param adb: adb instance of android device
        """
        super(_Minitouch, self).__init__(adb)
        self.adb = adb
        self.HOME = TEMP_HOME
        self.MNT_HOME = MNT_HOME
        self.MNT_PORT = None
        self.MNT_LOCAL_NAME = MNT_LOCAL_NAME.format(self.adb.get_device_id())
        self.max_x, self.max_y = None, None
        self.start_server()
        logger.info('minitouch init, port:{} name:{}, max_x={}, max_y={}', self.MNT_PORT, self.MNT_LOCAL_NAME,
                    self.max_x, self.max_y)

    def _push_target_mnt(self):
        """ push specific minitouch """
        mnt_path = MNT_INSTALL_PATH.format(self.adb.abi_version())
        # push and grant
        self.adb.push(mnt_path, self.MNT_HOME)
        time.sleep(1)
        self.adb.start_shell(['chmod', '755', self.MNT_HOME])
        logger.info('minicap installed in {}', self.MNT_HOME)

    def start_server(self):
        self.set_minitouch_port()
        self.setup_server()
        self.setup_client()

    def set_minitouch_port(self):
        """
        command forward to minicap
        :return:
        """
        self._is_mnt_install()
        self.adb.set_forward('localabstract:%s' % self.MNT_LOCAL_NAME)
        self.MNT_PORT = self.adb.get_forward_port(self.MNT_LOCAL_NAME)
        if not self.MNT_PORT:
            raise logger.error('minicap port not set: local_name{}', self.MNT_LOCAL_NAME)

    def setup_server(self):
        # 如果之前服务在运行,则销毁
        self.adb.kill_process(name=MNT_HOME)
        p = self.adb.start_shell("{path} -n '{name}' 2>&1".format(path=self.MNT_HOME, name=self.MNT_LOCAL_NAME))

        nbsp = NonBlockingStreamReader(p.stdout, name='minitouch_server')
        while True:
            line = nbsp.readline(timeout=5.0)
            if line is None:
                raise RuntimeError("minitouch setup timeout")

            line = line.decode(get_std_encoding(sys.stdout))
            # 识别出setup成功的log, 并匹配出max_x, max_y
            m = re.search("Type \w touch device .+ \((\d+)x(\d+) with \d+ contacts\) detected on .+ \(.+\)", line)
            if m:
                self.max_x, self.max_y = int(m.group(1)), int(m.group(2))
                break
            else:
                self.max_x = 32768
                self.max_y = 32768

        if p.poll() is not None:
            raise RuntimeError("minitouch server quit immediately")

        # s = SafeSocket()
        # s.connect((self.adb.host, self.MNT_PORT))
        #
        # # get minitouch server info
        # socket_out = s.makefile()
        # # v <version>
        # # protocol version, usually it is 1. needn't use this
        # version = re.findall(r'(\d+)', socket_out.readline())
        # # ^ <max-contacts> <max-x> <max-y> <max-pressure>
        # max_contacts, max_x, max_y, max_pressure = re.findall(r'(\d+)', socket_out.readline())
        # self.max_x, self.max_y = int(max_x), int(max_y)
        # # $ <pid>
        # pid = re.findall(r'(\d+)', socket_out.readline())
        # self.client = s

    def setup_client(self):
        s = SafeSocket()
        s.connect((self.adb.host, self.MNT_PORT))
        s.sock.settimeout(2)
        header = b""
        while True:
            try:
                header += s.sock.recv(4096)
            except socket.timeout:
                logger.warning("minitouch header not recved")
                break
            if header.count(b'\n') >= 3:
                break
        logger.debug("minitouch header:{}", repr(header))
        self.client = s

    def _is_mnt_install(self):
        if not self.adb.check_file(self.HOME, 'minitouch'):
            logger.error('{} minitouch is not install in {}', self.adb.device_id, self.adb.get_device_id())
            self._push_target_mnt()
        logger.info('{} minitouch is install', self.adb.device_id, )

    def send(self, content: str):
        byte_connect = str2byte(content)
        self.client.send(byte_connect)
        print(byte_connect)
        return self.client.recv(0)


class Minitouch(_Minitouch):
    def transform_xy(self, x, y):
        width, height = self.size_info['width'], self.size_info['height']
        nx = float(x) * self.max_x / width
        ny = float(y) * self.max_y / height
        if nx > self.max_x or ny > self.max_y:
            raise OverflowError('坐标不能大于max值, x={},y={},max_x={},max_y={}'.format(nx, ny, self.max_x, self.max_y))
        return "%.0f" % nx, "%.0f" % ny

    def sleep(self, duration: int):
        """
        command: 'w <ms>\n'
        """
        s = 'w {}\n'.format(duration)
        self.send(s)

    def down(self, x: int, y: int, index: int = 0, pressure: int = 50):
        """
        command: 'd <index> <x> <y> <pressure>\n'

        Args:
            x: x轴坐标
            y: y轴坐标
            index: 使用的手指
            pressure: 按压力度
        """
        x, y = self.transform_xy(x, y)
        s = 'd {} {} {} {}\nc\n'.format(index, x, y, pressure)
        self.send(s)

    def up(self, x: int, y: int, index: int = 0):
        """
        command: 'u <index>\n'

        Args:
              index: 使用的手指
        """
        s = 'u {}\nc\n'.format(index)
        self.send(s)

    def move(self, start: Tuple[int, int], end: Tuple[int, int], index: int = 0, spacing: int = 5,
             pressure: int = 50, duration: int = 50):
        """
        拖动

        Args:
            start: 起始点坐标,(x,y)
            end: 终点坐标 (x,y)
            index: 使用的手指
            spacing: 每一次移动的间隔像素
            pressure: 按压力度
            duration: 延迟

        :return:
            None
        """
        start_x, start_y = self.transform_xy(start[0], start[1])
        end_x, end_y = self.transform_xy(end[0], end[1])
        x, y = None, None
        t = ["d {} {} {} {}\nc\n".format(index, start_x, start_y, pressure)]
        for i in range(spacing, 100, spacing):
            i = i / 100
            x = round((1 - i) * start_x + i * end_x)
            y = round((1 - i) * start_y + i * end_y)
            t.append("m {} {} {} {}\nc\nw {}\n".format(index, x, y, pressure, duration))
        # 如果没移动完
        if x < end_x or y < end_y:
            x = round(x + (end_x - x))
            y = round(y + (end_y - y))
            t.append("m {} {} {} {}\nc\nw {}\n".format(index, x, y, pressure, duration))
        t.append("u {}\nc\n".format(index))
        self.send(''.join(t))

    def reset_events(self):
        self.send('r\n')

    def click(self, x: int, y: int, index: int = 0, duration: int = 20):
        self.down(x, y, index)
        self.sleep(duration)
        self.up(x, y, index)

# -*- coding: utf-8 -*-
import re
import json
import time
import sys
import socket
from typing import Tuple, Dict
from core.utils import str2byte
from core.adb import ADB

from loguru import logger


class Minitouch(object):
    """
    minitouch模块
    由于minitouch中传坐标精确到了小数点后一位,为了可读性,约定传参时坐标为正常坐标如:1920,1080
    发送坐标时需要乘以10变为19200,10800
    """

    def __init__(self, adb: ADB):
        """
        :param adb: adb instance of android device
        """
        self.adb = adb
        self.HOME = '/data/local/tmp'
        self.MNT_HOME = '/data/local/tmp/minitouch'
        self.MNT_CMD = 'LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minitouch'
        self.MNT_LOCAL_NAME = 'minitouch_%s' % self.adb.get_device_id()
        self._abi_version = self.adb.abi_version().rstrip()
        self.server_proc = None
        self.max_x = 0
        self.max_y = 0
        self.set_minitouch_port()
        self.start_minitouch_server()
        self.reset_events()

    def _push_target_mnt(self):
        """ push specific minitouch """
        mnt_path = "./static/stf_libs/{}/minitouch".format(self._abi_version)
        # push and grant
        self.adb.start_cmd(['push', mnt_path, self.MNT_HOME])
        self.adb.start_shell(['chmod', '777', self.MNT_HOME])
        logger.debug('minicap installed in {}', self.MNT_HOME)

    def set_minitouch_port(self):
        """
        command forward to minicap
        :return:
        """
        self._is_mnt_install()
        self.adb.set_forward('localabstract:%s' % self.MNT_LOCAL_NAME)
        index = self.adb._local_in_forwards(remote='localabstract:%s' % self.MNT_LOCAL_NAME)
        if not index[0]:
            raise logger.error('minitouch port not set: local_name{}', self.MNT_LOCAL_NAME)
        self.MNT_PORT = int(re.compile(r'tcp:(\d+)').findall(self.adb._forward_local_using[index[1]]['local'])[0])

    def start_minitouch_server(self):
        self.adb.start_shell("{path} -n '{name}'".format(path=self.MNT_HOME,name=self.MNT_LOCAL_NAME))
        time.sleep(1)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', self.MNT_PORT))

        # get minitouch server info
        socket_out = client.makefile()
        # v <version>
        # protocol version, usually it is 1. needn't use this
        version = re.findall(r'(\d+)', socket_out.readline())

        # ^ <max-contacts> <max-x> <max-y> <max-pressure>
        max_contacts, max_x, max_y, max_pressure = re.findall(r'(\d+)', socket_out.readline())
        self.max_x, self.max_y = int(max_x)/10, int(max_y)/10
        # $ <pid>
        pid = re.findall(r'(\d+)', socket_out.readline())
        self.client = client

    def _is_mnt_install(self):
        if not self.adb.check_file(self.HOME, 'minitouch'):
            logger.error('minitouch is not install in {}', self.adb.get_device_id())
            self._push_target_mnt()
        logger.info('minitouch is install')

    def send(self, content: str):
        byte_connect = str2byte(content)
        self.client.sendall(byte_connect)
        return self.client.recv(0)

    def sleep(self, ms: int):
        """
        command: 'w <ms>\n'
        """
        s = 'w {}\n'.format(ms)
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
        if x > self.max_x or y > self.max_y:
            raise OverflowError('坐标不能大于max值, x={},y={},max_x={},max_y={}'.format(x, y, self.max_x, self.max_y))
        s = 'd {} {} {} {}\nc\n'.format(index, x*10, y*10, pressure)
        self.send(s)

    def up(self, x: int, y: int, index: int = 0):
        """
        command: 'u <index>\n'

        Args:
              index: 使用的手指
        """
        s = 'u {}\nc\n'.format(index)
        self.send(s)

    def move(self, start: Tuple[int, int], end: Tuple[int, int], index: int = 0, spacing: int = 5, pressure: int = 50, duration: int = 50):
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
        start_x, start_y = start
        end_x, end_y = end
        if start_x > self.max_x or start_y > self.max_y:
            raise OverflowError('start坐标不能大于max值, x={},y={},max_x={},max_y={}'.format(start_x, start_y, self.max_x, self.max_y))
        if end_x > self.max_x or end_y > self.max_y:
            raise OverflowError('end坐标不能大于max值, x={},y={},max_x={},max_y={}'.format(end_x, end_y, self.max_x, self.max_y))
        x, y = 0, 0
        t = ["d {} {} {} {}\nc\n".format(index, start_x * 10, start_y * 10, pressure)]
        for i in range(spacing, 100, spacing):
            i = i/100
            x = round((1-i)*start_x + i*end_x)
            y = round((1-i)*start_y + i*end_y)
            t.append("m {} {} {} {}\nc\nw {}\n".format(index, x * 10, y * 10, pressure, duration))
        # 如果没移动完
        if x < end_x or y < end_y:
            x = round(x + (end_x - x))
            y = round(y + (end_y - y))
            t.append("m {} {} {} {}\nc\nw {}\n".format(index, x * 10, y * 10, pressure, duration))
        t.append("u {}\nc\n".format(index))
        self.send(''.join(t))

    def reset_events(self):
        self.send('r\n')

    def click(self, x: int, y: int, index: int = 0, duration: int = 20):
        self.down(x, y)
        self.sleep(duration)
        self.up(x, y)


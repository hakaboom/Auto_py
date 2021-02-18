# -*- coding: utf-8 -*-
import re
import socket
import time
import math
from typing import Tuple

from loguru import logger

from core.adb import ADB
from core.constant import (TEMP_HOME, MNT_HOME, MNT_LOCAL_NAME, MNT_INSTALL_PATH)
from core.utils.snippet import str2byte


class transform(object):
    """通过minitouch的max_x,max_y与屏幕适配"""
    def __init__(self, display_info: dict, max_x: int = 0, max_y: int = 0, orientation: int = 1, screen_size: dict = None):
        self.orientation = orientation
        self.display_info = display_info
        self.event_size = dict(width=display_info['max_x'], height=display_info['max_y'])
        self.screen_size = dict(width=display_info['width'], height=display_info['height'])
        self.event_scale = self.event2windows()

    def event2windows(self):
        return {
            'width': self.screen_size['width'] / self.event_size['width'],
            'height': self.screen_size['height'] / self.event_size['height']
        }

    def right2right(self, x, y):
        return round(x / self.event_scale['width']), \
               round(y / self.event_scale['height'])

    def portrait2right(self, x, y):
        return round((x / self.screen_size['height'] * self.screen_size['width']) / self.event_scale['width']), \
               round((y / self.screen_size['width'] * self.screen_size['height'] / self.event_scale['height']))

    def left2right(self, x, y):
        return round((1 - x / self.screen_size['height']) * self.screen_size['width'] / self.event_scale['height']), \
               round((1 - y / self.screen_size['width']) * self.screen_size['height'] / self.event_scale['height'])


class _Minitouch(transform):
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
        self.HOME = TEMP_HOME
        self.MNT_HOME = MNT_HOME
        self.MNT_PORT = 0
        self.MNT_LOCAL_NAME = MNT_LOCAL_NAME.format(self.adb.get_device_id())
        self._abi_version = self.adb.abi_version()
        self.max_x, self.max_y = 0, 0
        self.set_minitouch_port()
        self.start_minitouch_server()
        super(_Minitouch, self).__init__(display_info=self._get_display_info())
        logger.info('minitouch init, port:{} name:{}, max_x={}, max_y={}', self.MNT_PORT, self.MNT_LOCAL_NAME,
                    self.max_x, self.max_y)

    def _get_display_info(self):
        display_info = self.adb.get_display_info()
        display_info.update({
            'max_x': self.max_x,
            'max_y': self.max_y
        })
        return display_info

    def _push_target_mnt(self):
        """ push specific minitouch """
        mnt_path = MNT_INSTALL_PATH.format(self._abi_version)
        # push and grant
        self.adb.push(mnt_path, self.MNT_HOME)
        time.sleep(1)
        self.adb.start_shell(['chmod', '777', self.MNT_HOME])
        logger.info('minicap installed in {}', self.MNT_HOME)

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

    def start_minitouch_server(self):
        # 如果之前服务在运行,则销毁
        self.adb.kill_process(name=MNT_HOME)
        time.sleep(1)
        self.adb.start_shell("{path} -n '{name}'".format(path=self.MNT_HOME, name=self.MNT_LOCAL_NAME))
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
        self.max_x, self.max_y = int(max_x), int(max_y)
        # $ <pid>
        pid = re.findall(r'(\d+)', socket_out.readline())
        self.client = client

    def _is_mnt_install(self):
        if not self.adb.check_file(self.HOME, 'minitouch'):
            logger.error('{} minitouch is not install in {}', self.adb.device_id, self.adb.get_device_id())
            self._push_target_mnt()
        logger.info('{} minitouch is install', self.adb.device_id,)

    def send(self, content: str):
        byte_connect = str2byte(content)
        self.client.sendall(byte_connect)
        return self.client.recv(0)

    def transform(self, x, y):
        print(x, y)
        if self.display_info['orientation'] == 0:
            return self.right2right(x, y)
        elif self.display_info['orientation'] == 1:
            return self.left2right(x, y)
        elif self.display_info['orientation'] == 2:
            return self.portrait2right(x, y)


class Minitouch(_Minitouch):
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
        x, y = self.transform(x, y)
        if x > self.max_x or y > self.max_y:
            raise OverflowError('坐标不能大于max值, x={},y={},max_x={},max_y={}'.format(x, y, self.max_x, self.max_y))
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
        start_x, start_y = self.transform(start)
        end_x, end_y =  self.transform(end)
        if start_x > self.max_x or start_y > self.max_y:
            raise OverflowError('start坐标不能大于max值, x={},y={},max_x={},max_y={}'.
                                format(start_x, start_y, self.max_x, self.max_y))
        if end_x > self.max_x or end_y > self.max_y:
            raise OverflowError('end坐标不能大于max值, x={},y={},max_x={},max_y={}'.
                                format(end_x, end_y, self.max_x, self.max_y))

        x, y = 0, 0
        t = ["d {} {} {} {}\nc\n".format(index, start_x, start_y, pressure)]
        for i in range(spacing, 100, spacing):
            i = i/100
            x = round((1-i)*start_x + i*end_x)
            y = round((1-i)*start_y + i*end_y)
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

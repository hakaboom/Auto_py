#! usr/bin/python
# -*- coding:utf-8 -*-
import re
import math
import time
from core.adb import ADB
from loguru import logger
from .base import transform


class Touch_event(transform):
    def __init__(self, adb, max_x, max_y):
        super(Touch_event, self).__init__(adb)
        self.event_id = 1
        self.index_count = 0
        self.index = [False, False, False, False, False, False, False, False, False, False, False]
        self.max_x, self.max_y = max_x, max_y

    def add_event_id(self):
        self.event_id += 1

    def index_down(self, index):
        """手指按下调整为True,count减1"""
        self.index[index] = True
        self.index_count += 1

    def index_up(self, index):
        """手指按下调整为True,count减1"""
        self.index[index] = False
        self.index_count -= 1

    def transform_xy(self, x, y):
        width, height = self.size_info['width'], self.size_info['height']
        nx = round(x / (width / self.max_x))
        ny = round(y / (height / self.max_y))
        return nx, ny


class Touch(object):
    """
        通过setevent操作,需要root权限,可以多点触控
        函数内时间单位为ms,间隔最好不要低于50ms
    """

    def __init__(self, adb: ADB):
        self.adb = adb
        path, max_x, max_y = self._get_event()
        self.event_path = path
        self.Touch_event = Touch_event(adb, max_x, max_y)

    def _get_event(self):
        """获取触摸的event文件"""
        devices = self.adb.raw_shell(['getevent', '-p'])
        # 按照add device拆分
        patter = re.compile(r'add device [\s\S]+?input props:')
        devices = [*patter.findall(devices)]
        # 找到含有ABS (0003)的devices
        patter = re.compile('ABS \(0003\): ')
        device = ''
        for k, v in enumerate(devices):
            if patter.findall(v):
                device = devices[k]
                continue
        if not device:
            raise ValueError("input event not found\n{}".format(devices))
        # 获取path
        patter = re.compile('add device.+:(.+?)\s')
        path = patter.findall(device)[0].strip()
        # 获取0035 0036
        patter = re.compile('0035.+:(.+?)\n.+0036.+:(.+?)\n')
        width, height = patter.findall(device)[0]
        patter = re.compile(r'[\s\S]+?max (.+?),')
        width = int(patter.findall(width)[0])
        height = int(patter.findall(height)[0])
        logger.info('get event path:{}, eventSize(width={},height={})', path, width, height)
        return path, width, height

    def _build_down(self,  x: int, y: int, index: int = 1):
        x, y = self.Touch_event.transform(x, y)
        eventPath = self.event_path
        event_id = self.Touch_event.event_id
        self.Touch_event.add_event_id()
        self.Touch_event.index_down(index)
        t = (
            'sendevent {} {} {} {}'.format(eventPath, 3, 47, index - 1),
            'sendevent {} {} {} {}'.format(eventPath, 3, 57, event_id),
            'sendevent {} {} {} {}'.format(eventPath, 1, 330, 1),
            'sendevent {} {} {} {}'.format(eventPath, 3, 58, 2),
            'sendevent {} {} {} {}'.format(eventPath, 3, 53, int(x)),
            'sendevent {} {} {} {}'.format(eventPath, 3, 54, int(y)),
            'sendevent {} 0 0 0'.format(eventPath),
        )
        return '&&'.join(t)

    def _build_up(self, x: int, y: int, index: int = 1):
        x, y = self.Touch_event.transform(x, y)
        eventPath = self.event_path
        index_count = self.Touch_event.index_count
        self.Touch_event.index_up(index)
        if index_count > 1:
            t = (
                'sendevent {} {} {} {}'.format(eventPath, 3, 47, index - 1),
                'sendevent {} {} {} {}'.format(eventPath, 3, 57, -1),
                'sendevent {} 0 0 0'.format(eventPath),
            )
        else:
            t = (
                'sendevent {} {} {} {}'.format(eventPath, 3, 47, index - 1),
                'sendevent {} {} {} {}'.format(eventPath, 3, 57, -1),
                'sendevent {} {} {} {}'.format(eventPath, 1, 330, 0),
                'sendevent {} 0 0 0'.format(eventPath),
            )
        return '&&'.join(t)

    def down(self, x: int, y: int, index: int = 1):
        s = self._build_down(x, y, index)
        self.adb.start_shell(s)

    def up(self, x: int, y: int, index: int = 1):
        s = self._build_up(x, y, index)
        self.adb.start_shell(s)

    def click(self, x: int, y: int, index: int = 0, duration: int = 20):
        down = self._build_down(x, y, index)
        up = self._build_up(x, y, index)
        self.adb.start_shell('{}&&{}'.format(down, up))

    def long_click(self, x: int, y: int, index: int = 1, duration: int = 500):
        down = self._build_down(x, y, index)
        up = self._build_up(x, y, index)
        self.adb.start_shell('&&'.join(down))
        self.sleep(duration)
        self.adb.start_shell('&&'.join(up))

    def sleep(self, duration: int = 50):
        time.sleep(duration / 1000)

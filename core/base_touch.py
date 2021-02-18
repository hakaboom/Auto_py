#! usr/bin/python
# -*- coding:utf-8 -*-
import re
import math
import time
from core.adb import ADB
from loguru import logger


class Touch_event(object):
    def __init__(self, event_path: str, event_size: dict, display_info: dict):
        self.event_id = 1
        self.index_count = 0
        self.index = [False, False, False, False, False, False, False, False, False, False, False]
        self.event_path = event_path
        self.event_size = event_size
        self.display_info = display_info
        self.event_scale = self.event_size2windows()

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

    def event_size2windows(self):
        return {
            'width': self.display_info['width'] / self.event_size['width'],
            'height': self.display_info['height'] / self.event_size['height']
        }

    def transform(self, x, y):
        if self.display_info['orientation'] == 0:
            return self.right2right(x, y)
        elif self.display_info['orientation'] == 1:
            return self.left2right(x, y)
        elif self.display_info['orientation'] == 2:
            return self.portrait2right(x, y)

    def right2right(self, x, y):
        return x / self.event_scale['width'], y / self.event_scale['height']

    def portrait2right(self, x, y):
        return (x / self.display_info['height'] * self.display_info['width']) / self.event_scale['width'], (
                y / self.display_info['width'] * self.display_info['height'] / self.event_scale['height'])

    def left2right(self, x, y):
        return (1 - x / self.display_info['height']) * self.display_info['width'] / self.event_scale['height'], (
                1 - y / self.display_info['width']) * self.display_info['height'] / self.event_scale['height']


class Touch(object):
    """
        基本触摸函数,通过adb操作
        函数内时间单位为ms,间隔最好不要低于50ms
        使用setevent
    """

    def __init__(self, adb: ADB):
        self.adb = adb
        path, name, width, height = self._get_event()
        self.event_path = path
        self.event_name = name
        self.event_size = {'width': width, 'height': height}
        self.display_info = self.adb.get_display_info()
        self.Touch_event = Touch_event(event_path=self.event_path, event_size=self.event_size,
                                       display_info=self.display_info)
        logger.info('adb_touch init, event_path:{}'.format(path))

    def _get_event(self):
        """获取包含0035,0036的event文件"""
        devices = self.adb.raw_shell(['getevent', '-p'])
        # 按照add device拆分
        patter = re.compile(r'add device.+:(.+?)\s+name:\s+\"(.+?)\"\s+[\s\S]{1,9999}0035.+:(.+?)\n.+0036.+:(.+?)\n')
        b = patter.findall(devices)
        if not b:
            raise ValueError("input event not found\n{}".format(devices))
        path, name, width, height = b[0]
        patter = re.compile(r'[\s\S]+?max (.+?),')
        width = int(patter.findall(width)[0])
        height = int(patter.findall(height)[0])
        if width < height:
            width, height = height, width
        return path, name, width, height

    def _build_down(self,  x: int, y: int, index: int = 1):
        x, y = self.Touch_event.transform(x, y)
        eventPath = self.Touch_event.event_path
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
        eventPath = self.Touch_event.event_path
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
        logger.info('adb touch point:(x={},y={})', x, y)

    def long_click(self, x: int, y: int, index: int = 1, duration: int = 500):
        down = self._build_down(x, y, index)
        up = self._build_up(x, y, index)
        self.adb.start_shell('&&'.join(down))
        self.sleep(duration)
        self.adb.start_shell('&&'.join(up))

    def sleep(self, duration: int = 50):
        time.sleep(duration / 1000)

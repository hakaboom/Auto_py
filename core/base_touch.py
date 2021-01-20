#! usr/bin/python
# -*- coding:utf-8 -*-
import re
import math
import time
from core.adb import ADB


class Touch_event(object):
    def __init__(self, event_path: str, event_size: dict, screen_size: dict, orientation: int = 1):
        self.event_id = 1
        self.index_count = 0
        self.index = [False, False, False, False, False, False, False, False, False, False, False]
        self.event_path = event_path
        self.event_size = event_size
        self.screen_size = screen_size
        self.event_scale = self.event_size2windows()
        self.orientation = orientation

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
            'width': self.screen_size['width'] / self.event_size['width'],
            'height': self.screen_size['height'] / self.event_size['height']
        }

    def transform(self, x, y):
        if self.orientation == 1:
            return self.right2right(x, y)
        if self.orientation == 2:
            return self.left2right(x, y)
        if self.orientation == 3:
            return self.portrait2right(x, y)

    def right2right(self, x, y):
        return x / self.event_scale['width'], y / self.event_scale['height']

    def portrait2right(self, x, y):
        return (x / self.screen_size['height'] * self.screen_size['width']) / self.event_scale['width'], (
                y / self.screen_size['width'] * self.screen_size['height'] / self.event_scale['height'])

    def left2right(self, x, y):
        return (1 - x / self.screen_size['height']) * self.screen_size['width'] / self.event_scale['height'], (
                1 - y / self.screen_size['width']) * self.screen_size['height'] / self.event_scale['height']


class Touch(object):
    """基本触摸函数,通过adb操作"""
    def __init__(self, adb: ADB, orientation: int = 1):
        self.adb = adb
        self.event_path = self._get_event_path()
        self.event_size = self._get_event_size()
        self.screen_size = {'width': 1280, 'height': 720}
        self.Touch_event = Touch_event(event_path=self.event_path, event_size=self.event_size,
                                       screen_size=self.screen_size, orientation=orientation)

    def _get_event_size(self):
        """获取event文件中的最大宽,高"""
        devices = self.adb.raw_shell(['getevent -p', self.event_path])
        for i in devices.split('\n'):
            i = i.rstrip()
            if i.find('0035  :') > -1:
                width = int(re.findall(r'max (.+?),', i)[0])
                continue
            if i.find('0036  :') > -1:
                height = int(re.findall(r'max (.+?),', i)[0])
                continue
        if width < height:
            width, height = height, width
        width = math.ceil(width / 10)
        height = math.ceil(height / 10)
        return {'width': width, 'height': height}

    def _get_event_path(self):
        """获取event文件位置"""
        devices = self.adb.raw_shell('cat /proc/bus/input/devices')
        t = [{}]
        for i in devices.split('\n'):
            l = i.split(': ')
            if len(l) == 1:
                t.append({})
            else:
                t[len(t) - 1][l[0]] = l[1].rstrip()
        for i in enumerate(t):
            if len(i[1]) == 0:
                pass
            else:
                if i[1]['N'] == 'Name="input"':
                    return '/dev/input/' + re.findall(r'event\d+', i[1]['H'])[0]

    def down(self, x: int, y: int, index: int = 1):
        x, y = self.Touch_event.transform(x, y)
        eventPath = self.Touch_event.event_path
        event_id = self.Touch_event.event_id
        self.Touch_event.add_event_id()
        self.Touch_event.index_down(index)
        t = (
                    # 'sendevent {} {} {} {}'.format(eventPath, 3, 47, index - 1),
                    'sendevent {} {} {} {}'.format(eventPath, 3, 57, event_id),
                    'sendevent {} {} {} {}'.format(eventPath, 1, 330, 1),
                    'sendevent {} {} {} {}'.format(eventPath, 3, 53, int(x * 10)),
                    'sendevent {} {} {} {}'.format(eventPath, 3, 54, int(y * 10)),
                    # 'sendevent {} {} {} {}'.format(eventPath, 3, 48, 5),
                    # 'sendevent {} {} {} {}'.format(eventPath, 3, 58, 50),
                    'sendevent {} 0 0 0'.format(eventPath),
                )
        self.adb.start_shell(';'.join(t))

    def up(self, x: int, y: int, index: int = 1):
        x, y = self.Touch_event.transform(x, y)
        eventPath = self.Touch_event.event_path
        self.Touch_event.index_up(index)
        if self.Touch_event.index_count > 0:
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
        self.adb.start_shell(';'.join(t))

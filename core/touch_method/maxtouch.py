#! usr/bin/python
# -*- coding:utf-8 -*-
import time
import sys
import re
from loguru import logger
from core.adb import ADB
from core.utils.nbsp import NonBlockingStreamReader
from core.utils.safesocket import SafeSocket
from core.utils.snippet import str2byte, get_std_encoding
from core.constant import TEMP_HOME, MAX_HOME, MAX_INSTALL_PATH, MAX_LOCAL_NAME
from .base import transform


class _Maxtouch(transform):
    def __init__(self, adb):
        self.adb = adb
        self.HOME = TEMP_HOME
        self.MAX_LOCAL_NAME = MAX_LOCAL_NAME.format(self.adb.get_device_id())
        self.MAX_PORT = 0
        self.max_x, self.max_y = None, None
        # 开启服务
        self.start_server()
        super(_Maxtouch, self).__init__(adb)

    def start_server(self):
        self.install()
        self.set_server()
        self.set_client()

    def _get_display_info(self):
        display_info = self.adb.get_display_info()
        display_info.update({
            'max_x': self.max_x,
            'max_y': self.max_y
        })
        return display_info

    def install(self):
        if not self.adb.check_file(self.HOME, 'maxpresent.jar'):
            logger.error('maxtouch is not install')
            self.push_target_maxtouch()

    def push_target_maxtouch(self):
        """push maxpresent.jar to device"""
        self.adb.push(MAX_INSTALL_PATH, MAX_HOME)
        time.sleep(1)
        self.adb.start_shell(['chmod', '755', MAX_HOME])
        logger.info('maxtouh installed in {}', MAX_HOME)

    def set_maxtouch_port(self):
        self.adb.set_forward('localabstract:%s' % self.MAX_LOCAL_NAME)
        self.MAX_PORT = self.adb.get_forward_port(self.MAX_LOCAL_NAME)
        if not self.MAX_PORT:
            raise logger.error('maxtouch port not set: local_name {}', self.MAX_LOCAL_NAME)
        logger.info("maxtouch start in port:{}", self.MAX_PORT)

    def set_server(self):
        self.set_maxtouch_port()
        # 如果之前服务在运行,则销毁
        self.adb.kill_process(name='app_process')
        p = self.adb.start_shell("app_process -Djava.class.path={0} /data/local/tmp com.netease.maxpresent.MaxPresent socket {1}".format(MAX_HOME, self.MAX_LOCAL_NAME))

        nbsp = NonBlockingStreamReader(p.stdout, name='maxtouch_server')
        line = nbsp.readline(timeout=5.0)
        if line is None:
            raise RuntimeError('maxtouch setup timeout')

        # 匹配出max_x, max_y
        line = line.decode(get_std_encoding(sys.stdout))
        m = re.search("Metrics Message : (\d+[^=]\d)=====(\d+[^=]\d)\r\n", line)
        if m:
            self.max_x = int(float(m.group(1)))
            self.max_y = int(float(m.group(2)))
        else:
            raise RuntimeError("maxtouch can not get max_x/max_y {}".format(line))
        if self.max_x < self.max_y:
            self.max_x, self.max_y = self.max_y, self.max_x

        if p.poll() is not None:
            # server setup error, may be already setup by others
            # subprocess exit immediately
            raise RuntimeError("maxtouch server quit immediately")
        self.server = p
        return p

    def set_client(self):
        s = SafeSocket()
        s.connect((self.adb.host, self.MAX_PORT))
        s.sock.settimeout(2)
        self.client = s

    def send(self, content: str):
        byte_connect = str2byte(content)
        self.client.send(byte_connect)
        return self.client.recv(0)


class Maxtouch(_Maxtouch):
    def transform_xy(self, x, y):
        width, height = self.size_info['width'], self.size_info['height']
        nx = x / width
        ny = y / height
        if nx > self.max_x or ny > self.max_y:
            raise OverflowError('坐标不能大于max值, x={},y={},max_x={},max_y={}'.format(nx, ny, self.max_x, self.max_y))
        return nx, ny

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

    def click(self, x: int, y: int, index: int = 0, duration: int = 20):
        self.down(x, y, index)
        time.sleep(duration / 1000)
        self.up(x, y, index)
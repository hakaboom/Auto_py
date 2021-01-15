# -*- coding: utf-8 -*-
import os
import re
import sys
import time
import random
import platform
import warnings
import subprocess
import threading
from typing import Union

import requests
from loguru import logger

THISPATH = os.path.dirname(os.path.realpath(__file__))
STATICPATH = os.path.join(THISPATH, "static")
DEFAULT_ADB_PATH = {
    "Windows": os.path.join(STATICPATH, "adb", "windows", "adb.exe"),
    "Darwin": os.path.join(STATICPATH, "adb", "mac", "adb"),
    "Linux": os.path.join(STATICPATH, "adb", "linux", "adb"),
    "Linux-x86_64": os.path.join(STATICPATH, "adb", "linux", "adb"),
    "Linux-armv7l": os.path.join(STATICPATH, "adb", "linux_arm", "adb"),
}


def split_cmd(cmds):
    """
    Split the commands to the list for subprocess
    Args:
        cmds: command(s)
    Returns:
        array commands
    """
    # cmds = shlex.split(cmds)  # disable auto removing \ on windows
    return cmds.split() if isinstance(cmds, str) else list(cmds)


def get_std_encoding(stream):
    return getattr(stream, "encoding", None) or sys.getfilesystemencoding()


class AdbError(Exception):
    """
        This is AdbError BaseError
        When ADB have something wrong
    """
    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return "stdout[%s] stderr[%s]" % (self.stdout, self.stderr)


class ADB(object):
    """adb object class"""
    status_device = 'device'
    status_offline = 'offline'
    SHELL_ENCODING = 'utf-8'

    def __init__(self, device_id=None, adb_path=None, host='127.0.0.1', port=5037):
        self.device_id = device_id
        self.adb_path = adb_path or self.builtin_adb_path()
        self._set_cmd_options(host, port)
        self._sdk_version = 0

    @staticmethod
    def builtin_adb_path() -> str:
        """adb路径"""
        system = platform.system()
        machine = platform.machine()
        adb_path = DEFAULT_ADB_PATH.get('{}-{}'.format(system, machine))
        if not adb_path:
            adb_path = DEFAULT_ADB_PATH.get(system)
        if not adb_path:
            raise RuntimeError("No adb executable supports this platform({}-{}).".format(system, machine))

        # overwrite uiautomator adb
        if "ANDROID_HOME" in os.environ:
            del os.environ["ANDROID_HOME"]
        return adb_path

    def _set_cmd_options(self, host, port):
        """设置adb服务器"""
        self.host = host
        self.port = port
        self.cmd_options = [self.adb_path]
        if self.host not in ("localhost", "127.0.0.1"):
            self.cmd_options += ['-H', self.host]
        if self.port != 5037:
            self.cmd_options += ['-P', str(self.port)]

    def start_server(self):
        """
        等于 adb start-server

        :return: None
        """
        return self.cmd('start-server', devices=False)

    def kill_server(self):
        """
        等于 adb kill-server

        :return: None
        """
        return self.cmd('kill-server', devices=False)

    def start_cmd(self, cmds, devices=True):
        """
        用cmds创建一个subprocess

        :param cmds:
            需要运行的参数,可以是list,str
        :param devices:
            如果为True,则需要指定device-id,命令中会传入-s
        :return:
            subprocess.Popen
        """
        if devices:
            if not self.device_id:
                raise logger.error('please set device_id first')
            cmd_options = self.cmd_options + ['-s', self.device_id]
        else:
            cmd_options = self.cmd_options

        cmds = cmd_options + split_cmd(cmds)
        logger.debug(" ".join(cmds))
        proc = subprocess.Popen(
            cmds,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return proc

    @staticmethod
    def close_proc_pipe(proc):
        """
        关闭stdin,stdout,stderr流对象
        :param proc: 
            选择关闭的Popen对象
        :return:
            None 
        """""

        def close_pipe(pipe):
            if pipe:
                pipe.close()

        close_pipe(proc.stdin)
        close_pipe(proc.stdout)
        close_pipe(proc.stderr)

    def cmd(self, cmds, devices=True, ensure_unicode=True, timeout=None):
        """
        用cmds创建adb命令,并且返回stdout

        :param cmds:
            需要运行的参数,可以是list,str
        :param devices:
            如果为True,则需要指定device-id,命令中会传入-s
        :param ensure_unicode:
            是否解码stdout,stderr
        :param timeout:
            设置命令超时时间
        :return:
            返回命令结果stdout
        """
        proc = self.start_cmd(cmds, devices)
        if timeout:
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                logger.error("Command {cmd} time out after {timeout} seconds: stdout['{stdout}'], stderr['{stderr}']".
                             format(cmd=proc.args, timeout=timeout,
                                    stdout=stdout, stderr=stderr))
                raise
        else:
            stdout, stderr = proc.communicate()

        if ensure_unicode:
            stdout = stdout.decode(get_std_encoding(stdout))
            stderr = stderr.decode(get_std_encoding(stderr))

        if proc.returncode > 0:
            # adb error
            raise logger.error("adb connection error {stdout} {stderr}".format(stderr=stderr, stdout=stdout))
        return stdout

    def devices(self, state=None):
        """
        adb devices,返回一个list包含了devices
        :param state:
            过滤属性比如: 'device', 'offline'
        :return:
            返回adb设备列表 List
        """
        patten = re.compile(r'^[\w\d.:-]+\t[\w]+$')
        device_list = []
        # self.start_server()
        output = self.cmd("devices", devices=False)
        for line in output.splitlines():
            line = line.strip()
            if not line or not patten.match(line):
                continue
            serialno, cstate = line.split('\t')
            if state and cstate != state:
                continue
            device_list.append((serialno, cstate))
        return device_list

    def connect(self):
        """
        运行adb connect命令
        :return:
            None
        """
        if self.device_id and ':' in self.device_id:
            connect_result = self.cmd("connect %s" % self.device_id)
            logger.info(connect_result)

    def disconnect(self):
        """
        运行adb disconnect
        :return:
            None
        """
        if ':' in self.device_id:
            self.cmd("disconnect %s" % self.device_id)

    def start_shell(self, cmds):
        """
        运行adb shell
        :param cmds:
            需要运行的参数,可以是list,str
        :return:
            subprocess.Popen
        """
        cmds = ['shell'] + split_cmd(cmds)
        return self.start_cmd(cmds)

    def raw_shell(self, cmds, ensure_unicode: bool = True):
        """
        运行adb shell并返回
        :param cmds:
            需要运行的参数,可以是list,str
        :param ensure_unicode:
        :return:
            返回命令结果stdout
        """
        cmds = ['shell'] + split_cmd(cmds)
        stdout = self.cmd(cmds, ensure_unicode=False)
        if not ensure_unicode:
            return stdout
        try:
            return stdout.decode(self.SHELL_ENCODING)
        except UnicodeDecodeError:
            logger.error('shell output decode {} fail. repr={}'.format(self.SHELL_ENCODING, repr(stdout)))
            return str(repr(stdout))

    def shell(self, cmd):

        if self.sdk_version < 25:
            # sdk_version < 25, adb shell 不返回错误
            # https://issuetracker.google.com/issues/36908392
            cmd = split_cmd(cmd) + [";", "echo", "---$?---"]
            out = self.raw_shell(cmd).rstrip()
            m = re.match("(.*)---(\d+)---$", out, re.DOTALL)
            if not m:
                warnings.warn("return code not matched")
                stdout = out
                returncode = 0
            else:
                stdout = m.group(1)
                returncode = int(m.group(2))
            if returncode > 0:
                raise logger.error('adb shell error')
            return stdout
        else:
            try:
                out = self.raw_shell(cmd)
            except AdbError as err:
                raise logger.error("stdout={},stderr={}".format(err.stdout,err.stderr))
            else:
                return out

    @property
    def sdk_version(self):
        """
        获取SDK version
        :return:
            SDK version
        """
        if self._sdk_version is None:
            self._sdk_version = int(self.getprop('ro.build.version.sdk'))
        return self._sdk_version

    def push(self, local, remote):
        """
        运行adb push
        :param local:
            需要发送的文件路径
        :param remote:
            发送到设备上的路径
        :return:
            None
        """
        self.cmd(["push", local, remote], ensure_unicode=False)
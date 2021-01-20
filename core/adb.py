#! usr/bin/python
# -*- coding:utf-8 -*-
import os
import re
import sys
import time
import random
import socket
import platform
import warnings
import subprocess
from typing import Union, Tuple

from core.utils import split_cmd, split_process_status,get_std_encoding,AdbError

from loguru import logger

THISPATH = os.path.dirname(os.path.realpath('static'))
STATICPATH = os.path.join(THISPATH, "static")
DEFAULT_ADB_PATH = {
    "Windows": os.path.join(STATICPATH, "adb", "windows", "adb.exe"),
    "Darwin": os.path.join(STATICPATH, "adb", "mac", "adb"),
    "Linux": os.path.join(STATICPATH, "adb", "linux", "adb"),
    "Linux-x86_64": os.path.join(STATICPATH, "adb", "linux", "adb"),
    "Linux-armv7l": os.path.join(STATICPATH, "adb", "linux_arm", "adb"),
}


class ADB(object):
    """adb object class"""
    status_device = 'device'
    status_offline = 'offline'
    SHELL_ENCODING = 'utf-8'

    def __init__(self, device_id=None, adb_path=None, host='127.0.0.1', port=5037):
        self.device_id = device_id
        self.adb_path = adb_path or self.builtin_adb_path()
        self._set_cmd_options(host, port)
        self._forward_local_using = self.get_forwards()  # 已经使用的端口
        self.connect()
        self._display_info = []  # 需要通过minicap模块获取
        self._sdk_version = int(self.sdk_version())

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

    def _set_cmd_options(self, host: str, port: int):
        """
        设置adb服务器
        Args:
            host: adb路径
            port: adb端口号
        Returns:
            None
        """
        self.host = host
        self.port = port
        self.cmd_options = [self.adb_path]
        if self.host not in ("localhost", "127.0.0.1"):
            self.cmd_options += ['-H', self.host]
        if self.port != 5037:
            self.cmd_options += ['-P', str(self.port)]

    def start_server(self):
        """
        command 'adb start-server'

        :return: None
        """
        return self.cmd('start-server', devices=False)

    def kill_server(self):
        """
        command 'adb kill-server'

        :return: None
        """
        return self.cmd('kill-server', devices=False)

    def start_cmd(self, cmds: Union[list, str], devices: bool = True) -> subprocess.Popen:
        """
        用cmds创建一个subprocess.Popen

        Args:
            cmds: 需要运行的参数,可以是list,str
            devices: 如果为True,则需要指定device-id,命令中会传入-s
        Returns:
            subprocess.Popen
        """
        cmds = split_cmd(cmds)
        if devices:
            if not self.device_id:
                raise logger.error('please set device_id first')
            cmd_options = self.cmd_options + ['-s', self.device_id]
            logger.debug('adb -s {} {}', self.device_id, " ".join(cmds))
        else:
            cmd_options = self.cmd_options
            logger.debug('adb {}', " ".join(cmds))

        cmds = cmd_options + cmds
        proc = subprocess.Popen(
            cmds,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return proc

    @staticmethod
    def close_proc_pipe(proc: subprocess.Popen) -> None:
        """
        关闭stdin,stdout,stderr流对象

        Args: 
            proc: 选择关闭的Popen对象

        Returns:
             None 
        """""

        def close_pipe(pipe):
            if pipe:
                pipe.close()

        close_pipe(proc.stdin)
        close_pipe(proc.stdout)
        close_pipe(proc.stderr)

    def cmd(self, cmds: Union[list, str], devices: bool = True, ensure_unicode: bool = True, timeout: int = None,
            skip_error: bool = False):
        """
        用cmds创建adb命令,并且返回stdout

        Args:
            cmds: 需要运行的参数,可以是list,str
            devices: 如果为True,则需要指定device-id,命令中会传入-s
            ensure_unicode: 是否解码stdout,stderr
            timeout: 设置命令超时时间
            skip_error: 是否跳过报错

        Returns:
            返回命令结果stdout
        """
        proc = self.start_cmd(cmds, devices)
        if timeout:
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                logger.error("Command {cmd} time out after {timeout} seconds: stdout['{stdout}'], stderr['{stderr}']",
                             cmd=proc.args, timeout=timeout,
                             stdout=stdout, stderr=stderr)
                raise
        else:
            stdout, stderr = proc.communicate()
        if ensure_unicode:
            stdout = stdout.decode(get_std_encoding(stdout))
            stderr = stderr.decode(get_std_encoding(stderr))

        if proc.returncode > 0:
            # adb error
            logger.error("adb connection {stdout} {stderr}", stdout=stdout, stderr=stderr)
            if not skip_error:
                raise AdbError(stdout, stderr)
        return stdout

    def devices(self, state: bool = None):
        """
        command adb devices

        Args:
            state: 过滤属性比如: 'device', 'offline'
        Returns:
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
        command adb connect

        Returns:
             None
        """
        if self.device_id and ':' in self.device_id:
            connect_result = self.cmd("connect %s" % self.device_id)
            logger.info(connect_result)

    def disconnect(self):
        """
        command adb disconnect

        Returns:
             None
        """
        if ':' in self.device_id:
            self.cmd("disconnect %s" % self.device_id)

    def start_shell(self, cmds: Union[list, str]) -> start_cmd:
        cmds = ['shell'] + split_cmd(cmds)
        return self.start_cmd(cmds)

    def raw_shell(self, cmds: Union[list, str], ensure_unicode: bool = True, skip_error: bool = False):
        cmds = ['shell'] + split_cmd(cmds)
        stdout = self.cmd(cmds, ensure_unicode=False, skip_error=skip_error)
        if not ensure_unicode:
            return stdout
        try:
            return stdout.decode(self.SHELL_ENCODING)
        except UnicodeDecodeError:
            logger.error('shell output decode {} fail. repr={}', self.SHELL_ENCODING, repr(stdout))
            return str(repr(stdout))

    def shell(self, cmd: Union[list, str]):
        if self._sdk_version < 25:
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
                raise logger.error("stdout={},stderr={}", err.stdout, err.stderr)
            else:
                return out

    def forward(self, local: str, remote: str, no_rebind: bool = True):
        """
        command adb forward

        Args:
            local: 要转发的本地端口 tcp:<local>

            remote: 要与local绑定的设备端口 localabstract:{remote}"`
        :return:
            None
        """
        is_use, index = self._local_in_forwards(local, remote)
        if not is_use:
            cmds = ['forward']
            if no_rebind:
                cmds += ['--no-rebind']
            self.cmd(cmds + [local, remote])
            self._forward_local_using.append({'local': local, 'remote': remote})
            logger.debug('forward {} {}', local, remote)
        else:
            logger.info('{} {} has been forward', self._forward_local_using[index]['local'],
                        self._forward_local_using[index]['remote'])

    def get_forwards(self) -> list:
        """
        command adb forward --list

        :return:
            返回一个包含占用信息的列表,每个包含键值local和remote
        """
        l = []
        out = self.cmd(['forward', '--list'])
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            cols = line.split()
            if len(cols) != 3:
                continue
            device_id, local, remote = cols
            l.append({'local': local, 'remote': remote})
        return l

    def get_available_forward_local(self) -> int:
        """
        获取一个可用端口
        :return:
            port
        """
        sock = socket.socket()
        port = random.randint(11111, 20000)
        result = False
        try:
            sock.bind(('127.0.0.1', port))
            result = True
            # logger.debug('port:{} can use'.format(port))
        except:
            logger.debug('port:{} is in use'.format(port))
        sock.close()
        if not result:
            return self.get_available_forward_local()
        return port

    def set_forward(self, remote: str):
        """
        通过get_available_forward_local获取可用端口,并与remote绑定

        Args:
            remote: 要与local绑定的设备端口 localabstract:{remote}"

        :return:
            None
        """
        localport = self.get_available_forward_local()
        self.forward('tcp:%s' % localport, remote)

    def _local_in_forwards(self, local: str = None, remote: str = None) -> Tuple[bool, int]:
        """
        检查local是否已经启用

        :return:
            bool, if True return index in _forward_local_using
        """
        l = self.get_forwards()
        for i in range(len(l)):
            if local:
                if l[i]['local'] == local:
                    return True, i
            if remote:
                if l[i]['remote'] == remote:
                    return True, i
        return False, None

    def remove_forward(self, local=None):
        """
        运行adb forward -- remove
        :param local:
            tcp port,如不填写则清楚所以绑定
        :return:
            None
        """
        if local:
            cmds = ['forward', '--remove', local]
        else:
            cmds = ['forward', '--remove-all']
        self.cmd(cmds)
        local_using, index = local and self._local_in_forwards(local) or (False, -1)
        # 删除在_forward_local_using里的记录
        if local_using:
            del self._forward_local_using[index]

    def push(self, local, remote) -> None:
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

    def pull(self, remote, local) -> None:
        """
        运行adb pull
        :param remote:
            设备上的路径
        :param local:
            pull到本地的路径
        :return:
            None
        """
        self.cmd(["pull", remote, local], ensure_unicode=False)

    def abi_version(self):
        """ get abi (application binary interface) """
        abi = self.raw_shell(['getprop', 'ro.product.cpu.abi'])
        logger.info('device {} abi is {}'.format(self.device_id, abi).rstrip('\r\n'))
        return abi

    def sdk_version(self):
        """ get sdk version """
        sdk = self.raw_shell(['getprop', 'ro.build.version.sdk'])
        logger.info('device {} sdk is {}'.format(self.device_id, sdk).rstrip('\r\n'))
        return sdk

    def check_file(self, path: str, name: str) -> bool:
        """
        command adb shell find 'name' in the 'path'

        Args:
            path: 在设备上的路径

            name: 需要检查的文件
        :return:
            bool
        """
        return bool(self.raw_shell(['find', path, '-name', name]))

    def get_process_status(self, pid: int = None, name: str = None) -> list:
        """
        adb shell ps

        Args:
            pid: 按照pid寻找
            name: 通过grep寻找匹配的name(并不是精准寻找,只要有匹配的项都会返回)
        :return:
            list 每一项都包含了ps信息
        """
        if pid:
            shell = ['ps -x', str(pid)]
        elif name:
            shell = "ps | grep \"{}\"".format(name)
        else:
            shell = 'ps'
        out = self.raw_shell(shell, skip_error=True)
        return split_process_status(out)

    def kill_process(self, pid: int = None, name: str = None):
        """
        command adb shell kill [pid]
        :param name: 需要杀死的进程名
        :param pid: 需要杀死的进程pid
        :return:
            None
        """
        if pid:
            out = self.get_process_status(pid=pid)
            if out:
                pid = out[0]['PID']
            else:
                logger.error('pid：{} is not started', str(pid))
                return False
        elif name:
            out = self.get_process_status(name=name)
            if out:
                if len(out) > 1:
                    logger.info('匹配到多个进程')
                pid = out[0]['PID']
            else:
                logger.info('NAME: {} is not started', name)
                return False
        self.start_shell(['kill', str(pid)])

    def install_app(self, filepath, replace=False):
        pass

    def get_device_id(self):
        return self.device_id

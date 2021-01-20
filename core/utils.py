#! usr/bin/python
# -*- coding:utf-8 -*-
import re
import sys


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


def split_process_status(out):
    l = []
    for line in out.splitlines():
        line = line + '\t'
        line = re.compile("(\S+)").findall(line)
        if len(line) > 8:
            l.append({
                'User': line[0],  # 所属用户
                'PID': line[1],  # 进程 ID
                'PPID': line[2],  # 父进程 ID
                'VSIZE': line[3],  # 进程的虚拟内存大小，以KB为单位
                'RSS': line[4],  # 进程实际占用的内存大小，以KB为单位
                'WCHAN': line[5],  # 进程正在睡眠的内核函数名称；
                'PC': line[6],  # 计算机中提供要从“存储器”中取出的下一个指令地址的寄存器
                'NAME': line[8]  # 进程名
            })
    return len(l) > 0 and l or None


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

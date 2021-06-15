#! usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import re
import subprocess
from loguru import logger as loguru
from core.constant import filter_level


def initLogger():
    loguru.remove()  # 清除自带的
    loguru.add(sys.stdout, format="<green>{time:YYYY-MM-dd HH:mm:ss.SSS}</green> <red>|</red> "
                                  "<level><b>{level}</b></level>     <red>|</red> "
                                  "<cyan>{name}</cyan><red>:</red>"
                                  "<cyan>{function}</cyan><red>:</red>"
                                  "<cyan>{line}</cyan> <red>-</red> "
                                  "<level>{message}</level>",
               colorize=True, filter=filter_level)


def get_varible_name(var):
    for item in sys._getframe(2).f_locals.items():
        if (var is item[1]):
            return item[0]


def get_type(value):
    s = re.findall(r'<class \'(.+?)\'>', str(type(value)))
    if s:
        return s[0]
    else:
        raise ValueError('unknown error,can not get type: value={}, type={}'.format(value, type(value)))


def get_space(SpaceNum=1):
    return '\t'*SpaceNum


def pprint(*args):
    _str = []
    for index, value in enumerate(args):
        if isinstance(value, (dict, tuple, list)):
            _str.append('[{index}]({type}) = {value}\n'.format(index=index, value=_print(value),
                                                                     type=get_type(value)))
        else:
            _str.append('[{index}]({type}) = {value}\n'.format(index=index, value=value,
                                                                   type=get_type(value)))
    print(''.join(_str))


def _print(args, SpaceNum=1):
    _str = []
    SpaceNum += 1
    if isinstance(args, (tuple, list)):
        _str.append('')
        for index, value in enumerate(args):
            _str.append('{space}[{index}]({type}) = {value}'.format(index=index, value=_print(value, SpaceNum),
                                                                    type=get_type(value), space=get_space(SpaceNum)))
    elif isinstance(args, dict):
        _str.append('')
        for key, value in args.items():
            _str.append('{space}[{key}]({type}) = {value}'.format(key=key, value=_print(value,SpaceNum),
                                                                  type=get_type(value), space=get_space(SpaceNum)))
    else:
        _str.append(str(args))

    return '\n'.join(_str)


if sys.platform.startswith("win"):
    # Don't display the Windows GPF dialog if the invoked program dies.
    try:
        SUBPROCESS_FLAG = subprocess.CREATE_NO_WINDOW  # in Python 3.7+
    except AttributeError:
        import ctypes
        SEM_NOGPFAULTERRORBOX = 0x0002  # From MSDN
        ctypes.windll.kernel32.SetErrorMode(SEM_NOGPFAULTERRORBOX)  # win32con.CREATE_NO_WINDOW?
        SUBPROCESS_FLAG = 0x8000000
else:
    SUBPROCESS_FLAG = 0
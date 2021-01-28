#! usr/bin/python
# -*- coding:utf-8 -*-
import os
import sys
import re
import threading
from functools import wraps
import queue


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
    """
    Get encoding of the stream
    Args:
        stream: stream
    Returns:
        encoding or file system encoding
    """
    return getattr(stream, "encoding", None) or sys.getfilesystemencoding()


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


CLEANUP_CALLS = queue.Queue()
IS_EXITING = False


def reg_cleanup(func, *args, **kwargs):
    """
    Clean the register for given function
    Args:
        func: function name
        *args: optional argument
        **kwargs: optional arguments
    Returns:
        None
    """
    CLEANUP_CALLS.put((func, args, kwargs))


def _cleanup():
    # cleanup together to prevent atexit thread issue
    while not CLEANUP_CALLS.empty():
        (func, args, kwargs) = CLEANUP_CALLS.get()
        func(*args, **kwargs)


# atexit.register(_cleanup)

_shutdown = threading._shutdown


def exitfunc():
    global IS_EXITING
    IS_EXITING = True
    _cleanup()
    _shutdown()


def is_exiting():
    return IS_EXITING


# use threading._shutdown to exec cleanup when main thread exit
# atexit exec after all thread exit, which needs to cooperate with daemon thread.
# daemon thread is evil, which abruptly exit causing unexpected error
threading._shutdown = exitfunc


def on_method_ready(method_name):
    """
    Wrapper for lazy initialization of some instance methods
    Args:
        method_name: instance method name
    Returns:
        wrapper
    """
    def wrapper(func):
        @wraps(func)
        def ready_func(inst, *args, **kwargs):
            key = "_%s_ready" % method_name
            if not getattr(inst, key, None):
                method = getattr(inst, method_name)
                method()
                setattr(inst, key, True)
            return func(inst, *args, **kwargs)
        return ready_func
    return wrapper


def ready_method(func):
    @wraps(func)
    def wrapper(inst, *args, **kwargs):
        ret = func(inst, *args, **kwargs)
        key = "_%s_ready" % func.__name__
        if not getattr(inst, key, None):
            setattr(inst, key, True)
        return ret
    return wrapper


def str2byte(content):
    """ compile str to byte """
    return content.encode("utf-8")


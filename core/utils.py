#! usr/bin/python
# -*- coding:utf-8 -*-
import re
import sys
import time
import queue
from threading import Thread, Event


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


def str2byte(content):
    """ compile str to byte """
    return content.encode("utf-8")


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


class NonBlockingStreamReader:

    def __init__(self, stream, raise_EOF=False, print_output=True, print_new_line=True, name=None):
        """
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        raise_EOF: if True, raise an UnexpectedEndOfStream
                when stream is EOF before kill
        print_output: if True, print when readline
        """
        self._s = stream
        self._q = queue.Queue()
        self._lastline = None
        self.name = name or id(self)

        def _populateQueue(stream, queue, kill_event):
            """
            Collect lines from 'stream' and put them in 'quque'.
            """
            while not kill_event.is_set():
                line = stream.readline()
                if line:
                    queue.put(line)
                    if print_output:
                        # print only new line
                        if print_new_line and line == self._lastline:
                            continue
                        self._lastline = line
                elif kill_event.is_set():
                    break
                elif raise_EOF:
                    raise
                else:
                    # print("EndOfStream: %s" % self.name)
                    break

        self._kill_event = Event()
        self._t = Thread(target=_populateQueue, args=(self._s, self._q, self._kill_event), name="nbsp_%s" % self.name)
        self._t.daemon = True
        self._t.start()  # start collecting lines from the stream

    def readline(self, timeout=None):
        try:
            return self._q.get(block=timeout is not None, timeout=timeout)
        except queue.Empty:
            return None

    def read(self, timeout=0):
        time.sleep(timeout)
        lines = []
        while True:
            line = self.readline()
            if line is None:
                break
            lines.append(line)
        return b"".join(lines)

    def kill(self):
        self._kill_event.set()

#! usr/bin/python
# -*- coding:utf-8 -*-
import sys
from core.utils.snippet import get_std_encoding


class AdbError(Exception):
    """
        This is AdbError BaseError
        When ADB have something wrong
    """
    def __init__(self, stdout, stderr, cmds):
        self.stdout = stdout.decode(get_std_encoding(stdout)).rstrip()
        self.stderr = stderr.decode(get_std_encoding(stderr)).rstrip()
        self.cmds = cmds

    def __str__(self):
        # device not found
        # re.findall('device \'(.+?)\' not found', self.stderr)
        return "stdout[%s],stderr[%s]\ncmds[%s]" % (self.stdout, self.stderr, ' '.join(self.cmds))


class OcrError(Exception):
    """
        when ocr goes wrong
    """
    def __str__(self):
        return 'ocr出现错误,请检查报错信息'

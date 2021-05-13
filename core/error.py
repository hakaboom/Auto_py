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


class SurfCudaError(Exception):
    def __init__(self, image):
        self.image = image

    def __str__(self):
        return


class CvError(SurfCudaError):
    def __init__(self, image):
        self.image = image

# -*- coding: utf-8 -*-
import os

# ADB
THISPATH = os.path.dirname(os.path.realpath('static'))
STATICPATH = os.path.join(THISPATH, "static")
DEFAULT_ADB_PATH = {
    "Windows": os.path.join(STATICPATH, "adb", "windows", "adb.exe"),
    "Darwin": os.path.join(STATICPATH, "adb", "mac", "adb"),
    "Linux": os.path.join(STATICPATH, "adb", "linux", "adb"),
    "Linux-x86_64": os.path.join(STATICPATH, "adb", "linux", "adb"),
    "Linux-armv7l": os.path.join(STATICPATH, "adb", "linux_arm", "adb"),
}
SHELL_ENCODING = 'utf-8'

# minicap
TEMP_HOME = '/data/local/tmp'
MNC_HOME = '/data/local/tmp/minicap'
MNC_SO_HOME = '/data/local/tmp/minicap.so'
MNC_CMD = 'LD_LIBRARY_PATH={} {}'.format(TEMP_HOME, MNC_HOME)
MNC_CAP_PATH = 'temp_{}.png'.format
MNC_LOCAL_NAME = 'minicap_{}'.format
MNC_INSTALL_PATH = "./static/stf_libs/{}/minicap".format
MNC_SO_INSTALL_PATH = "./static/stf_libs/minicap-shared/aosp/libs/android-{}/{}/minicap.so".format


# minitouch
MNT_HOME = '/data/local/tmp/minitouch'
MNT_LOCAL_NAME = 'minitouch_{}'.format
MNT_INSTALL_PATH = "./static/stf_libs/{}/minitouch".format

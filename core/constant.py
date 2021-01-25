# -*- coding: utf-8 -*-
import os

# ADB
THISPATH = os.path.dirname(os.path.realpath('static'))
STATICPATH = os.path.join(THISPATH, "static")
DEFAULT_ADB_PATH = {  # adb.exe路径
    "Windows": os.path.join(STATICPATH, "adb", "windows", "adb.exe"),
    "Darwin": os.path.join(STATICPATH, "adb", "mac", "adb"),
    "Linux": os.path.join(STATICPATH, "adb", "linux", "adb"),
    "Linux-x86_64": os.path.join(STATICPATH, "adb", "linux", "adb"),
    "Linux-armv7l": os.path.join(STATICPATH, "adb", "linux_arm", "adb"),
}
SHELL_ENCODING = 'utf-8'  # adb shell的编码
ADB_CAP_NAME_RAW = '{}.raw'  # 使用ADB截图时生成raw的文件名
ADB_CAP_NAME = 'tmp_{}.png'  # 使用ADB截图时png保存到电脑的路径
ADB_CAP_PATH = '/data/local/tmp/{}'  # 使用ADB截图时在手机上的路径

# minicap
TEMP_HOME = '/data/local/tmp'  # 临时文件路径
MNC_HOME = '/data/local/tmp/minicap'  # minicap文件在手机上的路径
MNC_SO_HOME = '/data/local/tmp/minicap.so'  # minicap.so文件在手机上的路径
MNC_CMD = 'LD_LIBRARY_PATH={} {}'.format(TEMP_HOME, MNC_HOME)  # 运行minicap的cmd命令
MNC_CAP_PATH = 'tmp_{}.png'  # minicap截图保存到电脑的路径
MNC_LOCAL_NAME = 'minicap_{}'  # minicap开放的端口名字
MNC_INSTALL_PATH = "./static/stf_libs/{}/minicap"  # abi_version  minicap安装文件路径
MNC_SO_INSTALL_PATH = "./static/stf_libs/minicap-shared/aosp/libs/android-{}/{}/minicap.so"  # sdk,abi version


# minitouch
MNT_HOME = '/data/local/tmp/minitouch'  # minitouch文件在手机上的路径
MNT_LOCAL_NAME = 'minitouch_{}'  # device_id  minitouch开发的端口名字
MNT_INSTALL_PATH = "./static/stf_libs/{}/minitouch"  # abi_version minitouch安装文件路径

# yosemite
YOSEMITE_APK = os.path.join(STATICPATH, "apks", "Yosemite.apk")
YOSEMITE_PACKAGE = 'com.netease.nie.yosemite'
YOSEMITE_IME_SERVICE = 'com.netease.nie.yosemite/.ime.ImeService'

# javacap
JAC_LOCAL_NAME = 'javacap_{}'
JAC_CAP_PATH = 'tmp_{}.png'

class TOUCH_METHOD(object):
    MINITOUCH = "MINITOUCH"
    ADBTOUCH = "ADBTOUCH"


class CAP_METHOD(object):
    MINICAP = "MINICAP"
    JAVACAP = 'JAVACAP'
    ADBCAP = "ADBCAP"


# logger filter_level
def filter_level(record):
    """
    需要过滤的等级
    'DEBUG' 'INFO' 'SUCCESS' 'WARNING' 'ERROR'
    """
    level = ['DEBUG']
    return record["level"].name not in level
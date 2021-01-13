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


from loguru import logger

class ADB(object):
    '''adb object class'''
    status_devices = 'devices'
    status_offline = 'offline'

    def __init__(self, ):
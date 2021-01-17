# -*- coding: utf-8 -*-
import time
import timeit
import socket
import sys
import os
import random
import threading
import platform
import subprocess
from queue import Queue
from typing import Tuple,List
import re

import cv2
import numpy as np
from Minicap import connect

from adb import connect
from loguru import logger



a = connect(device_id='emulator-5554')
# a.set_minicap_port()
# a.start_mnc_server()
# a.screencap()
print(a.get_process_status(name='minicap'))
# a.kill_process(2266)
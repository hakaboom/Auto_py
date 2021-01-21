# -*- coding: utf-8 -*-
import time
import socket
import re
import subprocess
from core.run import Android
#
a = Android(device_id='emulator-5554')
a.screencap()
time.sleep(10)
a.minicap.start_mnc_server()
a.screencap()

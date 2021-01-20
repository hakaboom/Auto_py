# -*- coding: utf-8 -*-
import time
import threading
import subprocess
from core.run import Android

a = Android(device_id='emulator-5554')
a.screencap()
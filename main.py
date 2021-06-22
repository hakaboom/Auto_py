# -*- coding: utf-8 -*-
import cv2

from core.run import Android

device = Android(device_id='emulator-5554', cap_method='minicap')
device.screenshot()
device.javacap.teardown()

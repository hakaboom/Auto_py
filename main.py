# -*- coding: utf-8 -*-
import time
import threading
from core.run import Android

a = Android(device_id='emulator-5562')
a.screencap()
# def main1():
#     a = connect(device_id='emulator-5562')
#     a.set_minicap_port()
#     a.start_mnc_server()
#     a.screencap()
#
# def main2():
#     a = connect(device_id='emulator-5554')
#     a.set_minicap_port()
#     a.start_mnc_server()
#     a.screencap()
#
#
# class myThread (threading.Thread):
#     def __init__(self, threadID, name, counter):
#         threading.Thread.__init__(self)
#         self.threadID = threadID
#         self.name = name
#         self.counter = counter
#     def run(self):
#         globals()['main' + str(self.threadID)]()
# #
#
# thread1 = myThread(1, "Thread-1", 1)
# thread2 = myThread(2, "Thread-2", 2)
# thread1.start()
# thread2.start()

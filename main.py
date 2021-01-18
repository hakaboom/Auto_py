# -*- coding: utf-8 -*-
import time
import threading
from adb import connect

def main1():
    a = connect(device_id='emulator-5562')
    a.set_minicap_port()
    a.start_mnc_server()
    a.screencap()

def main2():
    a = connect(device_id='emulator-5554')
    a.set_minicap_port()
    a.start_mnc_server()
    a.screencap()


class myThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        print ("开始线程：" + self.name)
        globals()['main' + str(self.threadID)]()
        print ("退出线程：" + self.name)
#
# thread1 = myThread(1, "Thread-1", 1)
# thread2 = myThread(2, "Thread-2", 2)
# thread1.start()
# thread2.start()
main2()
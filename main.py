# -*- coding: utf-8 -*-
import time
# import re
# import sys
import cv2
import re
import numpy as np
from core.utils.base import pprint
from core.run import Android
#

# device = Android(device_id='192.168.1.192:5555', cap_method='adbcap')
# device.adb.install_app(filepath='E:\工作文件夹\铁道物语\sdk\\铁道0.9.5（4.17）.apk')

# device = Android(device_id='192.168.1.193:5555', cap_method='adbcap')
# device.adb.install_app(filepath='E:\sdk\\铁道0.9.5（4.17）.apk')



# print(device.adb.sdk_version(), device.adb.abi_version())
# device = Android(device_id='192.168.1.194:5555', cap_method='javacap')
# device.screenshot().save2path()
# cv2.namedWindow('capture', cv2.WINDOW_KEEPRATIO)
# while True:
#     img = device.screenshot().imread()
#     cv2.imshow('capture', img)
#     if cv2.waitKey(25) & 0xFF == ord('q'):
#         cv2.destroyAllWindows()
#         exit(0)

from core.utils.behavior_tree import Blackboard, Sequence

Main = Blackboard()
Main.set_value_bath(dict(count=0, index=1))
login = Sequence()
login.set_loop(True, -1, -1, 1)
login_success = Main.create_scene()
login_error = Main.create_scene()
login.add_scenes([login_success, login_error])


update = Sequence()
login_success.add_sequence(update)
update.set_loop(True, -1, -1, 1)
update_true = Main.create_scene()
update_error = Main.create_scene()
update.add_scenes([update_true, update_error])


"""
login(sequence) 
    - login_success(scene) add scene
            -- update(sequence) add sequence
                -- update_true(scene)
                -- update_error(scene)
    - login_error(scene) add scene
"""


@login_success.set_start_trigger
def login_success_rule(blackboard: Blackboard):
    return blackboard.get_value('count') == 0


@login_error.set_start_trigger
def login_error_rule(blackboard: Blackboard):
    return blackboard.get_value('index') == 0


@update_true.set_start_trigger
def update_true_rule(b: Blackboard):
    return False


@update_error.set_start_trigger
def update_error_rule(b: Blackboard):
    return False


login.run()
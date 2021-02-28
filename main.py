# -*- coding: utf-8 -*-
import time
# import re
# import sys
import cv2
import re
import numpy as np
from core.utils.base import pprint


from behavior_tree import Blackboard, Sequence

Main = Blackboard()
Main.set_value_bath(dict(count=0, index=1))
login = Sequence()
login.setLoop(True, -1, -1, 1)
login_success = Main.create_scene()
login_error = Main.create_scene()
login.add_scene(login_success, login_error)


update = Sequence()
login_success.add_sequence(update)
update.setLoop(True, -1, -1, 1)
update_true = Main.create_scene()
update_error = Main.create_scene()
update.add_scene(update_true, update_error)


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
    print("login_success")
    return blackboard.get_value('count') == 0


@login_error.set_start_trigger
def login_error_rule(blackboard: Blackboard):
    print("login_error")
    return blackboard.get_value('index') == 0


@update_true.set_start_trigger
def update_true_rule(b: Blackboard):
    print("update_true")
    return False


@update_error.set_start_trigger
def update_error_rule(b: Blackboard):
    print("update_False")
    return False


tree = login.get_scene_tree()
pprint(tree, 123123/141)
# -*- coding: utf-8 -*-
from inspect import isfunction
from core.utils.base import get_varible_name, pprint
import time
import sys


def none_fun(*args):
    pass


class Blackboard(object):
    def __init__(self):
        self.__tag = 'Blackboard'
        self.con = {}

    def set_value(self, member, value):
        self.con[member] = value

    def get_value(self, member, defaultValue=None):
        return self.con.get(member, defaultValue)

    def set_value_bath(self, value: dict):
        self.con.update(value)

    def get_all_value(self):
        return self.con

    def create_scene(self):
        return Scene(self)

    def create_sequence(self):
        return Sequence(self)


class Scene(object):
    """创建场景"""

    def __init__(self, blackboard):
        self.__tag = 'Scene'
        self.child = []
        self.blackboard = blackboard
        # 触发器
        self.startTrigger = Trigger(blackboard)  # 运行触发器
        self.endTrigger = Trigger(blackboard)  # 结束触发器
        # 行为器
        self.startingBehavior = Behavior(self)  # 运行前操作(一定会执行)
        self.doingBehavior = Behavior(self)  # 运行中循环操作(满足结束触发器则不会执行)
        self.endingBehavior = Behavior(self)  # 运行结束后操作(一定会执行)

    def add_sequence(self, sequence):
        if isinstance(sequence, Sequence):
            self.child.append(sequence)
        else:
            raise ValueError('value is not Sequence please check')

    def add_sequences(self, sequences: list):
        for sequence in sequences:
            self.add_sequence(sequence)

    def set_start_trigger(self, fun):
        if not isfunction(fun):
            raise ValueError('set start trigger Non function received: {}', fun)
        self.startTrigger.set_rule(fun)

    def set_doing_behavior(self, fun):
        if not isfunction(fun):
            raise ValueError('set_doing_behavior Non function received: {}', fun)
        self.doingBehavior.set_server(fun)

    def run(self):
        if self.startTrigger.check():
            self.startingBehavior.run()
            if not self.endTrigger.check():
                self.doingBehavior.run()
            self.endingBehavior.run()
            for sequence in self.child:
                sequence.run()
            return True
        return False


class Behavior(object):
    """行为器"""

    def __init__(self, Parent):
        self.__tag = 'Behavior'
        self.parent = Parent  # 设置父节点
        self.blackboard = Parent.blackboard
        self.triggerOnDelay = Trigger(Parent.blackboard)
        self.continuity = False  # 如果此项设置为true,则协程执行后不会自动销毁,再次运行这个动作的时候会继续上次的接着做
        self.co = None
        self.server = none_fun

    def set_server(self, serverFunction=None):
        if isfunction(serverFunction) or type(serverFunction).__name__ == 'method':
            self.server = serverFunction

    def run(self):
        self.server(self.blackboard)


class Trigger(object):
    """触发器"""

    def __init__(self, blackboard=None):
        self.__tag = 'Trigger'
        self.blackboard = blackboard
        self.rule = lambda _: None

    def set_rule(self, ruleFunction):
        if isfunction(ruleFunction) or type(ruleFunction).__name__ == 'method':
            self.rule = ruleFunction
            return True
        return False

    def check(self):
        if hasattr(self, 'blackboard'):
            return self.rule(self.blackboard)
        return self.rule(None)


class Sequence(object):
    """循环器"""

    def __init__(self, blackboard=None):
        self.__tag = 'Sequence'
        self.scenes = []
        self.isLoop = False
        self.maxCount = -1
        self.maxTime = -1
        self.loopIntervalTime = 0
        self.loopName = ''
        self.loopEndTrigger = Trigger(blackboard)

    def add_scene(self, scene):
        if isinstance(scene, Scene):
            self.scenes.append(dict(name=get_varible_name(scene), scene=scene))
        else:
            raise ValueError('{} is not Scene'.format(scene))

    def add_scenes(self, scenes: list):
        for scene in scenes:
            self.add_scene(scene)

    def get_end_trigger(self):
        return self.loopEndTrigger

    def set_loop(self, isLoop=False, loopCount=-1, loopTime=-1, IntervalTime=0, name=None):
        """
            设置场景检测的循环方式
            参数:	isLoop		Bool型,是否循环
                    loopCount 	循环次数
                    loopTime 	循环最长时间
                    IntervalTime每次循环的间隔(毫秒)
        """
        self.isLoop = isLoop
        self.maxCount = loopCount
        self.maxTime = loopTime
        self.loopIntervalTime = IntervalTime
        self.loopName = name or get_varible_name(self)

    def get_loop(self):
        return dict(isLoop=self.isLoop, maxCount=self.maxCount,
                    maxTime=self.maxTime, loopIntervalTime=self.loopIntervalTime)

    def run(self):
        flag = False
        loop_time = time.time()
        loop_count = 1
        while True:
            if flag:
                loop_time = time.time()
                loop_count = 0
            print('now running sequence: {}'.format(self.loopName))
            for v in self.scenes:
                flag = v['scene'].run()
                if flag:
                    break
            if self.loopEndTrigger.check():
                break
            loop_count += 1
            if self.loopIntervalTime > 0:
                time.sleep(self.loopIntervalTime)
            # 退出条件
            if (not flag and not self.isLoop) or ((self.isLoop and not flag) and (
                    not self.maxTime == -1 and (loop_time + self.maxTime < time.time()) or False) or (
                    not self.maxCount == -1 and (loop_count > self.maxCount) or False)):
                return

    def get_scene_tree(self):
        """通过遍历Sequence 获取当前节点下的子节点信息"""
        tree = []
        main_sequence_name = get_varible_name(self)
        for main_scenes in self.scenes:
            v = None
            if isinstance(main_scenes['scene'].child, Sequence):
                v = (main_scenes['name'], main_scenes['scene'].child.get_scene_tree())
            else:
                v = main_scenes['name']
            tree.append(v)
        return tree

    def print_scene_tree(self):
        tree = []
        for child in self.get_scene_tree():
            if isinstance(child, tuple):
                s = '{name}({type})={value}'.format(type='Sequence', value=child[1], name=child[0])
            else:
                s = '{type}={name}'.format(type='scene', name=child)
            tree.append(s)
        print(tree)
        # for value in tree:
        #     print(value)


if __name__ == '__main__':
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
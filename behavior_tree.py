# -*- coding: utf-8 -*-
from inspect import isfunction
from core.utils.base import get_varible_name
import time
import sys


def none_fun(*args):
    pass


class Blackboard(object):
    def __init__(self):
        self.__tag = 'Blackboard'
        self.con = {}

    def set_value(self, Member, Value):
        self.con[Member] = Value

    def get_value(self, Member, DefaultValue=None):
        return self.con.get(Member, DefaultValue)

    def set_value_bath(self, Value: dict):
        self.con.update(Value)

    def get_value_all(self, Target=None):
        Target = Target or self
        return Target.con

    def create_scene(self):
        return Scene(self)

    def create_sequence(self):
        return Sequence(self)


class Scene(object):
    """创建场景"""

    def __init__(self, blackboard):
        self.__tag = 'Scene'
        self.child = none_fun
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
            self.child = sequence
        else:
            raise ValueError('value is not Sequence please check')

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
            if isinstance(self.child, Sequence):
                self.child.run()
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
        self.loopEndTrigger = Trigger(blackboard)
        self.scenes_tree = []

    def add_scene(self, *args):
        for scene in args:
            if isinstance(scene, Scene):
                self.scenes_tree.append(dict(name=get_varible_name(scene), scene=scene))
                self.scenes.append(scene)
            else:
                raise ValueError('{} is not Scene, tuple index={}'.format(scene, args.index(scene)))

    def get_loopEndTrigger(self):
        return self.loopEndTrigger

    def setLoop(self, isLoop, LoopCount=-1, LoopTime=-1, IntervalTime=0):
        """
            设置场景检测的循环方式
            参数:	isLoop		Bool型,是否循环
                    LoopCount 	循环次数
                    LoopTime 	循环最长时间
                    IntervalTime每次循环的间隔(毫秒)
        """
        self.isLoop = isLoop
        self.maxCount = LoopCount
        self.maxTime = LoopTime
        self.loopIntervalTime = IntervalTime

    def run(self):
        flag = False
        loopTime = time.time()
        loopCount = 1
        while True:
            if flag:
                loopTime = time.time()
                loopCount = 0
            for v in self.scenes:
                flag = v.run()
                if flag:
                    break
            if self.loopEndTrigger.check():
                break
            loopCount += 1
            if self.loopIntervalTime > 0:
                time.sleep(self.loopIntervalTime)
            # 退出条件
            if (not flag and not self.isLoop) or ((self.isLoop and not flag) and (
                    not self.maxTime == -1 and (loopTime + self.maxTime < time.time()) or False) or (
                                                          not self.maxCount == -1 and (
                                                          loopCount > self.maxCount) or False)):
                return

    def get_scene_tree(self):
        """通过遍历Sequence 获取当前节点下的子节点信息"""
        tree = []
        for main_scenes in self.scenes_tree:
            v = None
            if isinstance(main_scenes['scene'].child, Sequence):
                v = main_scenes['scene'].child.get_scene_tree()
            else:
                v = main_scenes['name']
            tree.append(v)
        return tree
#! usr/bin/python
# -*- coding:utf-8 -*-
"""
坐标系转换---从原来叉叉助手框架转移过来的
包含了锚点模式,适用于各种分辨率,刘海屏的坐标适配
"""
from typing import Union
from loguru import logger
from pydantic import BaseModel


class display_type(BaseModel):
    """
        top, bottom为上下黑边, left和right为左右黑边, widht为宽, height为高
        width需要大于height
    """
    width: int
    height: int
    top = 0
    bottom = 0
    left = 0
    right = 0
    x = 0
    y = 0


class Point(object):
    """
        Point.ZERO      :一个x,y均为0的Point
        Point.INVALID   :一个x,y均为-1的Point
        Point(void) :构造一个x,y均为0的Point
        Point(x:int , y:int)    :根据x,y构造一个Point
        Point(Point)    :根据point,拷贝一个新的Point
        Point.x :x坐标
        Point.y :y坐标
        支持 +,-,*,/,==操作
    """
    def __init__(self, x: int, y: int,
                 anchor_mode: str = 'Middle', anchor_x: int = 0, anchor_y: int = 0):
        """
        构建一个点
        :param x: x轴坐标
        :param y: y轴坐标
        :param kwargs:
        """
        self.x = x
        self.y = y
        self.anchor_mode = anchor_mode
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y

    def __str__(self):
        return '<Point [{:.1f}, {:.1f}]>'.format(self.x, self.y)

    def __add__(self, other):
        if type(other) == Point:
            return Point(self.x + other.x, self.y + other.y)
        raise logger.error('目标对象不是Point类,请检查')

    def __sub__(self, other):
        if type(other) == Point:
            return Point(self.x - other.x, self.y - other.y)
        raise logger.error('目标对象不是Point类,请检查')

    def __mul__(self, other):
        if type(other) == int:
            return Point(self.x * other, self.y * other)
        raise logger.error('目标对象不是int类,请检查')

    def __truediv__(self, other):
        if type(other) == int:
            return Point(self.x / other, self.y / other)
        raise logger.error('目标对象不是int类,请检查')

    def __eq__(self, other):
        if type(other) == Point:
            return self.x == other.x and self.y == other.y
        else:
            logger.error('目标对象不是Point类,请检查')
            return False


Point.ZERO = Point(0, 0)
Point.INVALID = Point(-1, -1)


class Size(object):
    """
        Size.ZERO      :一个width,height均为0的Size
        Size.INVALID   :一个width,height均为-1的Size
        Size(void) :构造一个width,height均为0的Size
        Size(width:int , height:int)    :根据width,height构造一个Size
        Size(Size)    :根据Size,拷贝一个新的Size
        Size.width  :Size的宽
        Size.height :Size的高
        支持 +,-,*,/,==操作
    """
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

    def __str__(self):
        return '<Size [{} x {}]>'.format(self.width,self.height)

    def __add__(self, other):
        if type(other) == Size:
            return Size(self.width + other.width, self.height + other.height)
        raise logger.error('目标对象不是Size类,请检查')

    def __sub__(self, other):
        if type(other) == Size:
            return Size(self.width - other.width, self.height - other.height)
        raise logger.error('目标对象不是Size类,请检查')

    def __mul__(self, other):
        if type(other) == int:
            return Size(self.width * other, self.height * other)
        raise logger.error('目标对象不是int类,请检查')

    def __truediv__(self, other):
        if type(other) == int:
            return Size(self.width / other, self.height / other)
        raise logger.error('目标对象不是int类,请检查')

    def __eq__(self, other):
        if type(other) == Point:
            return self.width == other.width and self.height == other.height
        else:
            logger.error('目标对象不是Size类,请检查')
            return False

    def __lt__(self, other):
        if type(other) == Size:
            return self.width*self.height < other.width*other.height
        else:
            logger.error('目标对象不是Size类,请检查')
            return False

    def __gt__(self, other):
        if type(other) == Size:
            return self.width*self.height > other.width*other.height
        else:
            logger.error('目标对象不是Size类,请检查')
            return False

    def __le__(self, other):
        if type(other) == Size:
            return self.width*self.height <= other.width*other.height
        else:
            logger.error('目标对象不是Size类,请检查')
            return False

    def __ge__(self, other):
        if type(other) == Size:
            return self.width*self.height >= other.width*other.height
        else:
            logger.error('目标对象不是Size类,请检查')
            return False

Size.ZERO = Size(0, 0)
Size.INVALID = Size(-1, -1)


class Rect(object):
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __str__(self):
        return '<Rect [Point({}, {}), Size[{}, {}]]'.format(
            self.x, self.y, self.width, self.height)

    @property
    def size(self):
        return Size(self.width, self.height)

    @property
    def tl(self):
        """返回当前Rect的左上角Point坐标"""
        return Point(self.x, self.y)

    @property
    def br(self):
        """返回当前Rect的右下角Point坐标"""
        return Point(self.x+self.width, self.y+self.height)

    @property
    def middle(self):
        return Point(self.x+self.width/2, self.y+self.height/2)

    def contains(self, point: Point):
        """判断Point是否在当前Rect范围中"""
        if type(point) != Point:
            raise logger.error('目标对象不是Point类,请检查')
        tl, br = self.tl, self.br
        if tl.x <= point.x <= br.x and tl.y <= point.y <= br.y:
            return True
        return False


Rect.ZERO = Rect(0, 0, 0, 0)


class Anchor_transform(object):
    @staticmethod
    def Middle(x, y, dev, cur, mainPoint_scale):
        x = cur.x / 2 - ((dev.x / 2 - x) * mainPoint_scale['x']) + cur.left
        y = cur.y / 2 - ((dev.y / 2 - y) * mainPoint_scale['y']) + cur.top
        return x, y

    @staticmethod
    def Left(x, y, dev, cur, mainPoint_scale):
        x = x * mainPoint_scale['x'] + cur.left
        y = cur.y/2-((dev.y/2-y)*mainPoint_scale['y'])+cur.top
        return x, y

    @staticmethod
    def Right(x, y, dev, cur, mainPoint_scale):
        x = cur.x-((dev.x-x) * mainPoint_scale['x'])+cur.left
        y = cur.y/2-((dev.y/2-y) * mainPoint_scale['y'])+cur.top
        return x, y

    @staticmethod
    def top(x, y, dev, cur, mainPoint_scale):
        x = cur.x / 2 - ((dev.x / 2 - x) * mainPoint_scale['x']) + cur.left
        y = y * mainPoint_scale['y'] + cur.top
        return x, y

    @staticmethod
    def Bottom(x, y, dev, cur, mainPoint_scale):
        x = cur.x / 2 - ((dev.x / 2 - x) * mainPoint_scale['x']) + cur.left
        y = cur.y - ((dev.y - y) * mainPoint_scale['y']) + cur.top
        return x, y

    @staticmethod
    def Left_top(x, y, dev, cur, mainPoint_scale):
        x = x * mainPoint_scale['x'] + cur.left
        y = y * mainPoint_scale['y'] + cur.top
        return x, y

    @staticmethod
    def Left_bottom(x, y, dev, cur, mainPoint_scale):
        x = x * mainPoint_scale['x'] + cur.left
        y = cur.y - ((dev.y - y) * mainPoint_scale['y']) + cur.top
        return x, y

    @staticmethod
    def Right_top(x, y, dev, cur, mainPoint_scale):
        x = cur.x - ((dev.x - x) * mainPoint_scale['x']) + cur.left
        y = y * mainPoint_scale['y'] + cur.top
        return x, y

    @staticmethod
    def Right_bottom(x, y, dev, cur, mainPoint_scale):
        """锚点右下"""
        x = cur.x - ((dev.x-x)*mainPoint_scale['x']) + cur.left
        y = cur.y - ((dev.y-y)*mainPoint_scale['y']) + cur.top
        return x, y


class Anchor(object):
    def __init__(self, dev: dict, cur: dict, orientation: int):
        dev = display_type(**dev)
        cur = display_type(**cur)
        self.dev, self.cur = dev, cur

        if orientation == 1 or orientation == 2:
            dev_x = dev.width - dev.left - dev.right
            dev_y = dev.height - dev.top - dev.bottom
            cur_x = cur.width - cur.left - cur.right
            cur_y = cur.height - cur.top - cur.bottom
        elif orientation == 3:
            dev_x = dev.height - dev.top - dev.bottom
            dev_y = dev.width - dev.left - dev.right
            cur_x = cur.height - cur.top - cur.bottom
            cur_y = cur.width - cur.left - cur.right
        else:
            raise ValueError('没有定义orientation')
        dev.x, dev.y = dev_x, dev_y
        cur.x, cur.y = cur_x, cur_y

        scale_x = cur_x / dev_x
        scale_y = cur_y / dev_y
        # mainPoint_scale_mode x,y:'width','height'
        self.mainPoint_scale = {
            'x': scale_x,
            'y': scale_y,
        }
        #
        self.appurtenant_scale = {
            'x': scale_x,
            'y': scale_y,
        }

    def point(self, x: int, y: int, anchor_mode: str = 'Middle', anchor_x: int = 0, anchor_y: int = 0):
        point = Point(x=x, y=y, anchor_mode=anchor_mode, anchor_x=anchor_x, anchor_y=anchor_y)
        point.x, point.y = self.transform(point)
        return point

    def size(self, width: int, height: int):
        size = Size(width=width, height=height)
        size.width, size.height = self.transform(size)
        return size

    def transform(self, args: Union[Point, Size]):
        if isinstance(args, Point):
            # 计算锚点坐标
            anchor_x, anchor_y = self._count_anchor_point(args)
            # 计算从属点坐标
            x, y = self._count_appurtenant_point(args, anchor_x, anchor_y)
            return x, y
        elif isinstance(args, Size):
            width = args.width * self.mainPoint_scale['x']
            height = args.height * self.mainPoint_scale['y']
            return width, height
        else:
            raise ValueError('转换未知的类型: {}'.format(args))

    def _count_appurtenant_point(self, point, anchor_x, anchor_y):
        """计算锚点从属点坐标"""
        x = anchor_x + (point.x - point.anchor_x)*self.appurtenant_scale['x']
        y = anchor_y + (point.y - point.anchor_y)*self.appurtenant_scale['y']
        return x, y

    def _count_anchor_point(self, point):
        """计算锚点坐标"""
        anchor_fun = getattr(Anchor_transform, point.anchor_mode)
        x = point.anchor_x - self.dev.left
        y = point.anchor_y - self.dev.top
        x, y = anchor_fun(x, y, self.dev, self.cur, self.mainPoint_scale)
        return x, y

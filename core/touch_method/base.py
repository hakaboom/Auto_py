# -*- coding: utf-8 -*-
class transform(object):
    def __init__(self, display_info):
        self.display_info = display_info
        self.event_size = dict(width=display_info['max_x'], height=display_info['max_y'])
        self.screen_size = dict(width=display_info['width'], height=display_info['height'])
        self.event_scale = self.event2windows()

    def event2windows(self):
        return {
            'width': self.screen_size['width'] / self.event_size['width'],
            'height': self.screen_size['height'] / self.event_size['height']
        }

    def transform(self, x, y):
        if self.display_info['orientation'] == 0:
            return self.right2right(x, y)
        elif self.display_info['orientation'] == 1:
            return self.left2right(x, y)
        elif self.display_info['orientation'] == 2:
            return self.portrait2right(x, y)

    def right2right(self, x, y):
        return round(x / self.event_scale['width']), round(y / self.event_scale['width'])

    def portrait2right(self, x, y):
        return round((x / self.screen_size['height'] * self.screen_size['width']) / self.event_scale['width']), \
               round((y / self.screen_size['width'] * self.screen_size['height'] / self.event_scale['height']))

    def left2right(self, x, y):
        return round((1 - x / self.screen_size['height']) * self.screen_size['width'] / self.event_scale['height']), \
               round((1 - y / self.screen_size['width']) * self.screen_size['height'] / self.event_scale['height'])
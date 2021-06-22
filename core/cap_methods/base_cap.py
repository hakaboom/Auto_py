# -*- coding: utf-8 -*-


class BaseCap(object):
    def __init__(self, adb, *args, **kwargs):
        self.adb = adb

    def get_frame_from_stream(self):
        pass

    def get_frame(self):
        pass

    def teardown(self):
        pass

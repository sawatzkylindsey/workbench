#!/usr/bin/python
# -*- coding: utf-8 -*-


class NotFound(Exception):
    def __init__(self, msg, origin=None):
        self.msg = msg
        self.origin = origin

    def __repr__(self):
        return "NotFound: %s" % self.msg


class Invalid(Exception):
    def __init__(self, msg, origin=None):
        self.msg = msg
        self.origin = origin

    def __repr__(self):
        return "Invalid: %s" % self.msg


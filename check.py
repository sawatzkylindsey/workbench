#!/usr/bin/python
# -*- coding: utf-8 -*-


def checkNotNone(value):
    if value is None:
        raise ValueError("value '%s' is unexpectedly None" % value)

    return value


def checkNotEmpty(value):
    if len(value) == 0:
        raise ValueError("value '%s' is unexpectedly empty" % value)

    if isinstance(value, str) and len(value.lstrip()) == 0:
        raise ValueError("value '%s' is unexpectedly only whitespace" % value)

    return value


def checkNotContains(value, substr):
    if substr in value:
        raise ValueError("value '%s' unexpectedly contains '%s'" % (value, susbstr))

    return value


def checkNotInstance(value, instance):
    if isinstance(value, instance):
        raise ValueError("value '%s' is unexpectedly an instance '%s'" % (value, instance))

    return value


def checkInstance(value, instance):
    if not isinstance(value, instance):
        raise ValueError("value '%s' is unexpectedly not an instance '%s'" % (value, instance))

    return value


def checkNotEqual(value, other):
    if value == other:
        raise ValueError("value '%s' is unexpectedly equal to '%s'" % (value, other))

    return value


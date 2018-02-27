#!/usr/bin/python
# -*- coding: utf-8 -*-


def check_not_none(value):
    if value is None:
        raise ValueError("value is unexpectedly None")

    return value


def check_none(value):
    if value is not None:
        raise ValueError("value '%s' is unexpectedly not None" % value)

    return value


def check_not_empty(value):
    if len(value) == 0:
        raise ValueError("value '%s' is unexpectedly empty" % value)

    if isinstance(value, str) and len(value.lstrip()) == 0:
        raise ValueError("value '%s' is unexpectedly only whitespace" % value)

    return value


def check_not_contains(value, substr):
    if substr in value:
        raise ValueError("value '%s' unexpectedly contains '%s'" % (value, susbstr))

    return value


def check_not_instance(value, instance):
    if isinstance(value, instance):
        raise ValueError("value '%s' is unexpectedly an instance '%s'" % (value, instance))

    return value


def check_instance(value, instance):
    if not isinstance(value, instance):
        raise ValueError("value '%s' is unexpectedly not an instance '%s'" % (value, instance))

    return value


def check_not_equal(value, other):
    if value == other:
        raise ValueError("value '%s' is unexpectedly equal to '%s'" % (value, other))

    return value

def check_equal(value, other):
    if value != other:
        raise ValueError("value '%s' is unexpectedly not equal to '%s'" % (value, other))

    return value


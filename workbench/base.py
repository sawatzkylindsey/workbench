#!/usr/bin/python
# -*- coding: utf-8 -*-

import operator


class Base(object):
    def __init__(self, *args, **kwargs):
        super(Base, self).__init__(*args, **kwargs)

    def __repr__(self):
        return str(self)


class Comparable(Base):
    def __init__(self, *args, **kwargs):
        super(Comparable, self).__init__(*args, **kwargs)

    def _comparator(self, fn, other):
        raise NotImplementedError("%s:_comparator" % self.__class__.name)

    def __lt__(self, other):
        return self._comparator(operator.lt, other)

    def __le__(self, other):
        return self._comparator(operator.le, other)

    def __gt__(self, other):
        return self._comparator(operator.gt, other)

    def __ge__(self, other):
        return self._comparator(operator.ge, other)


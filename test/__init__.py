#!/usr/bin/python
# -*- coding: utf-8 -*-

from pytils.invigilator import create_suite


from workbench.test import graph, nlp


def all():
    return create_suite(unit())


def unit():
    return [
        graph.tests(),
        nlp.tests()
    ]


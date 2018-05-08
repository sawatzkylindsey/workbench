#!/usr/bin/python
# -*- coding: utf-8 -*-

from pytils.invigilator import create_suite


from test import graph, nlp, parser, processor


def all():
    return create_suite(unit())


def unit():
    return [
        graph.tests(),
        nlp.tests(),
        parser.tests(),
        processor.tests(),
    ]


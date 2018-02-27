#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import os
from pytils.invigilator import create_suite
from unittest import TestCase


from workbench.nlp import extract_terms, SPLITTER
from workbench.nlp import Term


logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().setLevel(logging.DEBUG)
root_handler = logging.FileHandler("%s.test.log" % os.path.splitext(os.path.basename(__file__))[0])
root_handler.setFormatter(logging.Formatter("%(levelname)s %(module)s..%(funcName)s: %(message)s"))
logging.getLogger().addHandler(root_handler)


class Tests(TestCase):
    def test_extract_terms(self):
        corpus1 = "once there was a little man, a little wooden man"
        corpus2 = "once there was a man, a little wooden man"
        corpus3 = "once there was a little man, a wooden man"
        little = Term(["little"])
        little_man = Term(["little", "man"])
        terms = set([little, little_man])
        self.assertEqual(extract_terms(SPLITTER(corpus1), terms), set([little, little_man]))
        self.assertEqual(extract_terms(SPLITTER(corpus2), terms), set([little]))
        self.assertEqual(extract_terms(SPLITTER(corpus3), terms), set([little_man]))

    def test_extract_terms_overlap(self):
        corpus = "once there was a little man"
        once_there = Term(["once", "there"])
        there_was = Term(["there", "was"])
        was_a = Term(["was", "a"])
        terms = set([once_there, there_was, was_a])
        self.assertEqual(extract_terms(SPLITTER(corpus), terms), set([once_there, was_a]))

    def test_extract_terms_end(self):
        corpus = "once there was a little man"
        man = Term(["man"])
        little_man = Term(["little", "man"])
        self.assertEqual(extract_terms(SPLITTER(corpus), set([man])), set([man]))
        self.assertEqual(extract_terms(SPLITTER(corpus), set([little_man])), set([little_man]))


def tests():
    return create_suite(Tests)


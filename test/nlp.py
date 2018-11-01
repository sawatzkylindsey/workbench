#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import os
from pytils.invigilator import create_suite
from unittest import TestCase


from workbench.nlp import extract_terms, split_words, split_sentences, stem
from workbench.nlp import Term
from workbench.trie import build as build_trie


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
        corpus4 = "little <= man"
        corpus5 = "little > man"
        little = Term(["little"])
        little_man = Term(["little", "man"])
        terms = set([little, little_man])
        terms_trie = build_trie(terms)
        self.assertEqual(extract_terms(split_words(corpus1), terms_trie), set([little, little_man]))
        self.assertEqual(extract_terms(split_words(corpus2), terms_trie), set([little]))
        self.assertEqual(extract_terms(split_words(corpus3), terms_trie), set([little_man]))
        self.assertEqual(extract_terms(split_words(corpus4), terms_trie), set([little]))
        self.assertEqual(extract_terms(split_words(corpus5), terms_trie), set([little_man]))

    def test_extract_terms_overlap(self):
        corpus = "once there was a little man"
        once_there = Term(["once", "there"])
        there_was = Term(["there", "was"])
        was_a = Term(["was", "a"])
        terms = set([once_there, there_was, was_a])
        terms_trie = build_trie(terms)
        self.assertEqual(extract_terms(split_words(corpus), terms_trie), set([once_there, was_a]))

    def test_extract_terms_end(self):
        corpus = "once there was a little man"
        man = Term(["man"])
        man_trie = build_trie([man])
        little_man = Term(["little", "man"])
        little_man_trie = build_trie([little_man])
        self.assertEqual(extract_terms(split_words(corpus), man_trie), set([man]))
        self.assertEqual(extract_terms(split_words(corpus), little_man_trie), set([little_man]))

    def test_split_sentences(self):
        self.assertEqual(split_sentences("once there was a little man"),
            [["once", "there", "was", "a", "little", "man"]])
        self.assertEqual(split_sentences("once there was. a little man"),
            [["once", "there", "was"], ["a", "little", "man"]])
        self.assertEqual(split_sentences("once there was? a little man"),
            [["once", "there", "was"], ["a", "little", "man"]])
        self.assertEqual(split_sentences("once there was! a little man"),
            [["once", "there", "was"], ["a", "little", "man"]])
        self.assertEqual(split_sentences("once there was!\n\n\na little man"),
            [["once", "there", "was"], ["a", "little", "man"]])
        self.assertEqual(split_sentences("once there was. a\n\nlittle man"),
            [["once", "there", "was"], ["a", "little", "man"]])
        self.assertEqual(split_sentences("once there was.  a little man."),
            [["once", "there", "was"], ["a", "little", "man"]])

        self.assertEqual(split_sentences("once there was a little man", True),
            [["once", "there", "was", "a", "little", "man"]])
        self.assertEqual(split_sentences("once there was. a little man", True),
            [["once", "there", "was", "a", "little", "man"]])
        self.assertEqual(split_sentences("once there was? a little man", True),
            [["once", "there", "was", "a", "little", "man"]])
        self.assertEqual(split_sentences("once there was! a little man", True),
            [["once", "there", "was", "a", "little", "man"]])
        self.assertEqual(split_sentences("once there was!\n\n\na little man", True),
            [["once", "there", "was"], ["a", "little", "man"]])
        self.assertEqual(split_sentences("once there was. a\n\nlittle man", True),
            [["once", "there", "was", "a"], ["little", "man"]])
        self.assertEqual(split_sentences("once there was. a  \n\n  little man", True),
            [["once", "there", "was", "a"], ["little", "man"]])

    def test_term(self):
        a = Term(["fox", "dog"])
        b = Term(["Fox", "dOG"])
        self.assertEqual(a, a)
        self.assertEqual(hash(a), hash(a))
        self.assertNotEqual(a, b)
        self.assertNotEqual(hash(a), hash(b))

        self.assertEqual(b.lower(), a)
        self.assertEqual(hash(b.lower()), hash(a))


def tests():
    return create_suite(Tests)


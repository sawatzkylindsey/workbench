#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import os
from pytils.invigilator import create_suite
from unittest import TestCase


from workbench.nlp import Term
from workbench.trie import Node, build as build_trie


logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().setLevel(logging.DEBUG)
root_handler = logging.FileHandler("%s.test.log" % os.path.splitext(os.path.basename(__file__))[0])
root_handler.setFormatter(logging.Formatter("%(levelname)s %(module)s..%(funcName)s: %(message)s"))
logging.getLogger().addHandler(root_handler)


class Tests(TestCase):
    def test_node_empty_nonterminal(self):
        node = Node({}, False)
        self.assertEqual(node, Node({}, False))
        self.assertNotEqual(node, Node({}, True))

    def test_node_empty(self):
        node = Node({}, True)
        self.assertEqual(node, Node({}, True))
        self.assertNotEqual(node, Node({}, False))

    def test_node_nonterminal(self):
        child = Node({}, True)
        child_x = Node({}, False)
        node = Node({"child": child}, False)
        self.assertEqual(node, Node({"child": child}, False))
        self.assertNotEqual(node, Node({"other": child}, False))
        self.assertNotEqual(node, Node({"child": child_x}, False))

    def test_node(self):
        child = Node({}, True)
        child_x = Node({}, False)
        node = Node({"child": child}, True)
        self.assertEqual(node, Node({"child": child}, True))
        self.assertNotEqual(node, Node({"other": child}, True))
        self.assertNotEqual(node, Node({"child": child_x}, True))


def tests():
    return create_suite(Tests)


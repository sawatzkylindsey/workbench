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
        self.assertNotEqual(node, Node({}, True, Term(["root"])))

    def test_node_empty(self):
        node = Node({}, True, Term(["root"]))
        self.assertEqual(node, Node({}, True, Term(["root"])))
        self.assertNotEqual(node, Node({}, False))

    def test_node_nonterminal(self):
        child = Node({}, True, Term(["root"]))
        child_x = Node({}, False)
        node = Node({"child": child}, False)
        self.assertEqual(node, Node({"child": child}, False))
        self.assertNotEqual(node, Node({"other": child}, False))
        self.assertNotEqual(node, Node({"child": child_x}, False))

    def test_node(self):
        child = Node({}, True, Term(["child"]))
        child_x = Node({}, False)
        node = Node({"child": child})
        self.assertEqual(node, Node({"child": child}))
        self.assertNotEqual(node, Node({"other": child}))
        self.assertNotEqual(node, Node({"child": child_x}))

    def test_equivalence1(self):
        child_a = Node({}, True, Term(["child"]))
        child_b = Node({}, True, Term(["child"]))
        node = Node({"child_a": child_a, "child_b": child_b})
        self.assertEqual(len(node.children), 2)
        self.assertEqual(len(node.children["child_a"].children), 0)
        self.assertEqual(len(node.children["child_b"].children), 0)

    def test_equivalence2(self):
        child_a = Node({}, True, Term(["child"]))
        child_c = Node({}, True, Term(["child"]))
        child_b = Node({"child_c": child_c})
        node = Node({"child_a": child_a, "child_b": child_b})
        self.assertEqual(len(node.children), 2)
        self.assertEqual(len(node.children["child_a"].children), 0)
        self.assertEqual(len(node.children["child_b"].children), 1)
        self.assertEqual(len(node.children["child_b"].children["child_c"].children), 0)


def tests():
    return create_suite(Tests)


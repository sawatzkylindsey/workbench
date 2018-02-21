#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import os
from pytils.invigilator import create_suite
from unittest import TestCase


from workbench.graph import DirectedLink, UndirectedLink
from workbench.graph import Graph, GraphBuilder, Node


logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().setLevel(logging.DEBUG)
root_handler = logging.FileHandler("%s.test.log" % os.path.splitext(os.path.basename(__file__))[0])
root_handler.setFormatter(logging.Formatter("%(levelname)s %(module)s..%(funcName)s: %(message)s"))
logging.getLogger().addHandler(root_handler)


class Tests(TestCase):
    def test_node(self):
        a = Node("a")
        b = Node("b")
        self.assertEqual(a.descendants, set())
        self.assertEqual(b.descendants, set())

        a.add_descendant(b)
        self.assertEqual(a.descendants, set([b]))
        self.assertEqual(b.descendants, set())

        b.add_descendant(a)
        self.assertEqual(a.descendants, set([b]))
        self.assertEqual(b.descendants, set([a]))

    def test_graph(self):
        a = Node("a")
        b = Node("b")
        a.add_descendant(b)
        graph = Graph([a.finalize(), b.finalize()])
        self.assertEqual(graph._links(Graph.DIRECTED), set([DirectedLink("a", "b")]))
        self.assertEqual(graph._links(Graph.UNDIRECTED), set([UndirectedLink("a", "b")]))

    def test_graph_builder_undirected(self):
        gb = GraphBuilder(Graph.UNDIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["colt"]) \
            .add("jack", ["colt"]) \
            .build()
        self.assertEqual(graph.links(), set([UndirectedLink("bobo", "jack"), UndirectedLink("bobo", "jill"), \
            UndirectedLink("bobo", "jane"), UndirectedLink("jack", "colt")]))

    def test_graph_builder_directed(self):
        gb = GraphBuilder(Graph.DIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["colt"]) \
            .add("jack", ["colt"]) \
            .add("jane", ["bobo"]) \
            .build()
        self.assertEqual(graph.links(), set([DirectedLink("bobo", "jack"), DirectedLink("bobo", "jill"), \
            DirectedLink("bobo", "jane"), DirectedLink("jack", "colt"), DirectedLink("jane", "bobo")]))

    def test_neighbourhood_directed(self):
        gb = GraphBuilder(Graph.DIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["colt"]) \
            .add("alik", ["jill"]) \
            .add("jill", ["stew"]) \
            .add("stew", ["alik"]) \
            .add("jane", ["bobo"]) \
            .build()
        self.assertEqual(graph.neighbourhood("bobo", 0, inclusive=False), set())
        self.assertEqual(graph.neighbourhood("bobo", 1, inclusive=False), graph.nodes(["jack", "jill", "jane"]))
        self.assertEqual(graph.neighbourhood("bobo", 2, inclusive=False), graph.nodes(["bobo", "jack", "jill", "jane", "colt", "stew"]))
        self.assertEqual(graph.neighbourhood("bobo", 3, inclusive=False), graph.nodes(["bobo", "jack", "jill", "jane", "colt", "stew", "alik"]))
        self.assertEqual(graph.neighbourhood("bobo", 4, inclusive=False), graph.nodes(["bobo", "jack", "jill", "jane", "colt", "stew", "alik"]))
        self.assertEqual(graph.neighbourhood("bobo", None, inclusive=False), graph.nodes(["bobo", "jack", "jill", "jane", "colt", "stew", "alik"]))

        self.assertEqual(graph.neighbourhood("bobo", 0, inclusive=True), graph.nodes(["bobo"]))
        self.assertEqual(graph.neighbourhood("bobo", 1, inclusive=True), graph.nodes(["bobo", "jack", "jill", "jane"]))
        self.assertEqual(graph.neighbourhood("bobo", 2, inclusive=True), graph.nodes(["bobo", "jack", "jill", "jane", "colt", "stew"]))
        self.assertEqual(graph.neighbourhood("bobo", 3, inclusive=True), graph.nodes(["bobo", "jack", "jill", "jane", "colt", "stew", "alik"]))
        self.assertEqual(graph.neighbourhood("bobo", 4, inclusive=True), graph.nodes(["bobo", "jack", "jill", "jane", "colt", "stew", "alik"]))
        self.assertEqual(graph.neighbourhood("bobo", None, inclusive=True), graph.nodes(["bobo", "jack", "jill", "jane", "colt", "stew", "alik"]))

        self.assertEqual(graph.neighbourhood("colt", None, inclusive=False), set())
        self.assertEqual(graph.neighbourhood("colt", None, inclusive=True), graph.nodes(["colt"]))

        self.assertEqual(graph.neighbourhood("jack", None, inclusive=False), graph.nodes(["colt"]))
        self.assertEqual(graph.neighbourhood("jack", None, inclusive=True), graph.nodes(["colt", "jack"]))

    def test_neighbourhood_undirected(self):
        gb = GraphBuilder(Graph.UNDIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["colt"]) \
            .add("jill", ["alik", "stew"]) \
            .add("colt", ["stew"]) \
            .build()
        self.assertEqual(graph.neighbourhood("bobo", 0, inclusive=False), set())
        self.assertEqual(graph.neighbourhood("bobo", 1, inclusive=False), graph.nodes(["jack", "jill", "jane"]))
        self.assertEqual(graph.neighbourhood("bobo", 2, inclusive=False), graph.nodes(["bobo", "jack", "jill", "jane", "alik", "colt", "stew"]))
        self.assertEqual(graph.neighbourhood("bobo", 3, inclusive=False), graph.nodes(["bobo", "jack", "jill", "jane", "alik", "colt", "stew"]))
        self.assertEqual(graph.neighbourhood("bobo", None, inclusive=False), graph.nodes(["bobo", "jack", "jill", "jane", "alik", "colt", "stew"]))

        self.assertEqual(graph.neighbourhood("bobo", 0, inclusive=True), graph.nodes(["bobo"]))
        self.assertEqual(graph.neighbourhood("bobo", 1, inclusive=True), graph.nodes(["bobo", "jack", "jill", "jane"]))
        self.assertEqual(graph.neighbourhood("bobo", 2, inclusive=True), graph.nodes(["bobo", "jack", "jill", "jane", "alik", "colt", "stew"]))
        self.assertEqual(graph.neighbourhood("bobo", 3, inclusive=True), graph.nodes(["bobo", "jack", "jill", "jane", "alik", "colt", "stew"]))
        self.assertEqual(graph.neighbourhood("bobo", None, inclusive=True), graph.nodes(["bobo", "jack", "jill", "jane", "alik", "colt", "stew"]))

    def test_cc_none_undirected(self):
        gb = GraphBuilder(Graph.UNDIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .build()
        self.assertEqual(graph.clustering_coefficients["bobo"], 0.0)
        self.assertEqual(graph.clustering_coefficients["jack"], 0.0)
        self.assertEqual(graph.clustering_coefficients["jill"], 0.0)
        self.assertEqual(graph.clustering_coefficients["jane"], 0.0)

    def test_cc_one_undirected(self):
        gb = GraphBuilder(Graph.UNDIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["jill"]) \
            .build()
        self.assertEqual(graph.clustering_coefficients["bobo"], 1 / 3.0)
        self.assertEqual(graph.clustering_coefficients["jack"], 1.0)
        self.assertEqual(graph.clustering_coefficients["jill"], 1.0)
        self.assertEqual(graph.clustering_coefficients["jane"], 0.0)

    def test_cc_two_undirected(self):
        gb = GraphBuilder(Graph.UNDIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["jill", "jane"]) \
            .build()
        self.assertEqual(graph.clustering_coefficients["bobo"], 2 / 3.0)
        self.assertEqual(graph.clustering_coefficients["jack"], 2 / 3.0)
        self.assertEqual(graph.clustering_coefficients["jill"], 1.0)
        self.assertEqual(graph.clustering_coefficients["jane"], 1.0)

    def test_cc_three_undirected(self):
        gb = GraphBuilder(Graph.UNDIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["jill", "jane"]) \
            .add("jane", ["jill"]) \
            .build()
        self.assertEqual(graph.clustering_coefficients["bobo"], 1.0)
        self.assertEqual(graph.clustering_coefficients["jack"], 1.0)
        self.assertEqual(graph.clustering_coefficients["jill"], 1.0)
        self.assertEqual(graph.clustering_coefficients["jane"], 1.0)

    def test_cc_none_directed(self):
        gb = GraphBuilder(Graph.DIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .build()
        self.assertEqual(graph.clustering_coefficients["bobo"], 0.0)
        self.assertEqual(graph.clustering_coefficients["jack"], 0.0)
        self.assertEqual(graph.clustering_coefficients["jill"], 0.0)
        self.assertEqual(graph.clustering_coefficients["jane"], 0.0)

    def test_cc_one_directed(self):
        gb = GraphBuilder(Graph.DIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["jill"]) \
            .build()
        self.assertEqual(graph.clustering_coefficients["bobo"], 1 / 6.0)
        self.assertEqual(graph.clustering_coefficients["jack"], 0.0)
        self.assertEqual(graph.clustering_coefficients["jill"], 0.0)
        self.assertEqual(graph.clustering_coefficients["jane"], 0.0)

    def test_cc_two_directed(self):
        gb = GraphBuilder(Graph.DIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["jill", "jane"]) \
            .build()
        self.assertEqual(graph.clustering_coefficients["bobo"], 2 / 6.0)
        self.assertEqual(graph.clustering_coefficients["jack"], 0.0)
        self.assertEqual(graph.clustering_coefficients["jill"], 0.0)
        self.assertEqual(graph.clustering_coefficients["jane"], 0.0)

    def test_cc_three_directed(self):
        gb = GraphBuilder(Graph.DIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["jill", "jane"]) \
            .add("jane", ["jill"]) \
            .build()
        self.assertEqual(graph.clustering_coefficients["bobo"], 3 / 6.0)
        self.assertEqual(graph.clustering_coefficients["jack"], 1 / 2.0)
        self.assertEqual(graph.clustering_coefficients["jill"], 0.0)
        self.assertEqual(graph.clustering_coefficients["jane"], 0.0)

    def test_cc_four_directed(self):
        gb = GraphBuilder(Graph.DIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["jill", "jane"]) \
            .add("jane", ["jill"]) \
            .add("jill", ["jack"]) \
            .build()
        self.assertEqual(graph.clustering_coefficients["bobo"], 4 / 6.0)
        self.assertEqual(graph.clustering_coefficients["jack"], 1 / 2.0)
        self.assertEqual(graph.clustering_coefficients["jill"], 0.0)
        self.assertEqual(graph.clustering_coefficients["jane"], 0.0)

    def test_cc_five_directed(self):
        gb = GraphBuilder(Graph.DIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["jill", "jane"]) \
            .add("jane", ["jill"]) \
            .add("jill", ["jack", "jane"]) \
            .build()
        self.assertEqual(graph.clustering_coefficients["bobo"], 5 / 6.0)
        self.assertEqual(graph.clustering_coefficients["jack"], 1.0)
        self.assertEqual(graph.clustering_coefficients["jill"], 1 / 2.0)
        self.assertEqual(graph.clustering_coefficients["jane"], 0.0)

    def test_cc_six_directed(self):
        gb = GraphBuilder(Graph.DIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["jill", "jane"]) \
            .add("jane", ["jill", "jack"]) \
            .add("jill", ["jack", "jane"]) \
            .build()
        self.assertEqual(graph.clustering_coefficients["bobo"], 1.0)
        self.assertEqual(graph.clustering_coefficients["jack"], 1.0)
        self.assertEqual(graph.clustering_coefficients["jill"], 1.0)
        self.assertEqual(graph.clustering_coefficients["jane"], 1.0)

    def test_cc_seven_directed(self):
        gb = GraphBuilder(Graph.DIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["jill", "jane"]) \
            .add("jane", ["jill", "jack"]) \
            .add("jill", ["jack", "jane", "bobo"]) \
            .build()
        self.assertEqual(graph.clustering_coefficients["bobo"], 1.0)
        self.assertEqual(graph.clustering_coefficients["jack"], 1.0)
        self.assertEqual(graph.clustering_coefficients["jill"], 4 / 6.0)
        self.assertEqual(graph.clustering_coefficients["jane"], 1.0)


def tests():
    return create_suite(Tests)


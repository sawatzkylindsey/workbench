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
        self.assertEqual(a, a)
        self.assertEqual(hash(a), hash(a))
        self.assertNotEqual(a, b)
        self.assertNotEqual(hash(a), hash(b))

        self.assertFalse(a < a)
        self.assertLessEqual(a, a)
        self.assertFalse(a > a)
        self.assertGreaterEqual(a, a)

        self.assertLess(a, b)
        self.assertLessEqual(a, b)

        self.assertGreater(b, a)
        self.assertGreaterEqual(b, a)

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

        graph_d = Graph([a.finalize(), b.finalize()], Graph.DIRECTED)
        self.assertEqual(graph_d.links(), set([DirectedLink("a", "b")]))

        graph_ud = Graph([a.finalize(), b.finalize()], Graph.UNDIRECTED)
        self.assertEqual(graph_ud.links(), set([UndirectedLink("a", "b")]))

    def test_graph_empty(self):
        graph_d = Graph([], Graph.DIRECTED)
        self.assertEqual(graph_d.links(), set())
        self.assertEqual(graph_d.global_max_distance(), None)
        self.assertEqual(graph_d._max_distances, {})
        self.assertEqual(graph_d._distances, {})

        graph_ud = Graph([], Graph.UNDIRECTED)
        self.assertEqual(graph_ud.links(), set())
        self.assertEqual(graph_ud.global_max_distance(), None)
        self.assertEqual(graph_ud._max_distances, {})
        self.assertEqual(graph_ud._distances, {})

    def test_graph_single(self):
        bobo = Node("bobo")
        graph_d = Graph([bobo.finalize()], Graph.DIRECTED)
        self.assertEqual(graph_d.links(), set())
        self.assertEqual(graph_d.global_max_distance(), 0)
        self.assertEqual(graph_d._max_distances, {
            "bobo": 0
        })
        self.assertEqual(graph_d._distances, {
            "bobo": {
                "bobo": 0
            }
        })

        graph_ud = Graph([bobo.finalize()], Graph.UNDIRECTED)
        self.assertEqual(graph_ud.links(), set())
        self.assertEqual(graph_ud.global_max_distance(), 0)
        self.assertEqual(graph_ud._max_distances, {
            "bobo": 0
        })
        self.assertEqual(graph_ud._distances, {
            "bobo": {
                "bobo": 0
            }
        })

    def test_graph_builder_undirected(self):
        gb = GraphBuilder(Graph.UNDIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["colt"]) \
            .add("jack", ["colt"]) \
            .add("alik", ["peny"]) \
            .build()
        self.assertEqual(graph.links(), set([UndirectedLink("bobo", "jack"), UndirectedLink("bobo", "jill"), \
            UndirectedLink("bobo", "jane"), UndirectedLink("jack", "colt"), UndirectedLink("alik", "peny")]))
        self.assertEqual(graph.global_max_distance(), 3)
        self.assertEqual(graph._max_distances, {
            "bobo": 2,
            "jack": 2,
            "jill": 3,
            "jane": 3,
            "colt": 3,
            "alik": 1,
            "peny": 1,
        })
        self.assertEqual(graph._distances, {
            "bobo": {
                "bobo": 0,
                "jack": 1,
                "jill": 1,
                "jane": 1,
                "colt": 2,
                "alik": None,
                "peny": None,
            },
            "jack": {
                "bobo": 1,
                "jack": 0,
                "jill": 2,
                "jane": 2,
                "colt": 1,
                "alik": None,
                "peny": None,
            },
            "jill": {
                "bobo": 1,
                "jack": 2,
                "jill": 0,
                "jane": 2,
                "colt": 3,
                "alik": None,
                "peny": None,
            },
            "jane": {
                "bobo": 1,
                "jack": 2,
                "jill": 2,
                "jane": 0,
                "colt": 3,
                "alik": None,
                "peny": None,
            },
            "colt": {
                "bobo": 2,
                "jack": 1,
                "jill": 3,
                "jane": 3,
                "colt": 0,
                "alik": None,
                "peny": None,
            },
            "alik": {
                "bobo": None,
                "jack": None,
                "jill": None,
                "jane": None,
                "colt": None,
                "alik": 0,
                "peny": 1,
            },
            "peny": {
                "bobo": None,
                "jack": None,
                "jill": None,
                "jane": None,
                "colt": None,
                "alik": 1,
                "peny": 0,
            },
        })

    def test_graph_builder_directed(self):
        gb = GraphBuilder(Graph.DIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["colt"]) \
            .add("jack", ["colt"]) \
            .add("jane", ["bobo"]) \
            .add("alik", ["peny"]) \
            .build()
        self.assertEqual(graph.links(), set([DirectedLink("bobo", "jack"), DirectedLink("bobo", "jill"), \
            DirectedLink("bobo", "jane"), DirectedLink("jack", "colt"), DirectedLink("jane", "bobo"), DirectedLink("alik", "peny")]))
        self.assertEqual(graph.global_max_distance(), 3)
        self.assertEqual(graph._max_distances, {
            "bobo": 2,
            "jack": 1,
            "jill": 0,
            "jane": 3,
            "colt": 0,
            "alik": 1,
            "peny": 0,
        })
        self.assertEqual(graph._distances, {
            "bobo": {
                "bobo": 0,
                "jack": 1,
                "jill": 1,
                "jane": 1,
                "colt": 2,
                "alik": None,
                "peny": None,
            },
            "jack": {
                "bobo": None,
                "jack": 0,
                "jill": None,
                "jane": None,
                "colt": 1,
                "alik": None,
                "peny": None,
            },
            "jill": {
                "bobo": None,
                "jack": None,
                "jill": 0,
                "jane": None,
                "colt": None,
                "alik": None,
                "peny": None,
            },
            "jane": {
                "bobo": 1,
                "jack": 2,
                "jill": 2,
                "jane": 0,
                "colt": 3,
                "alik": None,
                "peny": None,
            },
            "colt": {
                "bobo": None,
                "jack": None,
                "jill": None,
                "jane": None,
                "colt": 0,
                "alik": None,
                "peny": None,
            },
            "alik": {
                "bobo": None,
                "jack": None,
                "jill": None,
                "jane": None,
                "colt": None,
                "alik": 0,
                "peny": 1,
            },
            "peny": {
                "bobo": None,
                "jack": None,
                "jill": None,
                "jane": None,
                "colt": None,
                "alik": None,
                "peny": 0,
            },
        })

    def test_neighbourhood_directed(self):
        gb = GraphBuilder(Graph.DIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["colt"]) \
            .add("alik", ["jill"]) \
            .add("jill", ["stew"]) \
            .add("stew", ["alik"]) \
            .add("jane", ["bobo"]) \
            .add("peny", ["ruby"]) \
            .build()
        self.assertEqual(graph.neighbourhood("bobo", 0, False), set())
        self.assertEqual(graph.neighbourhood("bobo", 1, False), set([("jack", 1), ("jill", 1), ("jane", 1)]))
        self.assertEqual(graph.neighbourhood("bobo", 2, False), set([("jack", 1), ("jill", 1), ("jane", 1), ("colt", 2), ("stew", 2)]))
        self.assertEqual(graph.neighbourhood("bobo", 3, False), set([("jack", 1), ("jill", 1), ("jane", 1), ("colt", 2), ("stew", 2), ("alik", 3)]))
        self.assertEqual(graph.neighbourhood("bobo", 4, False), set([("jack", 1), ("jill", 1), ("jane", 1), ("colt", 2), ("stew", 2), ("alik", 3)]))
        self.assertEqual(graph.neighbourhood("bobo", None, False), set([("jack", 1), ("jill", 1), ("jane", 1), ("colt", 2), ("stew", 2), ("alik", 3)]))

        self.assertEqual(graph.neighbourhood("bobo", 0, True), set([("bobo", 0)]))
        self.assertEqual(graph.neighbourhood("bobo", 1, True), set([("bobo", 0), ("jack", 1), ("jill", 1), ("jane", 1)]))
        self.assertEqual(graph.neighbourhood("bobo", 2, True), set([("bobo", 0), ("jack", 1), ("jill", 1), ("jane", 1), ("colt", 2), ("stew", 2)]))
        self.assertEqual(graph.neighbourhood("bobo", 3, True), set([("bobo", 0), ("jack", 1), ("jill", 1), ("jane", 1), ("colt", 2), ("stew", 2), ("alik", 3)]))
        self.assertEqual(graph.neighbourhood("bobo", 4, True), set([("bobo", 0), ("jack", 1), ("jill", 1), ("jane", 1), ("colt", 2), ("stew", 2), ("alik", 3)]))
        self.assertEqual(graph.neighbourhood("bobo", None, True), set([("bobo", 0), ("jack", 1), ("jill", 1), ("jane", 1), ("colt", 2), ("stew", 2), ("alik", 3)]))

        self.assertEqual(graph.neighbourhood("colt", None, False), set())
        self.assertEqual(graph.neighbourhood("colt", None, True), set([("colt", 0)]))

        self.assertEqual(graph.neighbourhood("jack", None, False), set([("colt", 1)]))
        self.assertEqual(graph.neighbourhood("jack", None, True), set([("jack", 0), ("colt", 1)]))

    def test_neighbourhood_undirected(self):
        gb = GraphBuilder(Graph.UNDIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["colt"]) \
            .add("jill", ["alik", "stew"]) \
            .add("colt", ["stew"]) \
            .add("peny", ["ruby"]) \
            .build()
        self.assertEqual(graph.neighbourhood("bobo", 0, False), set())
        self.assertEqual(graph.neighbourhood("bobo", 1, False), set([("jack", 1), ("jill", 1), ("jane", 1)]))
        self.assertEqual(graph.neighbourhood("bobo", 2, False), set([("jack", 1), ("jill", 1), ("jane", 1), ("alik", 2), ("colt", 2), ("stew", 2)]))
        self.assertEqual(graph.neighbourhood("bobo", 3, False), set([("jack", 1), ("jill", 1), ("jane", 1), ("alik", 2), ("colt", 2), ("stew", 2)]))
        self.assertEqual(graph.neighbourhood("bobo", None, False), set([("jack", 1), ("jill", 1), ("jane", 1), ("alik", 2), ("colt", 2), ("stew", 2)]))

        self.assertEqual(graph.neighbourhood("bobo", 0, True), set([("bobo", 0)]))
        self.assertEqual(graph.neighbourhood("bobo", 1, True), set([("bobo", 0), ("jack", 1), ("jill", 1), ("jane", 1)]))
        self.assertEqual(graph.neighbourhood("bobo", 2, True), set([("bobo", 0), ("jack", 1), ("jill", 1), ("jane", 1), ("alik", 2), ("colt", 2), ("stew", 2)]))
        self.assertEqual(graph.neighbourhood("bobo", 3, True), set([("bobo", 0), ("jack", 1), ("jill", 1), ("jane", 1), ("alik", 2), ("colt", 2), ("stew", 2)]))
        self.assertEqual(graph.neighbourhood("bobo", None, True), set([("bobo", 0), ("jack", 1), ("jill", 1), ("jane", 1), ("alik", 2), ("colt", 2), ("stew", 2)]))


    def test_cc_none_undirected(self):
        gb = GraphBuilder(Graph.UNDIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .build()
        self.assertEqual(graph.clustering_coefficients["bobo"], 0.0)
        self.assertEqual(graph.clustering_coefficients["jack"], 0.0)
        self.assertEqual(graph.clustering_coefficients["jill"], 0.0)
        self.assertEqual(graph.clustering_coefficients["jane"], 0.0)
        # Testing clustering coefficient expansion
        self.assertEqual(graph.neighbourhood("bobo", 0, False), set())
        self.assertEqual(graph.neighbourhood("bobo", 0, False, (1, 1.0)), set([("jack", 1), ("jill", 1), ("jane", 1)]))
        self.assertEqual(graph.neighbourhood("jack", 0, False), set())
        self.assertEqual(graph.neighbourhood("jack", 0, False, (1, 1.0)), set([("bobo", 1)]))
        self.assertEqual(graph.neighbourhood("jill", 0, False), set())
        self.assertEqual(graph.neighbourhood("jill", 0, False, (1, 1.0)), set([("bobo", 1)]))
        self.assertEqual(graph.neighbourhood("jane", 0, False), set())
        self.assertEqual(graph.neighbourhood("jane", 0, False, (1, 1.0)), set([("bobo", 1)]))

    def test_cc_one_undirected(self):
        gb = GraphBuilder(Graph.UNDIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["jill"]) \
            .build()
        self.assertEqual(graph.clustering_coefficients["bobo"], 1 / 3.0)
        self.assertEqual(graph.clustering_coefficients["jack"], 1.0)
        self.assertEqual(graph.clustering_coefficients["jill"], 1.0)
        self.assertEqual(graph.clustering_coefficients["jane"], 0.0)
        # Testing clustering coefficient expansion
        self.assertEqual(graph.neighbourhood("bobo", 0, False), set())
        self.assertEqual(graph.neighbourhood("bobo", 0, False, (1, 0.34)), set([("jack", 1), ("jill", 1)]))
        self.assertEqual(graph.neighbourhood("bobo", 0, False, (1, 0.32)), set())
        self.assertEqual(graph.neighbourhood("jack", 0, False), set())
        self.assertEqual(graph.neighbourhood("jack", 0, False, (1, 1.0)), set([("jill", 1)]))
        self.assertEqual(graph.neighbourhood("jill", 0, False), set())
        self.assertEqual(graph.neighbourhood("jill", 0, False, (1, 1.0)), set([("jack", 1)]))
        self.assertEqual(graph.neighbourhood("jane", 0, False), set())
        self.assertEqual(graph.neighbourhood("jane", 0, False, (1, 1.0)), set([("bobo", 1)]))
        self.assertEqual(graph.neighbourhood("jane", 0, False, (1, 0.1)), set([("bobo", 1)]))

    def test_cc_two_undirected(self):
        gb = GraphBuilder(Graph.UNDIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["jill", "jane"]) \
            .build()
        self.assertEqual(graph.clustering_coefficients["bobo"], 2 / 3.0)
        self.assertEqual(graph.clustering_coefficients["jack"], 2 / 3.0)
        self.assertEqual(graph.clustering_coefficients["jill"], 1.0)
        self.assertEqual(graph.clustering_coefficients["jane"], 1.0)
        # Testing clustering coefficient expansion
        self.assertEqual(graph.neighbourhood("bobo", 0, False), set())
        self.assertEqual(graph.neighbourhood("bobo", 0, False, (1, 1.0)), set([("jill", 1), ("jane", 1), ("jack", 1)]))
        self.assertEqual(graph.neighbourhood("bobo", 0, False, (1, 0.67)), set([("jill", 1), ("jane", 1)]))
        self.assertEqual(graph.neighbourhood("bobo", 0, False, (1, 0.65)), set())
        self.assertEqual(graph.neighbourhood("jack", 0, False), set())
        self.assertEqual(graph.neighbourhood("jack", 0, False, (1, 1.0)), set([("jill", 1), ("jane", 1), ("bobo", 1)]))
        self.assertEqual(graph.neighbourhood("jack", 0, False, (1, 0.67)), set([("jill", 1), ("jane", 1)]))
        self.assertEqual(graph.neighbourhood("jack", 0, False, (1, 0.65)), set())
        self.assertEqual(graph.neighbourhood("jill", 0, False), set())
        self.assertEqual(graph.neighbourhood("jill", 0, False, (1, 1.0)), set())
        self.assertEqual(graph.neighbourhood("jane", 0, False), set())
        self.assertEqual(graph.neighbourhood("jane", 0, False, (1, 1.0)), set())

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
        # Testing clustering coefficient expansion
        self.assertEqual(graph.neighbourhood("bobo", 0, False), set())
        self.assertEqual(graph.neighbourhood("bobo", 0, False, (1, 1.0)), set([("jack", 1), ("jill", 1), ("jane", 1)]))
        self.assertEqual(graph.neighbourhood("jack", 0, False), set())
        self.assertEqual(graph.neighbourhood("jack", 0, False, (1, 1.0)), set())
        self.assertEqual(graph.neighbourhood("jill", 0, False), set())
        self.assertEqual(graph.neighbourhood("jill", 0, False, (1, 1.0)), set())
        self.assertEqual(graph.neighbourhood("jane", 0, False), set())
        self.assertEqual(graph.neighbourhood("jane", 0, False, (1, 1.0)), set())

    def test_cc_one_directed(self):
        gb = GraphBuilder(Graph.DIRECTED)
        graph = gb.add("bobo", ["jack", "jill", "jane"]) \
            .add("jack", ["jill"]) \
            .build()
        self.assertEqual(graph.clustering_coefficients["bobo"], 1 / 6.0)
        self.assertEqual(graph.clustering_coefficients["jack"], 0.0)
        self.assertEqual(graph.clustering_coefficients["jill"], 0.0)
        self.assertEqual(graph.clustering_coefficients["jane"], 0.0)
        # Testing clustering coefficient expansion
        self.assertEqual(graph.neighbourhood("bobo", 0, False), set())
        self.assertEqual(graph.neighbourhood("bobo", 0, False, (1, 1.0)), set())
        self.assertEqual(graph.neighbourhood("jack", 0, False), set())
        self.assertEqual(graph.neighbourhood("jack", 0, False, (1, 1.0)), set([("jill", 1)]))
        self.assertEqual(graph.neighbourhood("jill", 0, False), set())
        self.assertEqual(graph.neighbourhood("jill", 0, False, (1, 1.0)), set())
        self.assertEqual(graph.neighbourhood("jane", 0, False), set())
        self.assertEqual(graph.neighbourhood("jane", 0, False, (1, 1.0)), set())

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
        # Testing clustering coefficient expansion
        self.assertEqual(graph.neighbourhood("bobo", 0, False), set())
        self.assertEqual(graph.neighbourhood("bobo", 0, False, (1, 1.0)), set())
        self.assertEqual(graph.neighbourhood("jack", 0, False), set())
        self.assertEqual(graph.neighbourhood("jack", 0, False, (1, 1.0)), set())
        self.assertEqual(graph.neighbourhood("jill", 0, False), set())
        self.assertEqual(graph.neighbourhood("jill", 0, False, (1, 0.1)), set([("jack", 1)]))
        self.assertEqual(graph.neighbourhood("jane", 0, False), set())
        self.assertEqual(graph.neighbourhood("jane", 0, False, (1, 1.0)), set([("jill", 1)]))

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


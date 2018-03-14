#!/usr/bin/python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from collections import defaultdict
from csv import reader as csv_reader
import json
import itertools
import logging
import math
import numpy
import os
import pdb
import pickle
import sys
import threading


from frontend import d3node, d3link
from graph import GraphBuilder, Graph
from pytils.log import setup_logging, user_log
from parser import GlossaryCsv, LineText
import nlp


TOP = 10
BIAS_RELATED = 0.1


def main():
    parser = ArgumentParser(prog="termnet")
    parser.add_argument("--verbose", "-v",
                        default=False,
                        action="store_true",
                        # Unfortunately, logging in python 2.7 doesn't have
                        # a built-in way to log asynchronously.
                        help="Turn on verbose logging.  " + \
                        "**This will SIGNIFICANTLY slow down the program.**")
    parser.add_argument("-f", "--input-format", default=GLOSSARY_CSV, help="One of %s" % FORMATS)
    parser.add_argument("input_text")
    parser.add_argument("output_json")
    args = parser.parse_args()
    setup_logging(".%s.log" % os.path.splitext(os.path.basename(__file__))[0], args.verbose)
    logging.debug(args)

    cooccurrences = parse_cooccurrences(args.input_text, args.input_format).cooccurrences
    builder = GraphBuilder(Graph.UNDIRECTED)

    for k, v in sorted(cooccurrences.iteritems()):
        user_log.info("%s: %s" % (k, [str(i) for i in v]))
        builder.add(k, v)

    graph = builder.build()
    write_json(graph, args.output_json)
    return 0


class Termnet:
    LIMIT = 100

    def __init__(self, graph):
        self.graph = graph
        self.average = 1.0 / len(self.graph.all_nodes)
        self.rank = {n.identifier: self.average for n in self.graph.all_nodes}
        self.page_ranks = {}
        self._background_calculate_ranks = threading.Thread(target=self.calculate_ranks)
        self._background_calculate_ranks.daemon = True
        self._background_calculate_ranks.start()

    def calculate_ranks(self):
        for node in sorted(self.graph.all_nodes):
            user_log.info("page ranking: %s" % node.identifier.name())
            self.page_ranks[node.identifier] = self.graph.page_rank(biases={d.identifier: BIAS_RELATED for d in node.descendants})

    def _find(self, value, f, i, j):
        test_i = f(value, i)

        if test_i > value:
            assert f(value, j) < value
            upper = i
            lower = j
        else:
            assert f(value, j) > value
            upper = j
            lower = i

        midpoint = (lower + upper) / 2.0
        test = f(value, midpoint)
        logging.info("test: %s with %s" % (test, midpoint))

        while not self._within(test, value):
            if test > value:
                upper = midpoint
            else:
                lower = midpoint

            midpoint = (lower + upper) / 2.0
            test = f(value, midpoint)
            logging.info("test: %s with %s" % (test, midpoint))

        logging.info("found: %s" % midpoint)
        return lambda x: f(x, midpoint)

    def _within(self, value, expected, epsilon=0.0000001):
        return abs(expected - value) < epsilon

    def _find_softener(self, value):
        i = 1.0
        j = -1.0
        test = self._left_inverse_sigmoid(value)(value, i)

        while test < value:
            i = i * 2.0
            test = self._left_inverse_sigmoid(value)(value, i)

        while test > value:
            j = j * 2.0
            test = self._left_inverse_sigmoid(value)(value, j)

        logging.info("lis: %s, %s" % (i, j))
        lis = self._find(value, self._left_inverse_sigmoid(value), i, j)
        def lis_fixed(x):
            y = lis(x)
            return y if y > x else x

        m = 1.0
        n = -1.0
        test = self._right_inverse_sigmoid(value)(value, m)

        while test < value:
            m = m * 2.0
            test = self._right_inverse_sigmoid(value)(value, m)

        while test > value:
            n = n * 2.0
            test = self._right_inverse_sigmoid(value)(value, n)

        logging.info("ris: %s, %s" % (m, n))
        ris = self._find(value, self._right_inverse_sigmoid(value), m, n)
        def ris_fixed(x):
            y = ris(x)
            return y if y < x else x

        def s(v):
            if v <= value:
                scaled = lis_fixed(v)
            else:
                scaled = ris_fixed(v)

            logging.info("scaled: %s -> %s" % (v, scaled))
            return scaled

        return s

    def _left_inverse_sigmoid(self, value):
        assert value >= 0.0 and value <= 1.0
        return lambda x, d: ((numpy.log10((1.0 / (-x + (2.0 * value))) - (0.5 / value)) + (1.0 / value)) / (2.0 / value)) + d

    def _right_inverse_sigmoid(self, value):
        assert value >= 0.0 and value <= 1.0
        return lambda x, d: ((numpy.log10((1.0 / (-x + 1.0)) - (0.5 / (1.0 - value))) + (1.0 / value)) / (2.0 / value)) + d

    def _scaling_left_inverse_sigmoid(self, value):
        assert value >= 0.0 and value <= 1.0
        return lambda x, d: ((numpy.log10((1.0 / (-x + (2.0 * value))) - (0.5 / value)) + (0.75 / value)) / (1.5 / value)) + d

    def _find_smoother(self, value):
        i = 1.0
        j = -1.0
        test = self._scaling_left_inverse_sigmoid(value)(value, i)

        while test < value:
            i = i * 2.0
            test = self._scaling_left_inverse_sigmoid(value)(value, i)

        while test > value:
            j = j * 2.0
            test = self._scaling_left_inverse_sigmoid(value)(value, j)

        logging.info("lis: %s, %s" % (i, j))
        lis = self._find(value, self._scaling_left_inverse_sigmoid(value), i, j)
        def lis_fixed(x):
            y = lis(x)
            return y if y > x else x

        return lambda v: lis_fixed(v)

    def reset(self):
        self.rank = {n.identifier: self.average for n in self.graph.all_nodes}

    def mark(self, term):
        if term is None:
            node_ranks = {}

            for node in self.graph.all_nodes:
                assert self.rank[node.identifier] >= 0.0 and self.rank[node.identifier] <= 1.0
                node_ranks[node.identifier] = self.rank[node.identifier]

            sorted_node_ranks = sorted(node_ranks.iteritems(), key=lambda item: item[1], reverse=True)
            smoothing_point = int(math.ceil(len(node_ranks) * 0.1))
            smoother = self._find_softener(sum([item[1] for item in sorted_node_ranks[:smoothing_point]]) / smoothing_point)
            selected_nodes = [item[0] for item in sorted_node_ranks[:TOP]]
            return {
                "nodes": [d3node(self._name(node.identifier), smoother(self.rank[node.identifier]), 0.75, self._coeff(node.identifier)).__dict__ for node in self.graph.all_nodes],
                "links": [d3link(self._name(link.source), self._name(link.target), 0.75).__dict__ for link in self.graph.links()]
            }

        for k, v in self.page_ranks[term].iteritems():
            assert v >= 0.0 and v <= 1.0, v
            self.rank[k] += v

        total = sum(self.rank.values())
        scale = 1.0 / total
        assert scale >= 0.0
        self.rank = {k: scale * v for k, v in self.rank.iteritems()}
        node_ranks = {
            term: self.rank[term]
        }
        sum_subgraph = self.rank[term]

        for node in self.graph.neighbourhood(term, 1):
            assert self.rank[node.identifier] >= 0.0 and self.rank[node.identifier] <= 1.0
            node_ranks[node.identifier] = self.rank[node.identifier]
            sum_subgraph += self.rank[node.identifier]

        logging.debug(node_ranks)
        sorted_node_ranks = sorted(node_ranks.iteritems(), key=lambda item: item[1], reverse=True)
        logging.info("%s: %s" % (sum_subgraph, sorted_node_ranks))
        smoothing_point = int(math.ceil(len(node_ranks) * 0.1))
        smoother = self._find_softener(sum([item[1] for item in sorted_node_ranks[:smoothing_point]]) / smoothing_point)
        selected_nodes = [item[0] for item in sorted_node_ranks[:TOP]]
        neighbour_nodes = [item[0] for item in sorted_node_ranks[TOP:]]
        selected_links = []
        neighbour_links = []

        for link in self.graph.links():
            if link.source in selected_nodes and link.target in selected_nodes:
                selected_links += [link]
            elif (link.source in selected_nodes and link.target in neighbour_nodes) \
                or (link.source in neighbour_nodes and link.target in selected_nodes) \
                or (link.source in neighbour_nodes and link.target in neighbour_nodes):
                neighbour_links += [link]

        return {
            "nodes": [d3node(self._name(identifier), smoother(node_ranks[identifier]), 1.0, self._coeff(identifier)).__dict__ for identifier in selected_nodes] \
                + [d3node(self._name(identifier), smoother(node_ranks[identifier]), 0.15, self._coeff(identifier)).__dict__ for identifier in neighbour_nodes],
            "links": [d3link(self._name(link.source), self._name(link.target), 1.0).__dict__ for link in selected_links] \
                + [d3link(self._name(link.source), self._name(link.target), 0.15).__dict__ for link in neighbour_links]
        }

    def _name(self, term):
        return term.name()
        #return self.parser.inflections.to_inflection(term).name()

    def _coeff(self, term):
        return self.graph.clustering_coefficients[term]

    def _out(self, node_alphas, link_alphas):
        return {
            "nodes": [{"id": self.parser.inflections.to_inflection(identifier).name(), "group": 0, "coeff": self.graph.clustering_coefficients[identifier]} for identifier in nodes],
            "links": [{"source": self.parser.inflections.to_inflection(link.source).name(), "target": self.parser.inflections.to_inflection(link.target).name()} for link in links]
        }


def str_kv(value):
    if isinstance(value, dict):
        return {str(k): str_kv(v) for k, v in value.iteritems()}
    else:
        return str(value)


def write_json(graph, output_json):
    nodes = [{"id": node.identifier.name(), "group": i % 10} for i, node in enumerate(graph.all_nodes)]
    links = [{"source": link.source.name(), "target": link.target.name()} for link in graph.links()]

    with open(output_json, "w") as fh:
        fh.write(json.dumps({"nodes": nodes, "links": links}, indent=4, sort_keys=True))


if __name__ == "__main__":
    sys.exit(main())


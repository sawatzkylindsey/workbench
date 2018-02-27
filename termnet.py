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
from log import setup_logging, user_log
from parser import GlossaryCsv


GLOSSARY_CSV = "glossary_csv"
FORMATS = [
    GLOSSARY_CSV
]
TOP = 10


def main():
    parser = ArgumentParser(prog="termnet")
    parser.add_argument("--verbose", "-v",
                        default=False,
                        action="store_true",
                        # Unfortunately, logging in python 2.7 doesn't have
                        # a built-in way to log asynchronously.
                        help="Turn on verbose logging.  " + \
                        "**This will SIGNIFICANTLY slow down the program.**")
    parser.add_argument("-f", "--input-format", default=GLOSSARY_CSV)
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
    def __init__(self, input_text, input_format):
        self.parser = parse_cooccurrences(input_text, input_format)
        builder = GraphBuilder(Graph.UNDIRECTED)

        for k, v in sorted(self.parser.cooccurrences.iteritems()):
            builder.add(k, v)

        self.graph = builder.build()
        portion = 1.0 / len(self.graph.all_nodes)
        self.rank = {n.identifier: portion for n in self.graph.all_nodes}
        self.page_ranks = {}
        self.average = {}
        self.softener = {}
        self._t = threading.Thread(target=self.calculate_ranks)
        self._t.daemon = True
        self._t.start()

    def calculate_ranks(self):
        i = 0

        for k, v in sorted(self.parser.cooccurrences.iteritems()):
            print("page ranking: %s" % k)
            self.page_ranks[k] = self.graph.page_rank(biases={i: 0.1 if i != k else 0.2 for i in v})
            self.average[k] = sum(self.page_ranks[k].values()) / len(self.page_ranks[k])
            self.softener[k] = self._find_softener(self.average[k])
            #if i >= 3:
            #    break

            i += 1

    def _find_softener(self, value):
        upper = 1.0
        lower = 2.0
        test = math.sqrt(value) / lower

        while test > value:
            lower = lower * 2.0
            test = math.sqrt(value) / lower

        midpoint = (lower + upper) / 2.0
        test = math.sqrt(value) / midpoint

        while not self._within(test, value):
            if test > value:
                upper = midpoint
            else:
                lower = midpoint

            midpoint = (lower + upper) / 2.0
            test = math.sqrt(value) / midpoint

        return lambda v: (math.sqrt(v) / midpoint) if v > value else v

    def _within(self, value, expected, epsilon=0.00001):
        return abs(expected - value) < epsilon

    def mark(self, term):
        if term is None:
            return {
                "nodes": [d3node(self._name(node.identifier), self.rank[node.identifier], 0.75, self._coeff(node.identifier)).__dict__ for node in self.graph.all_nodes],
                "links": [d3link(self._name(link.source), self._name(link.target), 0.75).__dict__ for link in self.graph.links()]
            }

        lemma_term = self.parser.inflections.to_lemma(term)
        average = self.average[lemma_term]
        average = sum(self.rank.values()) / len(self.rank)
        print(average)
        smoother = self._find_softener(average)
        #smoother = lambda v: math.sqrt(v) if v > average else v

        for k, v in self.page_ranks[lemma_term].iteritems():
            assert v >= 0.0 and v <= 1.0
            #softener = (math.log10(v) + 2.0) / 4.0
            #assert softener < v, "s: %s, v: %s" % (softener, v)
            #softened = (math.sqrt(v) / 2.0)
            #assert softened < v, "s: %s, v: %s" % (softened, v)
            softened = self.softener[lemma_term](v)
            #if v > average:
            #    assert softened < v, "a %s, v %s, s %s" % (average, v, softened)
            #else:
            #    assert softened > v, "a %s, v %s, s %s" % (average, v, softened)
            #print("s: %s, v: %s" % (self.softener[lemma_term](v), v))
            smoothed = smoother(v)
            self.rank[k] += smoothed

        total = sum(self.rank.values())
        scale = 1.0 / total
        assert scale >= 0.0
        self.rank = {k: scale * v for k, v in self.rank.iteritems()}
        node_ranks = {
            lemma_term: self.rank[lemma_term]
        }
        print(node_ranks)

        for node in self.graph.neighbourhood(lemma_term, 1):
            assert self.rank[node.identifier] >= 0.0 and self.rank[node.identifier] <= 1.0
            node_ranks[node.identifier] = self.rank[node.identifier]

        logging.debug(node_ranks)
        sorted_node_ranks = sorted(node_ranks.iteritems(), key=lambda item: item[1], reverse=True)
        print(sorted_node_ranks)
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
            "nodes": [d3node(self._name(identifier), node_ranks[identifier], 1.0, self._coeff(identifier)).__dict__ for identifier in selected_nodes] \
                + [d3node(self._name(identifier), node_ranks[identifier], 0.25, self._coeff(identifier)).__dict__ for identifier in neighbour_nodes],
            "links": [d3link(self._name(link.source), self._name(link.target), 1.0).__dict__ for link in selected_links] \
                + [d3link(self._name(link.source), self._name(link.target), 0.25).__dict__ for link in neighbour_links]
        }

    def _name(self, term):
        return self.parser.inflections.to_inflection(term).name()

    def _coeff(self, term):
        return self.graph.clustering_coefficients[term]

    #def _radius(self, value):
    #    assert value >= 0.0 and value <= 1.0
    #    scaled = (math.log10(value) + 2.0) / 2.0
    #
    #    if value < 0.01:
    #        return 0.01
    #    else:
    #        return value

    def _out(self, node_alphas, link_alphas):
        return {
            "nodes": [{"id": self.parser.inflections.to_inflection(identifier).name(), "group": 0, "coeff": self.graph.clustering_coefficients[identifier]} for identifier in nodes],
            "links": [{"source": self.parser.inflections.to_inflection(link.source).name(), "target": self.parser.inflections.to_inflection(link.target).name()} for link in links]
        }


def parse_cooccurrences(input_text, input_format):
    if input_format == GLOSSARY_CSV:
        parser = GlossaryCsv()
    else:
        raise ValueError("Unknown input format '%s'." % input_format)

    parser.parse(input_text)
    logging.debug(json.dumps(str_kv(parser.inflections.counts), indent=2, sort_keys=True))
    #logging.debug(json.dumps({str(k): str(v) for k, v in parser.inflections.counts.items()}, indent=2, sort_keys=True))
    return parser


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


#!/usr/bin/python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from collections import defaultdict
from csv import reader as csv_reader
import json
import itertools
import logging
import numpy
import os
import pdb
import pickle
import sys


from graph import GraphBuilder, Graph
from log import setup_logging, user_log
from parser import GlossaryCsv


GLOSSARY_CSV = "glossary_csv"
FORMATS = [
    GLOSSARY_CSV
]


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

    cooccurrences = read_cooccurrences(args.input_text, args.input_format)
    builder = GraphBuilder(Graph.UNDIRECTED)

    for k, v in sorted(cooccurrences.iteritems()):
        user_log.info("%s: %s" % (k, [str(i) for i in v]))
        builder.add(k, v)

    graph = builder.build()
    write_json(graph, args.output_json)
    return 0


class Termnet:
    def __init__(self, input_text, input_format):
        cooccurrences = read_cooccurrences(input_text, input_format)
        builder = GraphBuilder(Graph.UNDIRECTED)

        for k, v in sorted(cooccurrences.iteritems()):
            builder.add(k, v)

        self.graph = builder.build()
        self.page_ranks = {}
        portion = 1.0 / len(self.graph.all_nodes)
        self.rank = {n.identifier: portion for n in self.graph.all_nodes}
        i = 0

        for k, v in sorted(cooccurrences.iteritems()):
            print(k)
            self.page_ranks[k] = self.graph.page_rank(biases={i: 0.1 for i in v})

            #if i >= 3:
            #    break

            i += 1

    def mark(self, term):
        if term is None:
            return self._out([n.identifier for n in self.graph.all_nodes], self.graph.links())

        for k, v in self.page_ranks[term].iteritems():
            self.rank[k] += v

        total = sum(self.rank.values())
        scale = 1.0 / total
        self.rank = {k: scale * v for k, v in self.rank.iteritems()}
        node_ranks = []

        for node in self.graph.neighbourhood(term, 3):
            node_ranks += [(node.identifier, self.rank[node.identifier])]

        print(node_ranks)
        logging.debug(node_ranks)
        sorted_node_ranks = sorted(node_ranks, key=lambda item: item[1], reverse=True)
        print(sorted_node_ranks)
        nodes = [item[0] for item in sorted_node_ranks[:8]]
        print(nodes)
        logging.debug(nodes)
        links = []

        for link in self.graph.links():
            if link.source in nodes and link.target in nodes:
                links += [link]

        return self._out(nodes, links)

    def _out(self, nodes, links):
        return {
            "nodes": [{"id": identifier.name(), "group": 0, "coeff": self.graph.clustering_coefficients[identifier]} for identifier in nodes],
            "links": [{"source": link.source.name(), "target": link.target.name()} for link in links]
        }


def read_cooccurrences(input_text, input_format):
    if input_format == GLOSSARY_CSV:
        parser = GlossaryCsv()
    else:
        raise ValueError("Unknown input format '%s'." % input_format)

    parser.parse(input_text)
    logging.debug(json.dumps(str_kv(parser.inflections.counts), indent=2, sort_keys=True))
    #logging.debug(json.dumps({str(k): str(v) for k, v in parser.inflections.counts.items()}, indent=2, sort_keys=True))
    return parser.cooccurrences


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


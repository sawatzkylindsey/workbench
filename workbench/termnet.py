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
from pytils import check
import pickle
import sys
import threading


from workbench.frontend import d3node, d3link
from workbench.graph import GraphBuilder, Graph
from pytils.log import setup_logging, user_log
import workbench.parser
import workbench.nlp


TOP = 10
BIAS_RELATED = 0.05
BOTTOM_K = 0.1


def main():
    ap = ArgumentParser(prog="termnet")
    ap.add_argument("--verbose", "-v",
                        default=False,
                        action="store_true",
                        # Unfortunately, logging in python 2.7 doesn't have
                        # a built-in way to log asynchronously.
                        help="Turn on verbose logging.  " + \
                        "**This will SIGNIFICANTLY slow down the program.**")
    ap.add_argument("-f", "--input-format", default=workbench.parser.WIKIPEDIA, help="One of %s" % workbench.parser.FORMATS)
    ap.add_argument("input_text", nargs="+")
    args = ap.parse_args()
    setup_logging(".%s.log" % os.path.splitext(os.path.basename(__file__))[0], args.verbose, True)
    logging.debug(args)
    net = build(args.input_text, args.input_format)
    return 0


def build(input_text, input_format):
    check.check_instance(input_text, list)
    check.check_one_of(check.check_instance(input_format, str), workbench.parser.FORMATS)
    parse = workbench.parser.parse_input(input_text, input_format)
    builder = GraphBuilder(Graph.UNDIRECTED)
    maximum = max([max([len(l) for l in subd.values()]) for subd in parse.cooccurrences.values()])
    k = max(int(maximum * BOTTOM_K), 1)
    user_log.info("maximum: %s, k: %s" % (maximum, k))
    inflection_sentences = {}

    with open("cooccurrences.csv", "w") as fh:
        fh.write("a,b,sentence\n")

        for term_a, term_sentences in sorted(parse.cooccurrences.items()):
            source = parse.inflections.to_inflection(term_a)
            targets = {parse.inflections.to_inflection(term_b): sentences for term_b, sentences in filter(lambda item: len(item[1]) >= k, term_sentences.items())}

            if len(targets) > 0:
                builder.add(source, [t for t in targets.keys()])

                if source not in inflection_sentences:
                    inflection_sentences[source] = {}

                for target, sentences in targets.items():
                    if target not in inflection_sentences[source]:
                        inflection_sentences[source][target] = set()

                    for sentence in sentences:
                        inflection_sentences[source][target].add(sentence)

            for term_b, sentences in sorted(term_sentences.items()):
                for sentence in sentences:
                    fh.write("%s,%s,\"%s\"\n" % (term_a.name(), term_b.name(), sentence.replace("\"", "'")))

    with open("infl-sents.json", "w" ) as fh:
        fh.write(json.dumps(str_kv(inflection_sentences), indent=4, sort_keys=True))

    net = Termnet(builder.build(), inflection_sentences)
    return net


class Termnet:
    def __init__(self, graph, sentences):
        self.graph = graph
        self.sentences = sentences
        self.average = 1.0 / len(self.graph.all_nodes)
        self.rank = {n.identifier: self.average for n in self.graph.all_nodes}
        self.marked = False
        self.page_ranks = {}
        self.positive_influence = lambda x: 0
        self.negative_influence = lambda x: 0
        self.positive_points = set()
        self.negative_points = set()
        self.ignore_points = set()
        self._background_calculate_ranks = threading.Thread(target=self.calculate_ranks)
        self._background_calculate_ranks.daemon = True
        self._background_calculate_ranks.start()

    def calculate_ranks(self):
        for node in sorted(self.graph.all_nodes):
            user_log.info("page ranking: %s" % node.identifier.name())
            # Bias only the node itself
            self.page_ranks[node.identifier] = self.graph.page_rank(biases={node.identifier: self.average})
            # Bias the node's descendants
            #self.page_ranks[node.identifier] = self.graph.page_rank(biases={d.identifier: BIAS_RELATED for d in node.descendants})

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
        #logging.info("test: %s with %s" % (test, midpoint))

        while not self._within(test, value):
            if test > value:
                upper = midpoint
            else:
                lower = midpoint

            midpoint = (lower + upper) / 2.0
            test = f(value, midpoint)
            #logging.info("test: %s with %s" % (test, midpoint))

        #logging.info("found: %s" % midpoint)
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

        #logging.info("lis: %s, %s" % (i, j))
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

        #logging.info("ris: %s, %s" % (m, n))
        ris = self._find(value, self._right_inverse_sigmoid(value), m, n)
        def ris_fixed(x):
            y = ris(x)
            return y if y < x else x

        def s(v):
            if v <= value:
                scaled = lis_fixed(v)
            else:
                scaled = ris_fixed(v)

            #logging.info("scaled: %s -> %s" % (v, scaled))
            return scaled

        return s

    def _left_inverse_sigmoid(self, value):
        assert value >= 0.0 and value <= 1.0
        return lambda x, d: ((numpy.log10((1.0 / (-x + (2.0 * value))) - (0.5 / value)) + (1.0 / value)) / (1.0 / value)) + d

    def _right_inverse_sigmoid(self, value):
        assert value >= 0.0 and value <= 1.0
        return lambda x, d: ((numpy.log10((1.0 / (-x + 1.0)) - (0.5 / (1.0 - value))) + (1.0 / value)) / (1.0 / value)) + d

    def clean_slate(self):
        return len(self.positive_points) == 0 \
            and len(self.negative_points) == 0 \
            and len(self.ignore_points) == 0 \
            and not self.marked

    def reset(self):
        self.rank = {n.identifier: self.average for n in self.graph.all_nodes}
        self.positive_points = set()
        self.negative_points = set()
        self.ignore_points = set()
        self.marked = False

    def positive_add(self, term):
        assert term in self.graph
        self.positive_points.add(term)
        self.negative_remove(term)

    def positive_remove(self, term):
        assert term in self.graph

        if term in self.positive_points:
            self.positive_points.remove(term)

    def negative_add(self, term):
        assert term in self.graph
        self.negative_points.add(term)
        self.positive_remove(term)

    def negative_remove(self, term):
        assert term in self.graph

        if term in self.negative_points:
            self.negative_points.remove(term)

    def ignore_add(self, term):
        assert term in self.graph
        self.ignore_points.add(term)

    def ignore_remove(self, term):
        assert term in self.graph

        if term in self.ignore_points:
            self.ignore_points.remove(term)

    def mark(self, term):
        assert term in self.graph

        for k, v in self.page_ranks[term].items():
            assert v >= 0.0 and v <= 1.0, v
            self.rank[k] += v

        total = sum(self.rank.values())
        scale = 1.0 / total
        assert scale >= 0.0
        self.rank = {k: scale * v for k, v in self.rank.items()}
        self.marked = True

    def display(self, term):
        summary = ""

        if term is None:
            selection = [n.identifier for n in self.graph.all_nodes]
        else:
            selection = [identifier for identifier, d in self.graph.neighbourhood(term, 1, True, (2, 0.5))]

        selection = filter(lambda t: t not in self.ignore_points, selection)
        logging.debug("Positives: %s" % self.positive_points)
        logging.debug("Negatives: %s" % self.negative_points)
        positive_masks = [(point, lambda x: self.rank[point] * self.positive_influence(x)) for point in self.positive_points]
        negative_masks = [(point, lambda x: self.rank[point] * self.negative_influence(x)) for point in self.negative_points]
        node_ranks = {}
        sum_subgraph = 0.0

        for identifier in selection:
            assert self.rank[identifier] >= 0.0 and self.rank[identifier] <= 1.0
            node_rank = self.rank[identifier]
            masked_rank = 0.0
            masked_count = 0

            for point, mask in positive_masks:
                d = self.graph.distance(point, identifier)
                distance = self.graph.max_distance - d if d is not None else 0
                masked_rank += mask(distance) * node_rank
                masked_count += 1

            for point, mask in negative_masks:
                d = self.graph.distance(point, identifier)
                distance = d if d is not None else self.graph.max_distance
                #distance = self.graph.max_distance - d if d is not None else 0
                masked_rank += mask(distance) * node_rank
                masked_count += 1

            if masked_count == 0:
                masked_rank = node_rank
                masked_count = 1

            logging.debug("%s: masked rank: %s, base rank: %s" % (identifier.name(), masked_rank, node_rank))
            node_ranks[identifier] = (masked_rank / masked_count)
            sum_subgraph += self.rank[identifier]

        total = sum(node_ranks.values())
        scale = 1.0 / total
        assert scale >= 0.0
        node_ranks = {k: scale * v for k, v in node_ranks.items()}
        logging.debug(node_ranks)
        sorted_node_ranks = sorted(node_ranks.items(), key=lambda item: item[1], reverse=True)
        logging.info("%s: %s" % (sum_subgraph, sorted_node_ranks))
        #smoothing_point = int(math.ceil(len(node_ranks) * 0.05))
        #smoother = self._find_softener(sum([item[1] for item in sorted_node_ranks[:smoothing_point]]) / smoothing_point)

        if self.clean_slate():
            selected_nodes = [item[0] for item in sorted_node_ranks]
            neighbour_nodes = []
        else:
            selected_nodes = [item[0] for item in sorted_node_ranks[:TOP]]
            neighbour_nodes = [item[0] for item in sorted_node_ranks[TOP:]]

        selected_links = []
        neighbour_links = []
        best = 0

        for link in self.graph.links():
            if link.source in selected_nodes and link.target in selected_nodes:
                selected_links += [link]
                score = node_ranks[link.source] + node_ranks[link.target]

                if score > best:
                    best = score
                    summary = "|||".join(self.sentences[link.source][link.target])
            elif (link.source in selected_nodes and link.target in neighbour_nodes) \
                or (link.source in neighbour_nodes and link.target in selected_nodes) \
                or (link.source in neighbour_nodes and link.target in neighbour_nodes):
                neighbour_links += [link]

        return {
            "nodes": [d3node(self._name(identifier), node_ranks[identifier], 1.0, self._coeff(identifier)).__dict__ for identifier in selected_nodes] \
                + [d3node(self._name(identifier), node_ranks[identifier], 0.15, self._coeff(identifier)).__dict__ for identifier in neighbour_nodes],
            "links": [d3link(self._name(link.source), self._name(link.target), 1.0).__dict__ for link in selected_links] \
                + [d3link(self._name(link.source), self._name(link.target), 0.15).__dict__ for link in neighbour_links],
            "summary": summary
        }

    def _name(self, term):
        return term.name()

    def _coeff(self, term):
        return self.graph.clustering_coefficients[term]


def str_kv(value):
    if isinstance(value, dict):
        return {str(k): str_kv(v) for k, v in value.items()}
    else:
        return str(value)


def write_json(graph, output_json):
    nodes = [{"id": node.identifier.name(), "group": i % 10} for i, node in enumerate(graph.all_nodes)]
    links = [{"source": link.source.name(), "target": link.target.name()} for link in graph.links()]

    with open(output_json, "w") as fh:
        fh.write(json.dumps({"nodes": nodes, "links": links}, indent=4, sort_keys=True))


if __name__ == "__main__":
    sys.exit(main())


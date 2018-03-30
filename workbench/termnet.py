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


from workbench.check import check_instance, check_one_of
from workbench.frontend import d3node, d3link
from workbench.graph import GraphBuilder, Graph
from pytils.log import setup_logging, user_log
import workbench.parser
import workbench.nlp


TOP = 10
BIAS_RELATED = 0.1
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
    check_instance(input_text, list)
    check_one_of(check_instance(input_format, str), workbench.parser.FORMATS)
    parse = workbench.parser.parse_input(input_text, input_format)
    builder = GraphBuilder(Graph.UNDIRECTED)
    ## Could use comprehensions, but actually would be slower (would need to iterate twice).
    #total = 0
    #length = 0

    #for occurrences in parse.cooccurrences.values():
    #    for value in occurrences.values():
    #        total += value
    #        length += 1

    #average = float(total) / float(length)
    #print("average: %s" % average)
    maximum = max([max(subd.values()) for subd in parse.cooccurrences.values()])
    k = max(int(maximum * BOTTOM_K), 1)
    user_log.info("maximum: %s, k: %s" % (maximum, k))

    with open("cooccurrences.csv", "w") as fh:
        fh.write("a,b,count\n")

        for term_a, term_counts in sorted(parse.cooccurrences.items()):
            terms = [parse.inflections.to_inflection(term_b) for term_b, count in filter(lambda item: item[1] >= k, term_counts.items())]

            if len(terms) > 0:
                builder.add(parse.inflections.to_inflection(term_a), terms)
                #builder.add(parse.inflections.to_inflection(term_a), [parse.inflections.to_inflection(term_b) for term_b, count in filter(lambda item: item[1] > 1, term_counts.items())])
                #builder.add(parse.inflections.to_inflection(term_a), [parse.inflections.to_inflection(term_b) for term_b, count in term_counts.items()])

            for term_b, count in sorted(term_counts.items()):
                fh.write("%s,%s,%d\n" % (term_a.name(), term_b.name(), count))

    net = Termnet(builder.build())
    return net


class Termnet:
    LIMIT = 100

    def __init__(self, graph):
        self.graph = graph
        self.average = 1.0 / len(self.graph.all_nodes)
        self.rank = {n.identifier: self.average for n in self.graph.all_nodes}
        self.page_ranks = {}
        self.positive_points = {}
        self.negative_points = {}
        self.started = True
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

    def _find_distance_mask(self, value, positive):
        upper = -100.0
        lower = 100.0
        f = self._dropout_sigmoid(True)
        delta = abs(lower - upper) / 2.0
        midpoint = upper + delta
        print(midpoint)
        test = f(0, midpoint)
        #logging.info("test: %s with %s" % (test, midpoint))

        while not self._within(test, value):
            if test > value:
                upper = midpoint
            else:
                lower = midpoint

            delta = abs(lower - upper) / 2.0
            midpoint = upper + delta
            print(midpoint)
            test = f(0, midpoint)
            #logging.info("test: %s with %s" % (test, midpoint))

        #logging.info("found: %s" % midpoint)
        f = self._dropout_sigmoid(positive)
        return lambda x: f(x, midpoint) + 1.0

    def _dropout_sigmoid(self, positive):
        #assert value >= 0.0 and value <= 1.0
        return lambda x, d: 1.0 / (1.0 + numpy.exp((x if positive else -x) + d))

    def reset(self):
        self.rank = {n.identifier: self.average for n in self.graph.all_nodes}
        self.positive_points = {}
        self.negative_points = {}
        self.started = True

    def positive(self, term):
        self.started = False
        self.positive_points[term] = self.positive_points.get(term, 0) + 1

        if term in self.negative_points:
            del self.negative_points[term]

    def negative(self, term):
        self.started = False
        self.negative_points[term] = self.negative_points.get(term, 0) + 1

        if term in self.positive_points:
            del self.positive_points[term]

        logging.debug(self.negative_points)
        logging.debug(self.positive_points)

    def mark(self, term):
        assert term is not None

        for k, v in self.page_ranks[term].items():
            assert v >= 0.0 and v <= 1.0, v
            self.rank[k] += v

        total = sum(self.rank.values())
        scale = 1.0 / total
        assert scale >= 0.0
        self.rank = {k: scale * v for k, v in self.rank.items()}
        self.started = False

    def display(self, term):
        #if term is None:
            #node_ranks = {}

            #for node in self.graph.all_nodes:
            #    assert self.rank[node.identifier] >= 0.0 and self.rank[node.identifier] <= 1.0
            #    node_ranks[node.identifier] = self.rank[node.identifier]

            #sorted_node_ranks = sorted(node_ranks.items(), key=lambda item: item[1], reverse=True)
            #smoothing_point = int(math.ceil(len(node_ranks) * 0.1))
            #smoother = self._find_softener(sum([item[1] for item in sorted_node_ranks[:smoothing_point]]) / smoothing_point)
            #selected_nodes = [item[0] for item in sorted_node_ranks[:TOP]]
            #return {
            #    "nodes": [d3node(self._name(node.identifier), smoother(self.rank[node.identifier]), 0.75, self._coeff(node.identifier)).__dict__ for node in self.graph.all_nodes],
            #    "links": [d3link(self._name(link.source), self._name(link.target), 0.75).__dict__ for link in self.graph.links()]
            #}
        if term is None:
            selection = [n.identifier for n in self.graph.all_nodes]
        else:
            selection = [identifier for identifier, d in self.graph.neighbourhood(term, 1, True, (2, 0.5))]

        #positive_masks = [(p, self._find_distance_mask(min(self.rank[p] * 2, 1.0), True)) for p in self.positive_points]
        #negative_masks = [(p, self._find_distance_mask(min(self.rank[p] * 10, 1.0), False)) for p in self.negative_points]
        positive_masks = [(point, lambda x: (self.rank[point] * times) * (x**1.7)) for point, times in self.positive_points.items()]
        negative_masks = [(point, lambda x: (self.rank[point] * times) * (x**1.7)) for point, times in self.negative_points.items()]
        node_ranks = {}
        sum_subgraph = 0.0

        for identifier in selection:
            assert self.rank[identifier] >= 0.0 and self.rank[identifier] <= 1.0
            node_rank = self.rank[identifier]
            masked_rank = 0.0
            masked_count = 0

            for point, mask in positive_masks:
                d = self.graph.distance(point, identifier)
                #distance = d if d is not None else self.graph.max_distance
                distance = self.graph.max_distance - d if d is not None else 0
                masked_rank += mask(distance) * node_rank
                masked_count += 1

            for point, mask in negative_masks:
                d = self.graph.distance(point, identifier)
                distance = d if d is not None else self.graph.max_distance
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
        smoothing_point = int(math.ceil(len(node_ranks) * 0.05))
        smoother = self._find_softener(sum([item[1] for item in sorted_node_ranks[:smoothing_point]]) / smoothing_point)

        if self.started:
            selected_nodes = [item[0] for item in sorted_node_ranks]
            neighbour_nodes = []
        else:
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

    def _coeff(self, term):
        return self.graph.clustering_coefficients[term]

    def _out(self, node_alphas, link_alphas):
        return {
            "nodes": [{"id": self.parser.inflections.to_inflection(identifier).name(), "group": 0, "coeff": self.graph.clustering_coefficients[identifier]} for identifier in nodes],
            "links": [{"source": self.parser.inflections.to_inflection(link.source).name(), "target": self.parser.inflections.to_inflection(link.target).name()} for link in links]
        }


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


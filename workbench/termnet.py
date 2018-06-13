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


from workbench.graph import GraphBuilder, Graph
from pytils.log import setup_logging, user_log
import workbench.parser
from workbench.nlp import Term


TOP = 10
BIAS_RELATED = 0.05
BOTTOM_K = 0.1
HARD_CAP = 1000


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
    ap.add_argument("-w", "--window", default=0)
    ap.add_argument("input_texts", nargs="+")
    args = ap.parse_args()
    setup_logging(".%s.log" % os.path.splitext(os.path.basename(__file__))[0], args.verbose, True)
    logging.debug(args)
    net = build(args.input_texts, args.input_format, args.window)
    return 0


def build(input_text, input_format, window, keep):
    check.check_iterable(input_text)
    assert window > 0, window
    assert keep >= 0 and keep <= 100, keep
    parse = workbench.parser.parse_input(input_text, input_format, window)
    builder = GraphBuilder(Graph.UNDIRECTED)
    count_histogram = {}

    for subd in parse.cooccurrences.values():
        for term_sentences in subd.values():
            if len(term_sentences) not in count_histogram:
                count_histogram[len(term_sentences)] = 0

            count_histogram[len(term_sentences)] += 1

    logging.debug("count_histogram: %s" % count_histogram)
    sub_lengths = [[] if len(subd) == 0 else [len(l) for l in subd.values()] for subd in parse.cooccurrences.values()]

    if len(sub_lengths) > 0:
        maximum = max([0 if len(l) == 0 else max(l) for l in sub_lengths])
        minimum = min([0 if len(l) == 0 else min(l) for l in sub_lengths])
        average = sum([i for l in sub_lengths for i in l]) / sum([len(l) for l in sub_lengths])
    else:
        maximum = 0
        minimum = 0
        average = 0.0

    bottom_percent = (100.0 - keep) / 100.0
    cutoff = max(int(maximum * bottom_percent), 1)
    #print("cutoff: %d" % cutoff)
    logging.debug("maximum: %s, cutoff: %s" % (maximum, cutoff))
    inflection_sentences = {}
    excluded_terms = set()
    included_terms = set()

    for term_a, term_sentences in sorted(parse.cooccurrences.items()):
        source = parse.inflections.to_inflection(term_a)
        excluded_terms.add(source)
        targets = {parse.inflections.to_inflection(term_b): sentences for term_b, sentences in filter(lambda item: len(item[1]) >= cutoff, term_sentences.items())}

        if len(targets) > 0:
            builder.add(source, [t for t in targets.keys()])
            included_terms.add(source)
            excluded_terms.remove(source)

            if source not in inflection_sentences:
                inflection_sentences[source] = {}

            for target, sentences in targets.items():
                included_terms.add(target)

                if target not in inflection_sentences[source]:
                    inflection_sentences[source][target] = set()

                for sentence in sentences:
                    inflection_sentences[source][target].add(" ".join(sentence))

    graph = builder.build()
    properties = Properties(minimum, maximum, average, cutoff, len(included_terms) + len(excluded_terms), included_terms, excluded_terms)
    #print(len(graph))

    if len(graph) > 0:
        return Termnet(graph, inflection_sentences, properties)
    else:
        builder = GraphBuilder(Graph.UNDIRECTED)
        return Termnet(builder.build(), {}, Properties())

    return net


class Properties:
    def __init__(self, minimum_cooccurrence_count=0, maximum_cooccurrence_count=0, average_cooccurrence_count=0, cutoff_cooccurrence_count=0, total_terms=0, included_terms=[], excluded_terms=[]):
        self.minimum_cooccurrence_count = minimum_cooccurrence_count
        self.maximum_cooccurrence_count = maximum_cooccurrence_count
        self.average_cooccurrence_count = average_cooccurrence_count
        self.cutoff_cooccurrence_count = cutoff_cooccurrence_count
        self.total_terms = total_terms
        self.included_terms = [term.name() for term in included_terms]
        self.excluded_terms = [term.name() for term in excluded_terms]

    def dump(self):
        return {
            "minimum_cooccurrence_count": self.minimum_cooccurrence_count,
            "maximum_cooccurrence_count": self.maximum_cooccurrence_count,
            "average_cooccurrence_count": self.average_cooccurrence_count,
            "cutoff_cooccurrence_count": self.cutoff_cooccurrence_count,
            "total_terms": self.total_terms,
            "included": self.included_terms,
            "excluded": self.excluded_terms,
        }


class Termnet:
    def __init__(self, graph, sentences, properties):
        self.graph = graph
        self.sentences = sentences
        self.properties = properties
        self.average = 0 if len(self.graph) == 0 else 1.0 / len(self.graph.all_nodes)
        self.page_ranks = {}
        self._background_calculate_ranks = threading.Thread(target=self.calculate_ranks)
        self._background_calculate_ranks.daemon = True
        self._background_calculate_ranks.start()

    def calculate_ranks(self):
        for node in sorted(self.graph.all_nodes):
            logging.debug("page ranking: %s" % node.identifier.name())
            # Bias only the node itself
            self.page_ranks[node.identifier] = self.graph.page_rank(biases={node.identifier: self.average})
            # Bias the node's descendants
            #self.page_ranks[node.identifier] = self.graph.page_rank(biases={d.identifier: BIAS_RELATED for d in node.descendants})

    def meta_data(self):
        return self.properties.dump()


class TermnetSession:
    def __init__(self, termnet):
        self.termnet = termnet
        self.rank = {n.identifier: self.termnet.average for n in self.termnet.graph.all_nodes}
        self.focus_points = set()
        self.positive_influence = lambda x: 0
        self.negative_influence = lambda x: 0
        self.positive_points = set()
        self.negative_points = set()
        self.ignore_points = set()
        self.highlight_points = set()
        self.previous_term = None

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
        return len(self.focus_points) == 0 \
            and len(self.positive_points) == 0 \
            and len(self.negative_points) == 0 \
            and len(self.ignore_points) == 0

    def reset(self):
        self.rank = {n.identifier: self.termnet.average for n in self.termnet.graph.all_nodes}
        self.focus_points = set()
        self.positive_points = set()
        self.negative_points = set()
        self.ignore_points = set()
        self.highlight_points = set()

    def positive_add(self, term):
        assert term in self.termnet.graph
        self.positive_points.add(term)
        self.negative_remove(term)

    def positive_remove(self, term):
        assert term in self.termnet.graph

        if term in self.positive_points:
            self.positive_points.remove(term)

    def negative_add(self, term):
        assert term in self.termnet.graph
        self.negative_points.add(term)
        self.positive_remove(term)

    def negative_remove(self, term):
        assert term in self.termnet.graph

        if term in self.negative_points:
            self.negative_points.remove(term)

    def ignore_add(self, term):
        assert term in self.termnet.graph
        self.ignore_points.add(term)

    def ignore_remove(self, term):
        assert term in self.termnet.graph

        if term in self.ignore_points:
            self.ignore_points.remove(term)

    def highlight_add(self, term):
        assert term in self.termnet.graph
        self.highlight_points.add(term)

    def highlight_remove(self, term):
        assert term in self.termnet.graph

        if term in self.highlight_points:
            self.highlight_points.remove(term)

    def focus(self, term):
        assert term in self.termnet.graph

        while True:
            try:
                self.termnet.page_ranks[term]
                break
            except KeyError as e:
                pass

        for k, v in self.termnet.page_ranks[term].items():
            assert v >= 0.0 and v <= 1.0, v
            self.rank[k] += v

        total = sum(self.rank.values())
        scale = 1.0 / total
        assert scale >= 0.0
        self.rank = {k: scale * v for k, v in self.rank.items()}
        self.focus_points.add(term)

    def display_previous(self):
        return self.display(self.previous_term)

    def display(self, search_term):
        self.previous_term = search_term
        summary = ""

        if search_term is None:
            selection = set([n.identifier for n in self.termnet.graph.all_nodes])
        else:
            selection = set([identifier for identifier, d in self.termnet.graph.neighbourhood(search_term, 1, True, (2, 0.5))])

        for point in self.highlight_points:
            selection.add(point)

        logging.debug("Positives: %s" % self.positive_points)
        logging.debug("Negatives: %s" % self.negative_points)
        positive_masks = [(point, lambda x: self.rank[point] * self.positive_influence(x)) for point in self.positive_points]
        negative_masks = [(point, lambda x: self.rank[point] * self.negative_influence(x)) for point in self.negative_points]
        node_ranks = {}
        sum_subgraph = 0.0

        for identifier in selection:
            assert self.rank[identifier] >= 0.0 and self.rank[identifier] <= 1.0
            node_rank = self.rank[identifier]
            masked_rank = node_rank
            masked_count = 1

            for point, mask in positive_masks:
                d = self.termnet.graph.distance(point, identifier)
                distance = self.termnet.graph.max_distance(point) - d if d is not None else 0
                masked_rank += mask(distance) * self.rank[point]
                masked_count += 1

            for point, mask in negative_masks:
                d = self.termnet.graph.distance(point, identifier)
                distance = d if d is not None else self.termnet.graph.max_distance(point)
                masked_rank += mask(distance) * self.rank[point]
                masked_count += 1

            logging.debug("%s: masked rank: %s, base rank: %s" % (identifier.name(), masked_rank, node_rank))
            node_ranks[identifier] = (masked_rank / masked_count)
            sum_subgraph += self.rank[identifier]

        if len(node_ranks) == 0:
            return {
                "nodes": [],
                "links": [],
                "summary": "",
                "size": 0,
                "selection": 0,
            }

        total = sum(node_ranks.values())
        scale = 1.0 / total
        assert scale >= 0.0
        node_ranks = {k: scale * v for k, v in node_ranks.items()}
        logging.debug(node_ranks)
        sorted_node_ranks = sorted(filter(lambda item: item[0] not in self.ignore_points, node_ranks.items()), key=lambda item: item[1], reverse=True)
        logging.info("%s: %s" % (sum_subgraph, sorted_node_ranks))

        if self.clean_slate():
            selected_nodes = set([item[0] for item in sorted_node_ranks])
            neighbour_nodes = set()
        else:
            selected_nodes = set([item[0] for item in sorted_node_ranks[:TOP]])
            neighbour_nodes = set([item[0] for item in sorted_node_ranks[TOP:]])

            for point in filter(lambda point: point not in self.ignore_points, self.focus_points):
                selected_nodes.add(point)

                if point in neighbour_nodes:
                    neighbour_nodes.remove(point)

            for point in self.highlight_points:
                selected_nodes.add(point)

                if point in neighbour_nodes:
                    neighbour_nodes.remove(point)

        selected_links = []
        neighbour_links = []
        highlight_links = set()
        cascade_points = set()
        best = 0

        for link in self.termnet.graph.links():
            if link.source in selected_nodes and link.target in selected_nodes:
                selected_links += [link]
                score = node_ranks[link.source] + node_ranks[link.target]

                if score > best:
                    logging.debug("New best score %.5f with %s and %s." % (score, link.source, link.target))
                    best = score

                    try:
                        alpha = [s for s in self.termnet.sentences[link.source][link.target]]
                    except KeyError as e:
                        alpha = []

                    try:
                        beta = [s for s in self.termnet.sentences[link.target][link.source]]
                    except KeyError as e:
                        beta = []

                    summary = "|||".join(alpha + beta)
            elif (link.source in selected_nodes and link.target in neighbour_nodes) \
                or (link.source in neighbour_nodes and link.target in selected_nodes) \
                or (link.source in neighbour_nodes and link.target in neighbour_nodes):
                neighbour_links += [link]

            if link.source in self.highlight_points or link.target in self.highlight_points:
                highlight_links.add(link)

            if link.source in self.highlight_points and link.target in neighbour_nodes:
                cascade_points.add(link.target)
            elif link.source in neighbour_nodes and link.target in self.highlight_points:
                cascade_points.add(link.source)

        cascade_nodes = set()

        for point in cascade_points:
            cascade_nodes.add(point)
            neighbour_nodes.remove(point)

        return {
            "nodes": [self._node(node_ranks, identifier, 1.0) for identifier in selected_nodes] \
                + [self._node(node_ranks, identifier, 0.5) for identifier in cascade_nodes] \
                + [self._node(node_ranks, identifier, 0.1) for identifier in neighbour_nodes],
            "links": [self._link(link, 1.0 if link in highlight_links else 0.5) for link in selected_links] \
                + [self._link(link, 1.0 if link in highlight_links else 0.1) for link in neighbour_links],
            "summary": summary,
            "size": len(selected_nodes) + len(cascade_nodes) + len(neighbour_nodes),
            "selection": len(selected_nodes) + len(cascade_nodes),
        }

    def _node(self, node_ranks, identifier, alpha):
        return {
            "name": self._name(identifier),
            "rank": node_ranks[identifier],
            "alpha": alpha,
            "colour": "green" if identifier in self.focus_points else "blue",
            "coeff": self._coeff(identifier),
        }

    def _link(self, link, alpha):
        return {
            "source": self._name(link.source),
            "target": self._name(link.target),
            "alpha": alpha,
        }

    def _name(self, term):
        return term.name()

    def _coeff(self, term):
        return self.termnet.graph.clustering_coefficients[term]


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


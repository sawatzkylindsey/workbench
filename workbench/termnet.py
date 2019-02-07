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


from workbench.graph import GraphBuilder, Graph, RankedGraph
from pytils.log import setup_logging, user_log
import workbench.parser
from workbench.nlp import Term, Inflections
from workbench.nlp import stem as CANONICALIZE
from workbench import util


TOP = 10
LEFT = "left"
RIGHT = "right"


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


def build(input_text, input_format, window, separator, keep):
    check.check_iterable(input_text)
    assert window > 0, window
    assert keep >= 0 and keep <= 100, keep
    parse = workbench.parser.parse_input(input_text, input_format, window, separator)
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
    logging.debug("maximum: %s, cutoff: %s" % (maximum, cutoff))
    occurring_sentences = {}
    excluded_lemmas = set()
    included_lemmas = set()

    for source, target_sentences in sorted(parse.cooccurrences.items()):
        #source = parse.inflections.to_dominant_inflection(term_a)
        excluded_lemmas.add(source)
        targets = {target: sentences for target, sentences in filter(lambda item: len(item[1]) >= cutoff, target_sentences.items())}
        #targets = {parse.inflections.to_dominant_inflection(term_b): sentences for term_b, sentences in filter(lambda item: len(item[1]) >= cutoff, term_sentences.items())}

        if len(targets) > 0:
            builder.add(source, [t for t in targets.keys()])
            included_lemmas.add(source)
            excluded_lemmas.remove(source)

            if source not in occurring_sentences:
                occurring_sentences[source] = {}

            for target, sentences in targets.items():
                included_lemmas.add(target)

                if target not in occurring_sentences[source]:
                    occurring_sentences[source][target] = set()

                for sentence in sentences:
                    occurring_sentences[source][target].add(" ".join(sentence))

    graph = builder.build()
    properties = Properties(parse.inflections, minimum,
        maximum,
        average,
        cutoff,
        len(included_lemmas) + len(excluded_lemmas),
        included_lemmas,
        excluded_lemmas)

    if len(graph) > 0:
        return Termnet(graph, {LEFT: RankedGraph(graph)}, parse.inflections, occurring_sentences, properties)
    else:
        empty = GraphBuilder(Graph.UNDIRECTED).build()
        inflections = Inflections()
        return Termnet(empty, {LEFT: RankedGraph(empty)}, inflections, {}, Properties(inflections))

    return net


class Properties:
    def __init__(self, inflections, minimum_cooccurrence_count=0, maximum_cooccurrence_count=0, average_cooccurrence_count=0, cutoff_cooccurrence_count=0, total_terms=0, included_lemmas=set(), excluded_lemmas=set()):
        self.inflections = inflections
        self.minimum_cooccurrence_count = minimum_cooccurrence_count
        self.maximum_cooccurrence_count = maximum_cooccurrence_count
        self.average_cooccurrence_count = average_cooccurrence_count
        self.cutoff_cooccurrence_count = cutoff_cooccurrence_count
        self.total_terms = total_terms
        self.included_lemmas = included_lemmas
        self.excluded_lemmas = excluded_lemmas

    def dump(self):
        return {
            "minimum_cooccurrence_count": self.minimum_cooccurrence_count,
            "maximum_cooccurrence_count": self.maximum_cooccurrence_count,
            "average_cooccurrence_count": self.average_cooccurrence_count,
            "cutoff_cooccurrence_count": self.cutoff_cooccurrence_count,
            "total_terms": self.total_terms,
            "included": [self.inflections.to_dominant_inflection(lemma).name() for lemma in self.included_lemmas],
            "excluded": [self.inflections.to_dominant_inflection(lemma).name() for lemma in self.excluded_lemmas],
        }


class Termnet:
    def __init__(self, display_graph, ranked_graphs, inflections, sentences, properties):
        assert set([display_graph.kind]) == set([rg.graph.kind for rg in ranked_graphs.values()]), "mismatching kinds"
        self.display_graph = display_graph
        self.ranked_graphs = ranked_graphs
        self.inflections = inflections
        self.sentences = sentences
        self.properties = properties
        # Calculated
        self.all_groups = set([group for group in self.ranked_graphs.keys()])
        self.node_groups = {}

        for group, ranked_graph in self.ranked_graphs.items():
            for node in ranked_graph.graph.all_nodes:
                if node.identifier not in self.node_groups:
                    self.node_groups[node.identifier] = set()

                self.node_groups[node.identifier].add(group)

    def groups(self, identifier):
        return self.node_groups[identifier]

    def compare_with(self, other):
        assert self.display_graph.kind == other.display_graph.kind
        assert len(self.ranked_graphs) == 1
        assert len(other.ranked_graphs) == 1
        builder = GraphBuilder(self.display_graph.kind)

        for node in self.display_graph.all_nodes:
            builder.add(node.identifier, [d.identifier for d in node.descendants])

        for node in other.display_graph.all_nodes:
            builder.add(node.identifier, [d.identifier for d in node.descendants])

        display_graph = builder.build()
        inflections = self.inflections.combine(other.inflections)
        occurring_sentences = {}

        for a, b_sentences in self.sentences.items():
            if a not in occurring_sentences:
                occurring_sentences[a] = {}

            for b, sentences in b_sentences.items():
                if b not in occurring_sentences[a]:
                    occurring_sentences[a][b] = set()

                for sentence in sentences:
                    occurring_sentences[a][b].add(sentence)

        for a, b_sentences in other.sentences.items():
            if a not in occurring_sentences:
                occurring_sentences[a] = {}

            for b, sentences in b_sentences.items():
                if b not in occurring_sentences[a]:
                    occurring_sentences[a][b] = set()

                for sentence in sentences:
                    occurring_sentences[a][b].add(sentence)

        included_lemmas = self.properties.included_lemmas.union(other.properties.included_lemmas)
        excluded_lemmas = self.properties.excluded_lemmas.union(other.properties.excluded_lemmas)

        for lemma in included_lemmas:
            excluded_lemmas.discard(lemma)

        properties = Properties(inflections,
            min(self.properties.minimum_cooccurrence_count, other.properties.minimum_cooccurrence_count),
            max(self.properties.maximum_cooccurrence_count, other.properties.maximum_cooccurrence_count),
            (self.properties.average_cooccurrence_count + other.properties.average_cooccurrence_count) / 2.0,
            self.properties.cutoff_cooccurrence_count if self.properties.cutoff_cooccurrence_count == other.properties.cutoff_cooccurrence_count else None,
            len(display_graph),
            included_lemmas,
            excluded_lemmas)
        return Termnet(display_graph,
            {
                LEFT: [silly for silly in self.ranked_graphs.values()][0],
                RIGHT: [silly for silly in other.ranked_graphs.values()][0]},
            inflections,
            occurring_sentences,
            properties)

    def decode(self, term):
        #try:
        inflection = Term(term.lower().split(" "))
        return self.inflections.to_lemma(inflection)
        #except KeyError as e:
        #    pass
        #return self.lemma_map[term.transform(lambda w: CANONICALIZE(w).lower())]

    def encode(self, lemma):
        return self.inflections.to_dominant_inflection(lemma).name()

    def meta_data(self):
        return self.properties.dump()


class TermnetSession:
    def __init__(self, termnet):
        self.termnet = termnet
        self.focus_metric = RankedGraph.BPR
        self.positive_influence = lambda x: 0
        self.negative_influence = lambda x: 0
        self.previous_term = None
        self.reset()

    def clean_slate(self):
        return not self.focused \
            and len(self.focus_points) == 0 \
            and len(self.positive_points) == 0 \
            and len(self.negative_points) == 0
            # Don't need to count ignore_points or highlight_points because they don't affect weights

    def reset(self):
        group_maximums = {group: ranked_graph.uniform for group, ranked_graph in self.termnet.ranked_graphs.items()}
        minimum = min(group_maximums.items(), key=lambda item: item[1])
        self.ranks = {group: {n.identifier: minimum[1] for n in ranked_graph.graph.all_nodes} for group, ranked_graph in self.termnet.ranked_graphs.items()}

        #for group in self.ranks.keys():
        #    if group != minimum[0]:
        #        self.ranks[group] = util.fit(self.ranks[group], minimum[1])

        #pdb.set_trace()
        self.focused = False
        self.focus_points = set()
        self.positive_points = set()
        self.negative_points = set()
        self.ignore_points = set()
        self.highlight_points = set()

    def positive_add(self, term):
        lemma = self.termnet.decode(term)
        assert lemma in self.termnet.display_graph
        self.positive_points.add(lemma)
        self.negative_points.discard(lemma)

    def positive_remove(self, term):
        lemma = self.termnet.decode(term)
        assert lemma in self.termnet.display_graph
        self.positive_points.discard(lemma)

    def negative_add(self, term):
        lemma = self.termnet.decode(term)
        assert lemma in self.termnet.display_graph
        self.negative_points.add(lemma)
        self.positive_points.discard(lemma)

    def negative_remove(self, term):
        lemma = self.termnet.decode(term)
        assert lemma in self.termnet.display_graph
        self.negative_points.discard(lemma)

    def ignore_add(self, term):
        lemma = self.termnet.decode(term)
        assert lemma in self.termnet.display_graph
        self.ignore_points.add(lemma)

    def ignore_remove(self, term):
        lemma = self.termnet.decode(term)
        assert lemma in self.termnet.display_graph
        self.ignore_points.discard(lemma)

    def highlight_add(self, term):
        lemma = self.termnet.decode(term)
        assert lemma in self.termnet.display_graph
        self.highlight_points.add(lemma)

    def highlight_remove(self, term):
        lemma = self.termnet.decode(term)
        assert lemma in self.termnet.display_graph
        self.highlight_points.discard(lemma)

    def highlight_toggle(self, term):
        lemma = self.termnet.decode(term)
        assert lemma in self.termnet.display_graph

        if lemma in self.highlight_points:
            self.highlight_points.remove(lemma)
        else:
            self.highlight_points.add(lemma)

    def focus(self, term):
        if term is None:
            assert self.focus_metric in RankedGraph.UNBIASED
            lemma = None
        else:
            if isinstance(term, list):
                lemma = []

                for t in term:
                    l = self.termnet.decode(t)
                    lemma += [l]
                    assert l in self.termnet.display_graph
            else:
                lemma = self.termnet.decode(term)
                assert lemma in self.termnet.display_graph

        if lemma is None or isinstance(lemma, list):
            groups = self.termnet.ranked_graphs.keys()
        else:
            groups = self.termnet.groups(lemma)

        for group in groups:
            for k, v in self.termnet.ranked_graphs[group].get_metric(self.focus_metric, lemma).items():
                assert v >= 0.0 and v <= 1.0, v
                self.ranks[group][k] += v

        group_maximums = {}

        for group in self.ranks.keys():
            self.ranks[group] = util.scale(self.ranks[group])
            group_maximums[group] = max(self.ranks[group].values())

        minimum = min(group_maximums.items(), key=lambda item: item[1])

        for group in self.ranks.keys():
            if group != minimum[0]:
                self.ranks[group] = util.fit(self.ranks[group], minimum[1])

        #pdb.set_trace()
        self.focused = True

        if lemma is not None:
            if isinstance(lemma, list):
                for l in lemma:
                    self.focus_points.add(l)
            else:
                self.focus_points.add(lemma)

    def display_previous(self):
        return self.display(self.previous_term)

    def display(self, term, radius=280):
        self.previous_term = term

        if term is None:
            selection = set([n.identifier for n in self.termnet.display_graph.all_nodes])
        else:
            lemma = self.termnet.decode(term)
            assert lemma in self.termnet.display_graph
            selection = set([identifier for identifier, d in self.termnet.display_graph.neighbourhood(lemma, 1, True, (2, 0.5))])

        for point in self.focus_points:
            selection.add(point)

        for point in self.highlight_points:
            selection.add(point)

        logging.debug("Positives: %s" % self.positive_points)
        logging.debug("Negatives: %s" % self.negative_points)
        positive_masks = {group: [] for group in self.termnet.all_groups}
        negative_masks = {group: [] for group in self.termnet.all_groups}

        for point in self.positive_points:
            for group in self.termnet.groups(point):
                positive_masks[group] += [(point, lambda x: self.ranks[group][point] * self.positive_influence(x))]

        for point in self.negative_points:
            for group in self.termnet.groups(point):
                negative_masks[group] += [(point, lambda x: self.ranks[group][point] * self.negative_influence(x))]

        group_node_ranks = {}
        sum_subgraph = 0.0

        for identifier in selection:
            for group in self.termnet.groups(identifier):
                if group not in group_node_ranks:
                    group_node_ranks[group] = {}

                assert self.ranks[group][identifier] >= 0.0 and self.ranks[group][identifier] <= 1.0
                node_rank = self.ranks[group][identifier]
                masked_rank = node_rank
                masked_count = 1

                for point, mask in positive_masks[group]:
                    d = self.termnet.ranked_graphs[group].graph.distance(point, identifier)
                    distance = self.termnet.ranked_graphs[group].graph.max_distance(point) - d if d is not None else 0
                    masked_rank += mask(distance) * self.ranks[group][point]
                    masked_count += 1

                for point, mask in negative_masks[group]:
                    d = self.termnet.ranked_graphs[group].graph.distance(point, identifier)
                    distance = d if d is not None else self.termnet.ranked_graphs[group].graph.max_distance(point)
                    masked_rank += mask(distance) * self.ranks[group][point]
                    masked_count += 1

                logging.debug("%s: %s: masked rank: %s, base rank: %s" % (group, identifier.name(), masked_rank, node_rank))
                group_node_ranks[group][identifier] = (masked_rank / masked_count)
                sum_subgraph += self.ranks[group][identifier]

        node_ranks = {}
        sorted_node_ranks = {}

        for group in group_node_ranks.keys():
            #group_node_ranks[group] = util.scale(group_node_ranks[group])
            sorted_node_ranks[group] = sorted(filter(lambda item: item[0] not in self.ignore_points, group_node_ranks[group].items()), key=lambda item: item[1], reverse=True)

        logging.debug(sorted_node_ranks)
        logging.info("%s: %s" % (sum_subgraph, sorted_node_ranks))
        alpha_dark = 1.0
        alpha_light = 0.1
        alpha_medium = (alpha_dark + alpha_light) / 2.0

        if self.clean_slate():
            selected_nodes = set()
            neighbour_nodes = set([item[0] for snr in sorted_node_ranks.values() for item in snr])
            #selected_nodes = set([item[0] for snr in sorted_node_ranks.values() for item in snr])
            #neighbour_nodes = set()
        else:
            selected_nodes = set([item[0] for snr in sorted_node_ranks.values() for item in snr[:TOP]])
            neighbour_nodes = selection.difference(selected_nodes)

            for point in filter(lambda point: point not in self.ignore_points, self.focus_points):
                selected_nodes.add(point)
                neighbour_nodes.discard(point)

            for point in self.ignore_points:
                neighbour_nodes.discard(point)

        for point in self.highlight_points:
            selected_nodes.add(point)
            neighbour_nodes.discard(point)

        selected_links = set()
        neighbour_links = set()
        highlight_links = set()
        cascade_points = set()
        link_counts = {}
        max_link_count = None
        best = 0
        summary = ""

        for link in self.termnet.display_graph.links():
            try:
                sentences_a = [s for s in self.termnet.sentences[link.source][link.target]]
            except KeyError as e:
                sentences_a = []

            try:
                sentences_b = [s for s in self.termnet.sentences[link.target][link.source]]
            except KeyError as e:
                sentences_b = []

            link_counts[link] = len(sentences_a) + len(sentences_b)

            if max_link_count is None or link_counts[link] > max_link_count:
                max_link_count = link_counts[link]

            if link.source in selected_nodes and link.target in selected_nodes:
                selected_links.add(link)
                score = 0.0

                for group in self.termnet.groups(link.source):
                    score += group_node_ranks[group][link.source]

                for group in self.termnet.groups(link.target):
                    score += group_node_ranks[group][link.target]

                if score > best:
                    logging.debug("New best score %.5f with %s and %s." % (score, link.source, link.target))
                    best = score
                    summary = "|||".join(sentences_a + sentences_b)
            elif (link.source in selected_nodes and link.target in neighbour_nodes) \
                or (link.source in neighbour_nodes and link.target in selected_nodes) \
                or (link.source in neighbour_nodes and link.target in neighbour_nodes):
                neighbour_links.add(link)

            if (link.source in self.highlight_points and link.target in neighbour_nodes) \
                or (link.source in neighbour_nodes and link.target in self.highlight_points):
                selected_links.add(link)
                neighbour_links.discard(link)

            if link.source in self.highlight_points and link.target in neighbour_nodes:
                cascade_points.add(link.target)
            elif link.source in neighbour_nodes and link.target in self.highlight_points:
                cascade_points.add(link.source)

        cascade_nodes = set()

        for point in cascade_points:
            cascade_nodes.add(point)
            neighbour_nodes.remove(point)

        size = len(selected_nodes) + len(cascade_nodes) + len(neighbour_nodes)
        link_counts_sum = float(sum(link_counts.values()))
        fill_size = math.pi * math.pow(radius, 2)
        virtual_width = ((max_link_count / link_counts_sum) * fill_size) / radius

        return {
            "nodes": [self._node(identifier, group_node_ranks, alpha_dark) for identifier in selected_nodes] \
                + [self._node(identifier, group_node_ranks, alpha_medium) for identifier in cascade_nodes] \
                + [self._node(identifier, group_node_ranks, alpha_medium if len(selected_nodes) == 0 else alpha_light) for identifier in neighbour_nodes],
            "links": [self._link(link, alpha_dark, ((link_counts[link] / link_counts_sum) * fill_size) / virtual_width) for link in selected_links] \
                + [self._link(link, alpha_medium if len(selected_nodes) == 0 else alpha_light, ((link_counts[link] / link_counts_sum) * fill_size) / virtual_width) for link in neighbour_links],
            "summary": summary,
            "size": size,
            "selection": len(selected_nodes) + len(cascade_nodes),
        }

    def _node(self, identifier, group_node_ranks, alpha):
        return {
            "name": self.termnet.encode(identifier),
            "ranks": {group: 0.0 if identifier not in group_node_ranks[group] else group_node_ranks[group][identifier] for group in self.termnet.all_groups},
            "alpha": alpha,
            "groups": [group for group in self.termnet.groups(identifier)],
            #"colour": self._colour(identifier),
            #"coeff": self._coeff(identifier),
        }

    def _link(self, link, alpha, distance):
        return {
            "source": self.termnet.encode(link.source),
            "target": self.termnet.encode(link.target),
            "alpha": alpha,
            "distance": distance,
            "stroke": self._stroke(link),
        }

    def _stroke(self, link):
        source_group = self.termnet.groups(link.source)
        target_group = self.termnet.groups(link.target)

        if source_group == target_group:
            return "full"
        else:
            return "dash"


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


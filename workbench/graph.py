#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging
import math
import pdb
import threading

from pytils import base, check


class Node(base.Comparable):
    # Note: Want instance based equals/hash.
    def __init__(self, identifier):
        super(Node, self).__init__()
        self.identifier = check.check_not_instance(identifier, Node)
        self.descendants = set()
        self.finalized = False
        self._hash = None

    def add_descendant(self, descendant):
        check.check_equal(self.finalized, False)
        check.check_instance(descendant, Node)
        check.check_not_equal(self.identifier, descendant.identifier)
        self.descendants.add(descendant)

    def finalize(self):
        self.finalized = True
        return self

    def __repr__(self):
        return "Node{identifer:%s}" % self.identifier

    def _comparator(self, fn, other):
        return fn(self.identifier, other.identifier)

    # We do indeed want object identity (writing a __cmp__ method forces us to write __eq__ and __hash__).
    def __eq__(self, other):
        return id(self) == id(other)

    # We do indeed want object identity (writing a __cmp__ method forces us to write __eq__ and __hash__).
    def __hash__(self):
        if self._hash is None:
            self._hash = id(self)

        return self._hash


class DirectedLink(object):
    def __init__(self, source, target):
        super(DirectedLink, self).__init__()
        self.source = check.check_not_instance(source, Node)
        self.target = check.check_not_instance(target, Node)
        self._hash = None

    def __repr__(self):
        return "DirectedLink{source:%s, target:%s}" % (self.source, self.target)

    def __eq__(self, other):
        return self.source == other.source and \
            self.target == other.target

    def __hash__(self):
        if self._hash is None:
            self._hash = hash((self.source, self.target))

        return self._hash


class UndirectedLink(object):
    def __init__(self, source, target):
        super(UndirectedLink, self).__init__()
        self.source = check.check_not_instance(source, Node)
        self.target = check.check_not_instance(target, Node)
        self._hash = None

    def __repr__(self):
        return "UndirectedLink{%s, %s}" % (self.source, self.target)

    def __eq__(self, other):
        return (self.source == other.source and self.target == other.target) or \
            (self.source == other.target and self.target == other.source)

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(self.source) + hash(self.target)

        return self._hash


class Graph(object):
    DIRECTED = "directed"
    UNDIRECTED = "undirected"

    def __init__(self, all_nodes, kind):
        if len(all_nodes) > 0:
            identifier_class = all_nodes[0].identifier.__class__

            for node in all_nodes:
                check.check_instance(node.identifier, identifier_class)
                check.check_equal(node.finalized, True)

        self.all_nodes = all_nodes
        self.kind = check.check_one_of(kind, [Graph.DIRECTED, Graph.UNDIRECTED])
        self.indexes = {}

        for node in self.all_nodes:
            self.indexes[node.identifier] = node

        self.clustering_coefficients = self._calculate_clustering_coefficients()
        self._distances = {}
        self._max_distances = {}
        self._global_max_distance = None
        self._background_calculations = threading.Thread(target=self._submit_calculations)
        self._background_calculations.daemon = True
        self._background_calculations.start()

    def __contains__(self, identifier):
        return identifier in self.indexes

    def __getitem__(self, identifier):
        return self.indexes[identifier]

    def __len__(self):
        return len(self.all_nodes)

    def _calculate_clustering_coefficients(self):
        ccs = {}

        for node in self.all_nodes:
            neighbours = [n for n in node.descendants]
            count = 0

            for i, neighbour in enumerate(neighbours):
                for j in range(i if self.kind == Graph.UNDIRECTED else 0, len(neighbours)):
                    if neighbours[j] in neighbour.descendants:
                        count += 1

            total = len(neighbours)
            cc = 0.0

            if count > 0:
                if total > 1:
                    numerator = float(total) * (total - 1)

                    if self.kind == Graph.UNDIRECTED:
                        numerator /= 2.0

                    cc = count / numerator

            ccs[node.identifier] = cc

        return ccs

    def _submit_calculations(self):
        for node in self.all_nodes:
            self._calculate_distance(node)

    def _calculate_distance(self, node):
        distances = {}
        maximum = 0

        for neighbour, distance in self.neighbourhood(node, None, True, None):
            distances[neighbour] = distance

            if distance > maximum:
                maximum = distance

        for neighbour in self.all_nodes:
            if neighbour.identifier not in distances:
                distances[neighbour.identifier] = None

        self._distances[node.identifier] = distances
        self._max_distances[node.identifier] = maximum

    def links(self):
        links = set()

        for node in self.all_nodes:
            for descendant in node.descendants:
                if self.kind == self.DIRECTED:
                    link = DirectedLink(node.identifier, descendant.identifier)
                elif self.kind == self.UNDIRECTED:
                    link = UndirectedLink(node.identifier, descendant.identifier)
                else:
                    raise ValueError(self.kind)

                links.add(link)

        logging.debug("links(%s): nodes=%d -> links=%d." % (self.kind, len(self), len(links)))
        return links

    def distance(self, identifier_a, identifier_b):
        if identifier_a not in self._distances:
            # The background calculation hasn't yet processed identifier_a.
            # So just quickly run it on demand.
            try:
                node = self[identifier_a]
                self._calculate_distance(node)
            except KeyError as e:
                pass

        return self._distances[identifier_a][identifier_b]

    def max_distance(self, identifier):
        if identifier not in self._max_distances:
            # The background calculation hasn't yet processed identifier_a.
            # So just quickly run it on demand.
            try:
                node = self[identifier_a]
                self._calculate_distance(node)
            except KeyError as e:
                pass

        return self._max_distances[identifier]

    def global_max_distance(self):
        if self._global_max_distance is None:
            # The background calculation hasn't yet processed all the distances.
            # So wait for it to complete, and then calculate the global maximum.
            self._background_calculations.join()
            self._global_max_distance = None if len(self._max_distances) == 0 else max(self._max_distances.values())

        return self._global_max_distance

    def sub_graph(self, identifiers):
        gb = GraphBuilder(self.kind)

        for link in self.links():
            if link.source in identifiers and link.target in identifiers:
                gb.add(link.source, [link.target])

        return gb.build()

    def neighbourhood(self, node_or_identifier, limit=None, self_inclusive=False, expansion=None):
        if expansion is not None:
            assert isinstance(expansion, tuple)
            assert len(expansion) == 2
            assert isinstance(expansion[0], int) and expansion[0] > 0
            assert expansion[1] > 0.0 and expansion[1] <= 1.0

        if isinstance(node_or_identifier, Node):
            node = node_or_identifier
        else:
            node = self.indexes[node_or_identifier]

        call_id = "%s-%s-%s" % (node.identifier, limit, self_inclusive)
        processing = [(node, 0)]
        processed = {}

        while len(processing) > 0:
            current_node, current_distance = processing.pop()
            current_cc = self.clustering_coefficients[current_node.identifier]
            processed[current_node.identifier] = current_distance
            #logging.debug("%s: adding %s-%d" % (call_id, current_node, current_distance))
            descendant_distance = current_distance + 1

            for descendant in current_node.descendants:
                #logging.debug("%s: explore %s-%d" % (call_id, descendant, descendant_distance))
                descendant_cc = self.clustering_coefficients[descendant.identifier]

                if (descendant.identifier not in processed or processed[descendant.identifier] > descendant_distance) \
                    and (limit is None or descendant_distance <= limit \
                        or (expansion is not None and descendant_distance <= (limit + expansion[0]) and (descendant_cc * expansion[1]) >= current_cc)):
                    #logging.debug("%s: queuing (cc %.2f) %s-%d" % (call_id, descendant_cc, descendant.identifier, descendant_distance))
                    processing.append((descendant, descendant_distance))

        if not self_inclusive:
            del processed[node.identifier]

        return set(processed.items())

    def nodes(self, identifiers):
        return set([self.indexes[i] for i in identifiers])

    def page_rank(self, damping=0.85, epsilon=0.005, epochs=50, biases={}):
        assert damping >= 0.0 and damping <= 1.0
        initial = 1.0 / len(self.all_nodes)
        weights = {n.identifier: initial for n in self.all_nodes}

        for i in range(0, epochs):
            next_weights = self.page_rank_iteration(weights, damping, biases)

            if self._delta(weights, next_weights) < epsilon:
                break

            weights = next_weights

        return next_weights

    def page_rank_iteration(self, weights, damping, biases):
        assert damping >= 0.0 and damping <= 1.0
        intermediaries = {n.identifier: 0.0 for n in self.all_nodes}
        leak = 0.0

        for node in self.all_nodes:
            if len(node.descendants) > 0:
                contribution = weights[node.identifier] / len(node.descendants)

                for descendant in node.descendants:
                    intermediaries[descendant.identifier] += contribution
            else:
                leak += weights[node.identifier]

        for k, v in biases.items():
            assert v >= 0.0 and v <= 1.0
            intermediaries[k] += v

        assert len(weights) == len(intermediaries)
        damping_constant = (1.0 - damping) / len(self.all_nodes)
        leak_constant = (damping * leak) / len(self.all_nodes)
        out = {}

        for k, v in intermediaries.items():
            out[k] = damping_constant + leak_constant + (damping * v)

        if len(biases) > 0:
            total = sum(out.values())
            scale = 1.0 / total
            out = {k: scale * v for k, v in out.items()}

        assert math.isclose(1.0, sum(out.values()), abs_tol=0.005), sum(out.values())
        return out

    def _delta(self, a, b):
        total = 0.0

        for k, v in a.items():
            total += abs(v - b[k])

        return total


class UndirectedGraph(Graph):
    def __init__(self, all_nodes):
        super(UndirectedGraph, self).__init__(all_nodes, Graph.UNDIRECTED)
        pass


class DirectedGraph(Graph):
    def __init__(self, all_nodes):
        super(DirectedGraph, self).__init__(all_nodes, Graph.DIRECTED)
        pass


class GraphBuilder:
    def __init__(self, direction):
        self.direction = direction
        self.nodes = {}

        if direction != Graph.DIRECTED and direction != Graph.UNDIRECTED:
            raise ValueError(direction)

    def add(self, identifier, descendants=[]):
        check.check_list_or_set(descendants)

        for descendant in descendants:
            if descendant not in self.nodes:
                self.nodes[descendant] = Node(descendant)

        if identifier not in self.nodes:
            self.nodes[identifier] = Node(identifier)

        for descendant in descendants:
            logging.debug("%s -> %s" % (identifier, descendant))
            self.nodes[identifier].add_descendant(self.nodes[descendant])

            if self.direction == Graph.UNDIRECTED:
                self.nodes[descendant].add_descendant(self.nodes[identifier])

        logging.debug("%s: %s" % (identifier, ",".join([str(d.identifier) for d in self.nodes[identifier].descendants])))
        return self

    def build(self):
        if self.direction == Graph.DIRECTED:
            return DirectedGraph([n.finalize() for n in self.nodes.values()])
        elif self.direction == Graph.UNDIRECTED:
            return UndirectedGraph([n.finalize() for n in self.nodes.values()])
        else:
            raise ValueError(self.direction)


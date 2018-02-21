#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import pdb

from check import checkInstance, checkNotInstance, checkEqual, checkNotEqual


class Node:
    # Note: Want instance based equals/hash.
    def __init__(self, identifier):
        self.identifier = checkNotInstance(identifier, Node)
        self.descendants = set()
        self.finalized = False

    def add_descendant(self, descendant):
        checkEqual(self.finalized, False)
        checkInstance(descendant, Node)
        checkNotEqual(self.identifier, descendant.identifier)
        self.descendants.add(descendant)

    def finalize(self):
        self.finalized = True
        return self

    def __str__(self):
        return "Node{identifer:%s}" % self.identifier

    def __repr__(self):
        return str(self)


class DirectedLink:
    def __init__(self, source, target):
        self.source = checkNotInstance(source, Node)
        self.target = checkNotInstance(target, Node)

    def __eq__(self, other):
        return self.source == other.source and \
            self.target == other.target

    def __hash__(self):
        return hash((self.source, self.target))


class UndirectedLink:
    def __init__(self, source, target):
        self.source = checkNotInstance(source, Node)
        self.target = checkNotInstance(target, Node)

    def __eq__(self, other):
        return (self.source == other.source and self.target == other.target) or \
            (self.source == other.target and self.target == other.source)

    def __hash__(self):
        return hash(self.source) + hash(self.target)


class Graph(object):
    DIRECTED = "directed"
    UNDIRECTED = "undirected"

    def __init__(self, all_nodes):
        if len(all_nodes) > 0:
            identifier_class = all_nodes[0].identifier.__class__

            for node in all_nodes:
                checkInstance(node.identifier, identifier_class)
                checkEqual(node.finalized, True)

        self.all_nodes = all_nodes
        self.indexes = {}

        for node in self.all_nodes:
            self.indexes[node.identifier] = node

    def _links(self, direction):
        links = set()

        for node in self.all_nodes:
            for descendant in node.descendants:
                if direction == self.DIRECTED:
                    link = DirectedLink(node.identifier, descendant.identifier)
                elif direction == self.UNDIRECTED:
                    link = UndirectedLink(node.identifier, descendant.identifier)
                else:
                    raise ValueError(direction)

                links.add(link)

        logging.debug("links(%s): nodes=%d -> links=%d." % (direction, len(self.all_nodes), len(links)))
        return links

    def _sub_graph(self, direction, identifiers):
        gb = GraphBuilder(direction)

        for link in self.links():
            if link.source in identifiers and link.target in identifiers:
                gb.add(link.source, [link.target])

        return gb.build()


    def neighbourhood(self, node_or_identifier, limit=None, inclusive=False):
        if isinstance(node_or_identifier, Node):
            node = node_or_identifier
        else:
            node = self.indexes[node_or_identifier]

        call_id = "%s-%s-%s" % (node.identifier, limit, inclusive)
        out = set()
        logging.debug("%s: queing %s" % (call_id, node))
        processing = [(node, 0)]
        processed = {}
        first = True

        while len(processing) > 0:
            current_node, current_limit = processing.pop()

            if current_node in processed:
                assert processed[current_node] > current_limit

            if not first:
                processed[current_node] = current_limit

            if first:
                if inclusive:
                    out.add(current_node)
                    logging.debug("%s: adding %s (first+inclusive)" % (call_id, current_node))
            else:
                out.add(current_node)
                logging.debug("%s: adding %s" % (call_id, current_node))

            first = False
            descendant_limit = current_limit + 1

            for descendant in current_node.descendants:
                logging.debug("%s: explor %s (%s)" % (call_id, descendant, descendant_limit))

                if (descendant not in processed or processed[descendant] > descendant_limit) \
                    and (limit is None or descendant_limit <= limit):
                    logging.debug("%s: queing %s" % (call_id, descendant))
                    processing.append((descendant, descendant_limit))

        return out

    def nodes(self, identifiers):
        return set([self.indexes[i] for i in identifiers])

    def page_rank(self, damping=0.85, epsilon=0.005, epochs=50, biases={}):
        assert damping >= 0.0 and damping <= 1.0
        initial = 1.0 / len(self.all_nodes)
        weights = {n.identifier: initial for n in self.all_nodes}

        for i in xrange(0, epochs):
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
            direct_neighbours = self.neighbourhood(node.identifier, 1, False)

            if len(direct_neighbours) > 0:
                contribution = weights[node.identifier] / len(direct_neighbours)

                for direct_neighbour in direct_neighbours:
                    intermediaries[direct_neighbour.identifier] += contribution
            else:
                leak += weights[node.identifier]

        for k, v in biases.iteritems():
            assert v >= 0.0 and v <= 1.0
            intermediaries[k] += v

        assert len(weights) == len(intermediaries)
        damping_constant = (1.0 - damping) / len(self.all_nodes)
        leak_constant = (damping * leak) / len(self.all_nodes)
        out = {}

        for k, v in intermediaries.iteritems():
            out[k] = damping_constant + leak_constant + (damping * v)

        if len(biases) > 0:
            total = sum(out.values())
            scale = 1.0 / total
            out = {k: scale * v for k, v in out.iteritems()}

        return out

    def _delta(self, a, b):
        total = 0.0

        for k, v in a.iteritems():
            total += abs(v - b[k])

        return total


class UndirectedGraph(Graph):
    def __init__(self, all_nodes):
        super(UndirectedGraph, self).__init__(all_nodes)
        self.clustering_coefficients = {}

        for node in self.all_nodes:
            direct_neighbours = self.neighbourhood(node, 1)
            neighbours = [n for n in direct_neighbours]
            count = 0

            for i, neighbour in enumerate(neighbours):
                for j in xrange(i, len(neighbours)):
                    if neighbours[j] in neighbour.descendants:
                        count += 1

            total = len(neighbours)
            logging.debug("%s: count %d, total %d" % (node.identifier, count, total))
            cc = 0.0

            if count > 0:
                if total > 1:
                    cc = count / (float(total) * (total - 1) / 2.0)

            self.clustering_coefficients[node.identifier] = cc

    def links(self):
        return self._links(self.UNDIRECTED)

    def sub_graph(self):
        return self._sub_graph(self.UNDIRECTED)


class DirectedGraph(Graph):
    def __init__(self, all_nodes):
        super(DirectedGraph, self).__init__(all_nodes)
        self.clustering_coefficients = {}

        for node in self.all_nodes:
            direct_neighbours = self.neighbourhood(node, 1)
            neighbours = [n for n in direct_neighbours]
            count = 0

            for i, neighbour in enumerate(neighbours):
                for j in xrange(0, len(neighbours)):
                    if neighbours[j] in neighbour.descendants:
                        count += 1

            total = len(neighbours)
            logging.debug("%s: count %d, total %d" % (node.identifier, count, total))
            cc = 0.0

            if count > 0:
                if total > 1:
                    cc = count / (float(total) * (total - 1))

            self.clustering_coefficients[node.identifier] = cc

    def links(self):
        return self._links(self.DIRECTED)

    def sub_graph(self):
        return self._sub_graph(self.DIRECTED)


class GraphBuilder:
    def __init__(self, direction):
        self.direction = direction
        self.nodes = {}

        if direction != Graph.DIRECTED and direction != Graph.UNDIRECTED:
            raise ValueError(direction)

    def add(self, identifier, descendants=[]):
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


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

        for existing in self.descendants:
            checkNotEqual(descendant.identifier, existing.identifier)

        self.descendants.add(descendant)

    def finalize(self):
        self.finalized = True
        return self


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

    def neighbourhood(self, node_or_identifier, limit=None):
        if isinstance(node_or_identifier, Node):
            node = node_or_identifier
        else:
            node = self.indexes[node_or_identifier]

        out = set()
        processing = [(node, 0)]

        while len(processing) > 0:
            current_node, current_limit = processing.pop()
            out.add(current_node)

            for descendant in current_node.descendants:
                if descendant not in out \
                    and (limit is None or current_limit + 1 <= limit):
                    processing.append((descendant, current_limit + 1))

        return out

    def nodes(self, identifiers):
        return set([self.indexes[i] for i in identifiers])


class UndirectedGraph(Graph):
    def __init__(self, all_nodes):
        super(UndirectedGraph, self).__init__(all_nodes)
        self.clustering_coefficients = {}

        for node in self.all_nodes:
            direct_neighbours = self.neighbourhood(node, 1)
            direct_neighbours.remove(node)
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


class DirectedGraph(Graph):
    def __init__(self, all_nodes):
        super(DirectedGraph, self).__init__(all_nodes)
        self.clustering_coefficients = {}

        for node in self.all_nodes:
            direct_neighbours = self.neighbourhood(node, 1)
            direct_neighbours.remove(node)
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


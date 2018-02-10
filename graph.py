#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import pdb

from check import checkInstance, checkNotInstance, checkNotEqual


class Node:
    # Note: Want instance based equals/hash.
    def __init__(self, identifier):
        #for descendant in descendants:
        #    checkInstance(descendant, Node)
        #    checkNotEqual(identifier, descendant.identifier)

        self.identifier = checkNotInstance(identifier, Node)
        self.descendants = set()#checkInstance(descendants, set)

    def add_descendant(self, descendant):
        checkInstance(descendant, Node)
        checkNotEqual(self.identifier, descendant.identifier)

        for existing in self.descendants:
            checkNotEqual(descendant.identifier, existing.identifier)

        print("add: %s" % descendant.identifier)
        self.descendants.add(descendant)


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


class Graph:
    def __init__(self, nodes):
        if len(nodes) > 0:
            identifier_class = nodes[0].identifier.__class__

            for node in nodes:
                assert isinstance(node.identifier, identifier_class)

        self.nodes = nodes

    def get_links(self, directed=True):
        links = set()

        for node in self.nodes:
            for descendant in node.descendants:
                if directed:
                    link = DirectedLink(node.identifier, descendant.identifier)
                else:
                    link = UndirectedLink(node.identifier, descendant.identifier)

                links.add(link)

        logging.debug("get_links(%s): nodes=%d -> links=%d." % (directed, len(self.nodes), len(links)))
        return links


class GraphBuilder:
    def __init__(self):
        self.nodes = {}

    def add(self, identifier, descendants=[]):
        for descendant in descendants:
            if descendant not in self.nodes:
                self.nodes[descendant] = Node(descendant)

        if identifier not in self.nodes:
            self.nodes[identifier] = Node(identifier)

        for descendant in descendants:
            logging.debug("%s -> %s" % (identifier, descendant))
            self.nodes[identifier].add_descendant(self.nodes[descendant])

        logging.debug("%s: %s" % (identifier, ",".join([str(d.identifier) for d in self.nodes[identifier].descendants])))

    def build(self):
        return Graph(self.nodes.values())


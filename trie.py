#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging


class Node:
    def __init__(self, children, final):
        self.children = children
        self.final = final

    def __str__(self):
        return "Node{%s, %s}" % (self.children, self.final)

    def __repr__(self):
        return str(self)


def build(terms, tokenizer=lambda t: iter(t)):
    trie_dict = {}
    finals = {}

    for term in terms:
        d = trie_dict
        path = []

        for token in tokenizer(term):
            if token not in d:
                d[token] = {}

            d = d[token]
            path += [token]

        finals[tuple(path)] = True

    logging.debug("build:\n%s\n%s" % (trie_dict, finals))

    def _build(d, path=[]):
        iterator = d.iteritems
        children = {}

        for token, sub_dict in iterator():
            node = _build(sub_dict, path + [token])
            children[token] = node

        return Node(children, tuple(path) in finals)

    return _build(trie_dict)


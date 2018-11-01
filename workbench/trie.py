#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from pytils import check



class Node:
    def __init__(self, children, final=False, term=None):
        self.children = children
        self.final = final
        self.term = term

        if final and term is None:
            raise ValueError("final must be set with term")
        elif not final and term is not None:
            raise ValueError("final must be set with term")

        self._hash = hash((tuple([(k, v._hash) for k, v in self.children.items()]), final, term))

    def __repr__(self):
        return "Node{%s, %s, %s}" % (self.children, self.final, self.term)

    def __eq__(self, other):
        return self._hash == other._hash

    def __hash__(self):
        return self._hash


def build(terms, equivalences={}, tokenizer=lambda term: iter(term), equivalent_values=lambda token: [str(token)]):
    trie_dict = {}
    finals = {}

    def _build_trie_dict(term_dict):
        for term_path, term in term_dict.items():
            d = trie_dict
            path = []

            for token in tokenizer(term_path):
                if token not in d:
                    d[token] = {}

                d = d[token]
                path += [token]

            if tuple(path) in finals and finals[tuple(path)] != term:
                raise ValueError("duplicate path '%s' for different term '%s'" % (path, term))

            finals[tuple(path)] = term

    _build_trie_dict({t: t for t in terms})
    _build_trie_dict(equivalences)
    logging.debug("build:\n%s\n%s" % (trie_dict, finals))

    def _build(d, path=[]):
        children = {}

        for token, sub_dict in d.items():
            node = _build(sub_dict, path + [token])
            children[token] = node

        if tuple(path) in finals:
            return Node(children, True, finals[tuple(path)])
        else:
            return Node(children)

    return _build(trie_dict)


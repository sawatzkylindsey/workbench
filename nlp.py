#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from nltk.stem import SnowballStemmer
import nltk
import pdb
import re


from check import check_not_empty, check_none, check_instance
from trie import Node


STEMMER = SnowballStemmer("english")
SPLITTER = nltk.word_tokenize


def stem(word):
    return STEMMER.stem(word)


def extract_terms(corpus, terms_trie, lemmatizer=lambda x: x, inflection_recorder=lambda x, y: 0):
    check_instance(terms_trie, Node)
    extracted_terms = set()
    i = 0

    while i < len(corpus):
        span = 1
        node = terms_trie
        lemma = lemmatizer(corpus[i])
        sequence = None

        while lemma in node.children:
            node = node.children[lemma]

            if node.final:
                sequence = corpus[i:i + span]

            if i + span >= len(corpus):
                break

            lemma = lemmatizer(corpus[i + span])
            span += 1

        if sequence is not None:
            lemma_term = Term([lemmatizer(s) for s in sequence])
            inflection_term = Term(sequence)
            extracted_terms.add(lemma_term)
            inflection_recorder(lemma_term, inflection_term)
            i += len(sequence)
        else:
            i += 1

    return extracted_terms


class Term:
    def __init__(self, words):
        self.words = tuple(check_not_empty(words))

    def __len__(self):
        return len(self.words)

    def __iter__(self):
        return iter(self.words)

    def __eq__(self, other):
        return self.words == other.words

    def __hash__(self):
        return hash(self.words)

    def __str__(self):
        return "Term{%s}" % str(self.words)

    def __repr__(self):
        return str(self)

    def __cmp__(self, other):
        return cmp(self.words, other.words)

    def name(self):
        return "-".join(self.words)


class Inflections:
    def __init__(self):
        self.counts = {}
        self.lemma_to_inflection = None
        self.inflection_to_lemma = None

    def record(self, lemma_term, inflection_term):
        check_none(self.lemma_to_inflection)
        check_none(self.inflection_to_lemma)
        logging.debug("record: %s->%s" % (lemma_term, inflection_term))
        check_instance(lemma_term, Term)
        check_instance(inflection_term, Term)

        if lemma_term not in self.counts:
            self.counts[lemma_term] = {}

        count = self.counts[lemma_term].get(inflection_term, 0)
        self.counts[lemma_term][inflection_term] = count + 1

    def _setup_maps(self):
        if self.lemma_to_inflection is None:
            self.lemma_to_inflection = {}
            self.inflection_to_lemma = {}

            for lemma, inflections in self.counts.iteritems():
                tmp = sorted(inflections.iteritems(), key=lambda item: item[1], reverse=True)
                self.lemma_to_inflection[lemma] = tmp[0][0]
                self.inflection_to_lemma[tmp[0][0]] = lemma

    def to_inflection(self, lemma_term):
        self._setup_maps()
        check_instance(lemma_term, Term)
        return self.lemma_to_inflection[lemma_term]

    def to_lemma(self, inflection_term):
        self._setup_maps()
        check_instance(inflection_term, Term)
        return self.inflection_to_lemma[inflection_term]

    def lemma_counts(self):
        return [(lemma, sum(inflections.values())) for lemma, inflections in self.counts.iteritems()]

    def inflection_counts(self):
        return [(lemma, inflection, count) for lemma, inflections in self.counts.iteritems() for inflection, count in inflections.iteritems()]


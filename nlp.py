#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from nltk.stem import SnowballStemmer
import pdb
import re


from check import checkNotEmpty
from trie import build as trie_build


STEMMER = SnowballStemmer("english")
SPLITTER = lambda text: re.findall(r"\w+", text, re.UNICODE)


def stem(word):
    return STEMMER.stem(word)


def extract_terms(corpus, terms, lemmatizer, inflection_recorder=lambda x, y: 0):
    extracted_terms = set()
    trie = trie_build(terms, tokenizer=lambda t: iter(t))

    for i in xrange(0, len(corpus)):
        span = 1
        node = trie
        lemma = lemmatizer(corpus[i])

        while lemma in node.children:
            node = node.children[lemma]

            if node.final:
                sequence = corpus[i:i + span]
                lemma_term = Term([lemmatizer(s) for s in sequence])
                inflection_term = Term(sequence)
                extracted_terms.add(lemma_term)
                inflection_recorder(lemma_term, inflection_term)

            if i + span + 1 >= len(corpus):
                break

            lemma = lemmatizer(corpus[i + span])
            span += 1

    return extracted_terms


class Term:
    def __init__(self, words):
        self.words = tuple(checkNotEmpty(words))

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

    def record(self, lemma_term, inflection_term):
        logging.debug("record: %s->%s" % (lemma_term, inflection_term))
        assert isinstance(lemma_term, Term)
        assert isinstance(inflection_term, Term)

        if lemma_term not in self.counts:
            self.counts[lemma_term] = {}

        count = self.counts[lemma_term].get(inflection_term, 0)
        self.counts[lemma_term][inflection_term] = count + 1


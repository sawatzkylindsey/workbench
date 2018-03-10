#!/usr/bin/python
# -*- coding: utf-8 -*-

from csv import reader as csv_reader
import logging
import pdb
from rake_nltk import Rake
import re


import nlp


CANONICALIZER = nlp.stem


class GlossaryCsv:
    def __init__(self):
        self.terms = set()
        self.cooccurrences = {}
        self.inflections = None

    def parse(self, input_text):
        assert len(self.terms) == 0
        assert len(self.cooccurrences) == 0
        assert self.inflections is None
        self.inflections = nlp.Inflections()

        with open(input_text, "r") as fh:
            for row in csv_reader(fh):
                row = [unicode(item, "utf-8") for item in row]
                term = self._glossary_term(row)
                inflection = self._glossary_inflection(row)
                self.terms.add(term)
                self.inflections.record(term, inflection)
                self.cooccurrences[term] = set()

        with open(input_text, "r") as fh:
            for row in csv_reader(fh):
                row = [unicode(item, "utf-8") for item in row]
                term = self._glossary_term(row)
                reference_terms = nlp.extract_terms(corpus=nlp.SPLITTER(row[1].strip().lower()),
                                                    terms=self.terms,
                                                    lemmatizer=CANONICALIZER,
                                                    inflection_recorder=self.inflections.record)

                for reference_term in reference_terms:
                    if term != reference_term:
                        self.cooccurrences[term].add(reference_term)

    def _glossary_term(self, row):
        assert len(row) == 2, row
        lemmas = [CANONICALIZER(item) for item in nlp.SPLITTER(row[0].strip().lower())]
        return nlp.Term(lemmas)

    def _glossary_inflection(self, row):
        assert len(row) == 2, row
        inflections = [item for item in nlp.SPLITTER(row[0].strip().lower())]
        return nlp.Term(inflections)


class LineText:
    MINIMUM_TERM_LENGTH = 5

    def __init__(self):
        self.terms = set()
        self.cooccurrences = {}
        self.inflections = None

    def parse(self, input_texts):
        assert len(self.terms) == 0
        assert len(self.cooccurrences) == 0
        assert self.inflections is None
        self.inflections = nlp.Inflections()
        link_counts = {}
        conditional_inflections = {}

        for input_text in input_texts:
            with open(input_text, "r") as fh:
                rake = Rake()
                terms = rake.extract_keywords_from_sentences(fh.readlines())
                pdb.set_trace()

            self._parse(input_text, link_counts, conditional_inflections)

        flat_link_counts = [(term_a, term_b, count) for term_a, linked_terms in link_counts.iteritems() for term_b, count in linked_terms.iteritems()]

        with open("asdf.csv", "w") as fh:
            fh.write("a,b,count\n")

            for item in sorted(flat_link_counts, key=lambda item: item[2], reverse=True):
                fh.write(item[0].name())
                fh.write(",")
                fh.write(item[1].name())
                fh.write(",")
                fh.write(str(item[2]))
                fh.write("\n")

        for term_a, linked_terms in link_counts.iteritems():
            is_first = True

            for term_b, count in linked_terms.iteritems():
                if count >= 2:
                    if term_a not in self.cooccurrences:
                        self.cooccurrences[term_a] = set()

                    self.cooccurrences[term_a].add(term_b)

                    if is_first:
                        is_first = False

                        for infl in conditional_inflections[term_a]:
                            self.inflections.record(term_a, nlp.Term([infl]))

                    for infl in conditional_inflections[term_b]:
                        self.inflections.record(term_b, nlp.Term([infl]))

    def _parse(self, input_text, link_counts, conditional_inflections):
        with open(input_text, "r") as fh:
            for line in fh:
                print(line)
                tokens = [unicode(re.sub(r'[^A-Za-z]', r'', item.strip().lower()), "utf-8") for item in line.split(" ")]
                print(tokens)
                terms = [CANONICALIZER(item) for item in tokens]

                for inflection_a in tokens:
                    if len(inflection_a) >= self.MINIMUM_TERM_LENGTH:
                        for inflection_b in tokens:
                            if len(inflection_b) >= self.MINIMUM_TERM_LENGTH and \
                                inflection_a != inflection_b:
                                lemma_a = CANONICALIZER(inflection_a)
                                lemma_b = CANONICALIZER(inflection_b)

                                if lemma_a != lemma_b:
                                    term_a = nlp.Term([lemma_a])
                                    term_b = nlp.Term([lemma_b])

                                    if term_a not in link_counts:
                                        link_counts[term_a] = {}

                                    if term_b not in link_counts[term_a]:
                                        link_counts[term_a][term_b] = 0

                                    link_counts[term_a][term_b] += 1

                                    if term_a not in conditional_inflections:
                                        conditional_inflections[term_a] = []

                                    if term_b not in conditional_inflections:
                                        conditional_inflections[term_b] = []

                                    conditional_inflections[term_a] += [inflection_a]
                                    conditional_inflections[term_b] += [inflection_b]
                                    #self.inflections.record(term_a, nlp.Term([inflection_a]))
                                    #self.inflections.record(term_b, nlp.Term([inflection_b]))


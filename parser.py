#!/usr/bin/python
# -*- coding: utf-8 -*-

from csv import reader as csv_reader
import logging
import pdb


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
                self.terms.add(term)
                self.cooccurrences[term] = set()

        with open(input_text, "r") as fh:
            for row in csv_reader(fh):
                row = [unicode(item, "utf-8") for item in row]
                term = self._glossary_term(row)
                reference_terms = nlp.extract_terms(corpus=nlp.SPLITTER(row[1].strip()),
                                                    terms=self.terms,
                                                    lemmatizer=CANONICALIZER,
                                                    inflection_recorder=self.inflections.record)

                for reference_term in reference_terms:
                    if term != reference_term:
                        self.cooccurrences[term].add(reference_term)

    def _glossary_term(self, row):
        assert len(row) == 2, row
        lemmas = [CANONICALIZER(item) for item in nlp.SPLITTER(row[0].strip())]
        return nlp.Term(lemmas)


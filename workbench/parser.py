#!/usr/bin/python
# -*- coding: utf-8 -*-

from csv import reader as csv_reader
import json
import logging
import math
import os
import pdb
from pytils import check
from rake_nltk import Rake
import re
import requests
import textrank
import wikipediaapi


from workbench import errors
import workbench.nlp as nlp
from workbench.trie import build as build_trie


CANONICALIZER = nlp.stem
CLEANER = lambda text: text.strip()

GLOSSARY_CSV = ("gc", "glossary_csv")
WIKIPEDIA_ARTICLES_LIST = ("wal", "wikipedia_articles_list")
TERMS_CONTENT_TEXT = ("tct", "terms_content_text")
FORMATS = [
    GLOSSARY_CSV,
    WIKIPEDIA_ARTICLES_LIST,
    TERMS_CONTENT_TEXT,
]
wikipedia = wikipediaapi.Wikipedia("en", extract_format=wikipediaapi.ExtractFormat.NATLANG)


def file_to_content(input_file):
    with open(input_file, "r", encoding="utf-8") as fh:
        for line in fh.readlines():
            yield CLEANER(line)


def csv_to_content(input_file):
    with open(input_file, "r", encoding="utf-8") as fh:
        for row in csv_reader(fh):
            yield [CLEANER(cell) for cell in row]


def parse_input(input_stream, input_format, window=1, paragraphs=False):
    if format_matches(input_format, GLOSSARY_CSV):
        parser = GlossaryCsv()
    elif format_matches(input_format, WIKIPEDIA_ARTICLES_LIST):
        parser = WikipediaArticlesList(window, paragraphs)
    elif format_matches(input_format, TERMS_CONTENT_TEXT):
        parser = TermsContentText(window, paragraphs)
    else:
        raise ValueError("Unknown input format '%s'." % str(input_format))

    parser.parse(input_stream)
    return parser


def format_matches(input_format, FORMAT):
    if input_format == FORMAT:
        return True

    return any([input_format == f for f in FORMAT])


def str_kv(value):
    if isinstance(value, dict):
        return {str(k): str_kv(v) for k, v in value.items()}
    else:
        return str(value)


class GlossaryCsv:
    def __init__(self):
        self.terms = set()
        self.cooccurrences = {}
        self.inflections = nlp.Inflections()

    def parse(self, input_stream):
        if len(self.terms) > 0:
            raise ValueError("cannot invoke parse() multiple times for GlossaryCsv parser.")

        for row in input_stream:
            term = self._glossary_term(row)
            inflection = self._glossary_inflection(row)
            self.terms.add(term)
            self.inflections.record(term, inflection)
            self.cooccurrences[term] = {}

        terms_trie = build_trie(self.terms)

        for row in input_stream:
            term = self._glossary_term(row)

            for sentence in nlp.split_sentences(row[1]):
                reference_terms = nlp.extract_terms(corpus=sentence,
                                                    terms_trie=terms_trie,
                                                    lemmatizer=CANONICALIZER,
                                                    inflection_recorder=self.inflections.record)

                for reference_term in reference_terms:
                    if term != reference_term:
                        if reference_term not in self.cooccurrences[term]:
                            self.cooccurrences[term][reference_term] = []

                        self.cooccurrences[term][reference_term] += [sentence]

    def _glossary_term(self, row):
        assert len(row) == 2, row
        lemmas = [CANONICALIZER(item) for item in nlp.split_words(row[0])]
        return nlp.Term(lemmas)

    def _glossary_inflection(self, row):
        assert len(row) == 2, row
        inflections = [item for item in nlp.split_words(row[0])]
        return nlp.Term(inflections)


class WikipediaArticlesList:
    SECTION_BLACKLIST = [
        "Notes",
        "References",
        "Further reading",
        "External links",
        "See also",
    ]

    def __init__(self, window, paragraphs):
        assert window is None or window >= 1, window
        # If paragraphs is set, then window must be 1
        assert window == 1 or not paragraphs
        self.window = window
        self.paragraphs = paragraphs
        self.top_percent = 0.05
        self.terms = set()
        self.cooccurrences = {}
        self.inflections = nlp.Inflections()

    def parse(self, input_stream):
        pages = []
        parse_terms = set()

        for line in input_stream:
            for item in line.split("."):
                page_id = item.strip()

                if page_id != "":
                    if os.path.exists(self._page_file_contents(page_id)):
                        with open(self._page_file_contents(page_id), "r", encoding="utf-8") as fh:
                            page_content = fh.read()
                        with open(self._page_file_links(page_id), "r", encoding="utf-8") as fh:
                            page_links = [l.strip() for l in fh.readlines()]
                    else:
                        split = page_id.split("#")
                        page = wikipedia.page(split[0])

                        try:
                            if not page.exists():
                                raise errors.Invalid("Missing wikipedia page '%s'." % split[0])
                        except requests.exceptions.ReadTimeout as e:
                            raise errors.Invalid("Missing wikipedia page '%s'." % split[0])

                        if len(split) == 1:
                            page_content = check.check_not_empty(CLEANER(page.summary))
                        else:
                            page_content = ""

                        for section in (page.section_titles if len(split) == 1 else split[1:]):
                            if section not in self.SECTION_BLACKLIST:
                                logging.debug("Page '%s' using section '%s'." % (page_id, section))
                                raw_section_content = page.section_by_title(section).text

                                if raw_section_content is not None and len(raw_section_content) > 0:
                                    section_content = CLEANER(raw_section_content)

                                    if len(section_content) > 0:
                                        page_content += " " + section_content

                        page_links = [CLEANER(l) for l in page.links]

                    pages += [page_id]

                    if not os.path.exists(self._page_file_contents(page_id)):
                        with open(self._page_file_contents(page_id), "w", encoding="utf-8") as fh:
                            fh.write(page_content.replace("\n", "\n\n"))
                        with open(self._page_file_links(page_id), "w", encoding="utf-8") as fh:
                            for link in page_links:
                                fh.write("%s\n" % link)

                    page_terms = set()

                    for page_term in self._extract_links(page_id, page_links, page_content):
                        page_terms.add(page_term)

                    for term in page_terms:
                        self.terms.add(term)

                        if term not in parse_terms:
                            logging.debug("Page '%s' adding term '%s'." % (page_id, term))
                            parse_terms.add(term)
                            self.inflections.record(term, term)

        terms_trie = build_trie(parse_terms)

        for page_id in pages:
            with open(self._page_file_contents(page_id), "r", encoding="utf-8") as fh:
                page_content = fh.read()

            sentences = nlp.split_sentences(page_content, self.paragraphs)
            maximum_offset = math.ceil(float(len(sentences)) / self.window)

            for offset in range(0, maximum_offset):
                # List of lists                    vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
                sub_corpus = [word for sentence in sentences[offset:offset + self.window] for word in sentence]
                reference_terms = nlp.extract_terms(corpus=sub_corpus,
                                                    terms_trie=terms_trie,
                                                    lemmatizer=CANONICALIZER,
                                                    inflection_recorder=self.inflections.record)
                logging.debug("Page '%s' reference terms: %s" % (page_id, reference_terms))

                for a in reference_terms:
                    for b in reference_terms:
                        if a != b:
                            if a not in self.cooccurrences:
                                self.cooccurrences[a] = {}

                            if b not in self.cooccurrences[a]:
                                self.cooccurrences[a][b] = []

                            #self.cooccurrences[a].add(b)
                            self.cooccurrences[a][b] += [sub_corpus]

    def _automatic_term_extract(self, page_id, content):
        page_name = page_id.replace(" ", "_")
        terms_textrank = set(textrank.extract_key_phrases(content, self.top_percent))
        logging.debug("textranks: %s" % terms_textrank)
        #with open("textrank.%s.txt" % page_name, "w", encoding="utf-8") as fh:
        #    for term in terms_textrank:
        #        fh.write("%s\n" % term.replace(" ", "-"))
        rake = Rake()
        rake.extract_keywords_from_text(content)
        rake_ranked_phrases = rake.get_ranked_phrases()
        #with open("rake.%s.txt" % page_name, "w", encoding="utf-8") as fh:
        #    for term in rake_ranked_phrases:
        #        fh.write("%s\n" % nlp.Term(term.split(" ")).name())
        terms_rake = set(rake_ranked_phrases[:max(int(len(rake_ranked_phrases) * self.top_percent), 1)])
        logging.debug("rakes: %s" % terms_textrank)
        intersection_terms = terms_textrank.intersection(terms_rake)
        logging.debug("intersection: %s" % intersection_terms)
        return [nlp.Term(t.split(" ")) for t in filter(lambda term: term, intersection_terms)]

    def _extract_links(self, page_id, links, content):
        out = []

        for link in links:
            if link in content:
                term = nlp.Term([CANONICALIZER(t) for t in nlp.split_words(link)])

                if term == nlp.Term(["1"]):
                    pass
                else:
                    out += [term]

        return out

    def _page_file_contents(self, page_id):
        return "wiki/.wiki-%s.contents-txt" % page_id.replace(" ", "_")

    def _page_file_links(self, page_id):
        return "wiki/.wiki-%s.links-txt" % page_id.replace(" ", "_")


class TermsContentText:
    TERMS_CONTENT_SEPARATOR = "terms_content_separator"
    EQUIVALENCE_OPERATOR = "<="

    def __init__(self, window, paragraphs):
        assert window >= 1, window
        # If paragraphs is set, then window must be 1
        assert window == 1 or not paragraphs
        self.window = window
        self.paragraphs = paragraphs
        self.terms = set()
        self.equivalences = {}
        self.cooccurrences = {}
        self.inflections = nlp.Inflections()

    def _add_equivalence(self, equivalence, term):
        if equivalence in self.equivalences and self.equivalences[equivalence] != term:
            raise ValueError("equivalence '%s' already mapped to term '%s'" % (equivalence.name(), term.name()))

        self.equivalences[equivalence] = term
        current = equivalence

        while current in self.equivalences:
            current = self.equivalences[current]

            if current == equivalence:
                raise ValueError("cycle on '%s'" % equivalence.name())

    def parse(self, input_stream):
        content_point = None

        for item in input_stream:
            index = item.index(TermsContentText.TERMS_CONTENT_SEPARATOR)

            for sentence in nlp.split_sentences(item[0:index]):
                if TermsContentText.EQUIVALENCE_OPERATOR in sentence:
                    index = sentence.index(TermsContentText.EQUIVALENCE_OPERATOR)
                    left = sentence[:index]
                    right = sentence[index + 1:]
                    term = nlp.Term([CANONICALIZER(word) for word in left])
                    self.terms.add(term)
                    inflection = nlp.Term(left)
                    self.inflections.record(term, inflection)
                    # equivalence
                    equivalence_term = nlp.Term([CANONICALIZER(word) for word in right])
                    self._add_equivalence(equivalence_term, term)
                    equivalence_inflection = nlp.Term(right)
                    self._add_equivalence(equivalence_inflection, term)
                # Just silently ignore empty term definitions.
                elif len(sentence) > 0:
                    term = nlp.Term([CANONICALIZER(word) for word in sentence])
                    self.terms.add(term)
                    inflection = nlp.Term(sentence)
                    self.inflections.record(term, inflection)

            terms_trie = build_trie(self.terms, self.equivalences)
            sentences = nlp.split_sentences(item[len(TermsContentText.TERMS_CONTENT_SEPARATOR) + index:], self.paragraphs)
            maximum_offset = math.ceil(float(len(sentences)) / self.window)

            for offset in range(0, maximum_offset):
                # List of lists                    vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
                sub_corpus = [word for sentence in sentences[offset:offset + self.window] for word in sentence]
                reference_terms = nlp.extract_terms(corpus=sub_corpus,
                                                    terms_trie=terms_trie,
                                                    lemmatizer=CANONICALIZER,
                                                    inflection_recorder=self.inflections.record)

                for a in reference_terms:
                    for b in reference_terms:
                        if a != b:
                            if a not in self.cooccurrences:
                                self.cooccurrences[a] = {}

                            if b not in self.cooccurrences[a]:
                                self.cooccurrences[a][b] = []

                            self.cooccurrences[a][b] += [sub_corpus]


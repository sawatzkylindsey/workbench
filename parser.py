#!/usr/bin/python
# -*- coding: utf-8 -*-

from csv import reader as csv_reader
import json
import logging
import pdb
from rake_nltk import Rake
import re
import textrank
import wikipedia


from check import check_not_empty
import nlp
from trie import build as build_trie


CANONICALIZER = nlp.stem

GLOSSARY_CSV = "glossary_csv"
LINE_TEXT = "line_text"
WIKIPEDIA_ARTICLES_LIST = "wikipedia_articles_list"
FORMATS = [
    GLOSSARY_CSV,
    LINE_TEXT,
    WIKIPEDIA_ARTICLES_LIST
]


def parse_input(input_texts, input_format):
    if input_format == GLOSSARY_CSV:
        parser = GlossaryCsv()
    elif input_format == LINE_TEXT:
        parser = LineText()
    elif input_format == WIKIPEDIA_ARTICLES_LIST:
        parser = WikipediaArticlesList()
    else:
        raise ValueError("Unknown input format '%s'." % input_format)

    for input_text in input_texts:
        parser.parse(input_text)

    #logging.debug(json.dumps(str_kv(parser.inflections.counts), indent=2, sort_keys=True))
    #logging.debug(json.dumps({str(k): str(v) for k, v in parser.inflections.counts.items()}, indent=2, sort_keys=True)) 
    return parser


def str_kv(value):
    if isinstance(value, dict):
        return {str(k): str_kv(v) for k, v in value.iteritems()}
    else:
        return str(value)


class GlossaryCsv:
    def __init__(self):
        self.terms = set()
        self.cooccurrences = {}
        self.inflections = nlp.Inflections()

    def parse(self, input_text):
        if len(self.terms) > 0:
            raise ValueError("cannot invoke parse() multiple times for GlossaryCsv parser.")

        with open(input_text, "r") as fh:
            for row in csv_reader(fh):
                row = [unicode(item, "utf-8") for item in row]
                term = self._glossary_term(row)
                inflection = self._glossary_inflection(row)
                self.terms.add(term)
                self.inflections.record(term, inflection)
                self.cooccurrences[term] = set()

        terms_trie = build_trie(self.terms)

        with open(input_text, "r") as fh:
            for row in csv_reader(fh):
                row = [unicode(item, "utf-8") for item in row]
                term = self._glossary_term(row)
                reference_terms = nlp.extract_terms(corpus=nlp.SPLITTER(row[1].strip().lower()),
                                                    terms_trie=terms_trie,
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


class WikipediaArticlesList:
    SECTION_BLACKLIST = [
        u"Notes",
        u"References",
        u"Further reading",
        u"External links",
        u"See also",
    ]

    def __init__(self):
        self.terms = set()
        self.cooccurrences = {}
        self.inflections = nlp.Inflections()

    def parse(self, input_text):
        pages = {}
        parse_terms = set()

        with open(input_text, "r") as fh:
            for line in fh.readlines():
                page_id = unicode(line.strip(), "utf-8")
                split = page_id.split("#")
                page = wikipedia.page(split[0])

                if len(split) == 1:
                    page_content = self._strip(check_not_empty(page.summary).lower())
                else:
                    page_content = u""

                for section in (page.sections if len(split) == 1 else split[1:]):
                    if section not in self.SECTION_BLACKLIST:
                        logging.debug("Page '%s' using section '%s'." % (page_id, section))
                        raw_section_content = page.section(section)

                        if raw_section_content is not None and len(raw_section_content) > 0:
                            section_content = self._strip(raw_section_content)

                            if len(section_content) > 0:
                                page_content += u" " + section_content

                pages[page_id] = page_content
                page_terms = self._extract_terms(page_content)

                for term in page_terms:
                    self.terms.add(term)

                    if term not in parse_terms:
                        logging.debug("Page '%s' adding term '%s'." % (page_id, term))
                        parse_terms.add(term)
                        self.inflections.record(term, term)

        for page_id, page_content in pages.iteritems():
            for line in page_content.split("."):
                terms_trie = build_trie(parse_terms)
                reference_terms = nlp.extract_terms(corpus=nlp.SPLITTER(line), \
                                                    terms_trie=terms_trie)
                logging.debug("Page '%s' reference terms: %s" % (page_id, reference_terms))

                for a in reference_terms:
                    for b in reference_terms:
                        if a != b:
                            if a not in self.cooccurrences:
                                self.cooccurrences[a] = set()

                            self.cooccurrences[a].add(b)

    def _strip(self, content):
        return u" ".join(re.findall(r"(\w+|\.)", content, re.UNICODE))

    def _extract_terms(self, content):
        terms_textrank = set(textrank.extract_key_phrases(content))
        logging.debug("textranks: %s" % terms_textrank)
        rake = Rake()
        rake.extract_keywords_from_text(content)
        rake_ranked_phrases = rake.get_ranked_phrases()
        terms_rake = set(rake_ranked_phrases[:int(len(rake_ranked_phrases) * 0.3)])
        logging.debug("rakes: %s" % terms_textrank)
        return [nlp.Term(t.split(" ")) for t in terms_textrank.intersection(terms_rake)]


class LineText:
    MINIMUM_TERM_LENGTH = 5

    def __init__(self):
        self.terms = set()
        self.cooccurrences = {}
        self.inflections = nlp.Inflections()

    def parse(self, input_texts):
        link_counts = {}
        conditional_inflections = {}

        for input_text in input_texts:
            with open(input_text, "r") as fh:
                rake = Rake()
                terms = rake.extract_keywords_from_sentences(fh.readlines())

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


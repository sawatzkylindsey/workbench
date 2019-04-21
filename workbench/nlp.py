#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from nltk.stem import SnowballStemmer
import nltk
import random
import pdb
from pytils import base, check
import re


from workbench.trie import Node


SENTENCE_BREAK = "SB%s" % random.randrange(1000)
QUESTION_BREAK = "QB%s" % random.randrange(1000)
EXCLAMATION_BREAK = "EB%s" % random.randrange(1000)
PARAGRAPH_BREAK = "PB%s" % random.randrange(1000)
STEMMER = SnowballStemmer("english")
STEM_BANNED = {
    # Avoid stemming "Ares", as it will become "are".
    "ares": True,
}
SENTENCE_SEPARATORS = set([SENTENCE_BREAK, QUESTION_BREAK, EXCLAMATION_BREAK])
STEM_EXCEPTIONS = {
    "laterization": "laterization",
    "laterizations": "laterization",
    "learning": "learning",
    "learnings": "learning",
    "organization": "organization",
    "organizations": "organization",
    "organizer": "organizer",
    "organizers": "organizer",
    "development": "development",
    "developments": "development",
    "developmental": "development",
    "developmentals": "development",
    "appropriate": "appropriate",
    "appropriates": "appropriate",
    "appropriation": "appropriate",
    "appropriations": "appropriate",
    "respondent": "respondent",
    "respondents": "respondent",
    "internalize": "internalize",
    "internalizes": "internalize",
    "operant": "operant",
    "operants": "operant",
    "accommodation": "accommodation",
    "accommodations": "accommodation",
    "compensation": "compensation",
    "compensations": "compensation",
    "preoperational": "preoperational",
    "preoperationals": "preoperational",
    "perception": "perception",
    "perceptions": "perception",
    "refugee": "refugee",
    "refugees": "refugee",
    "attention": "attention",
    "attentions": "attention",
    "reflective": "reflective",
    "reflectives": "reflective",
    "attachment": "attachment",
    "attachments": "attachment",
    "plasticity": "plasticity",
    "plasticities": "plasticity",
    "plasticitys": "plasticity",
    "generativity": "generativity",
    "generativities": "generativity",
    "generativitys": "generativity",
    "integrity": "integrity",
    "integrities": "integrity",
    "integritys": "integrity",
    "interference": "interference",
    "interferences": "interference",
    "image": "image",
    "images": "image",
    "exploration": "exploration",
    "explorations": "exploration",
    "consequence": "consequence",
    "consequences": "consequence",
    "arousal": "arousal",
    "arousals": "arousal",
    "discrimination": "discrimination",
    "discriminations": "discrimination",
    "prompt": "prompt",
    "prompts": "prompt",
    "production": "production",
    "productions": "production",
    "initiative": "initiative",
    "initiatives": "initiative",
    "conservation": "conservation",
    "conservations": "conservation",
    "experimentation": "experimentation",
    "experimentations": "experimentation",
    "instruction": "instruction",
    "instructions": "instruction",
    "instructional": "instruction",
    "instructionals": "instruction",
    "tracking": "tracking",
    "trackings": "tracking",
    "processing": "processing",
    "processings": "processing",
    "shaping": "shaping",
    "shapings": "shaping",
    "decay": "decay",
    "decays": "decay",
    "retrieval": "retrieval",
    "retrievals": "retrieval",
    "chunking": "chunking",
    "chunkings": "chunkings",
    "construction": "construction",
    "constructions": "construction",
    "transfer": "transfer",
    "transfers": "transfer",
    "aversive": "aversive",
    "aversives": "aversive",
    "objective": "objective",
    "objectives": "objective",
    "contiguity": "contiguity",
    "contiguitys": "contiguity",
    "contiguities": "contiguity",
    "reversibility": "reversibility",
    "reversibilitys": "reversibility",
    "reversibilities": "reversibility",
    "priming": "priming",
    "primings": "priming",
    "commitment": "commitment",
    "commitments": "commitment",
    "pragmatic": "pragmatics",
    "pragmatics": "pragmatics",
    "overregularize": "overregularize",
    "overregularizes": "overregularize",
    #"withitness": "",
}
TAGS = {
    "CC": True,
    "CD": False,
    "DT": False,
    "EX": False,
    "FW": True,
    "IN": True,
    "JJ": True,
    "JJR": True,
    "JJS": True,
    "LS": False,
    "MD": False,
    "NN": True,
    "NNS": True,
    "NNP": True,
    "NNPS": True,
    "PDT": False,
    "POS": False,
    "PRP": False,
    "PRP$": False,
    "RB": False,
    "RBR": False,
    "RBS": False, #
    "RP": False, #
    "SYM": False,
    "TO": True,
    "UH": False,
    "VB": False,
    "VBD": False,
    "VBG": False,
    "VBN": False,
    "VBP": False,
    "VBZ": False,
    "WDT": False,
    "WP": False,
    "WP$": False,
    "WRB": False,
}


def stem(word):
    stemable = re.match("[a-zA-Z]{1}[a-z]{2,}$", word) is not None

    if stemable and word.lower() not in STEM_BANNED:
        if word.lower() in STEM_EXCEPTIONS:
            return STEM_EXCEPTIONS[word.lower()]
        else:
            return STEMMER.stem(word.lower())

    return word


def split_words(corpus):
    return re.findall("[\w\.<=]+", re.sub("(\s*\n\s*){2,}", " %s " % PARAGRAPH_BREAK,
        re.sub("!", " %s " % EXCLAMATION_BREAK, re.sub("\?", " %s " % QUESTION_BREAK, re.sub("\.(?!\w+)", " %s " % SENTENCE_BREAK, corpus)))))


def split_sentences(corpus, paragraphs=False):
    words = split_words(corpus)
    sentences = []
    sentence = []

    for word in words:
        if paragraphs and word == PARAGRAPH_BREAK:
            sentences += [sentence]
            sentence = []
        elif not paragraphs and word in SENTENCE_SEPARATORS:
            sentences += [sentence]
            sentence = []
        else:
            if word not in SENTENCE_SEPARATORS and word != PARAGRAPH_BREAK:
                sentence += [word]

    if len(sentence) != 0:
        sentences += [sentence]

    return sentences


def extract_terms(corpus, terms_trie, lemmatizer=lambda x: x, inflection_recorder=lambda x, y: 0):
    check.check_instance(terms_trie, Node)
    tags = [tag for word, tag in nltk.pos_tag(corpus)]
    assert len(tags) == len(corpus)
    extracted_terms = set()
    i = 0

    while i < len(corpus):
        span = 1
        node = terms_trie
        lemma = lemmatizer(corpus[i])
        tag = tags[i]
        sequence = None
        matched_term = None

        while lemma in node.children:
            if tag in TAGS and TAGS[tag]:
                node = node.children[lemma]

                if node.final:
                    sequence = corpus[i:i + span]
                    matched_term = node.term

                if i + span >= len(corpus):
                    break

                lemma = lemmatizer(corpus[i + span])
                tag = tags[i + span]
                span += 1
            else:
                break

        if sequence is not None:
            inflection_term = Term(sequence)
            extracted_terms.add(matched_term)
            inflection_recorder(matched_term, inflection_term)
            i += len(sequence)
        else:
            i += 1

    return extracted_terms


class Term(base.Comparable):
    def __init__(self, words):
        super(Term, self).__init__()
        self.words = tuple(check.check_not_empty(words))
        self._hash = None

    def __len__(self):
        return len(self.words)

    def __iter__(self):
        return iter(self.words)

    def __eq__(self, other):
        return self.words == other.words

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(self.words)

        return self._hash

    def __repr__(self):
        return "Term{%s}" % str(self.words)

    def _comparator(self, fn, other):
        return fn(self.words, other.words)

    def name(self):
        return " ".join(self.words)

    def transform(self, function):
        return Term([function(word) for word in self.words])

    def lower(self):
        return self.transform(lambda w: w.lower())


class Inflections:
    def __init__(self):
        self.counts = {}
        self.inflections = {}
        self.lemma_to_inflection = None

    def combine(self, other):
        combination = Inflections()

        for lemma_term, inflection_counts in self.counts.items():
            for inflection_term, count in inflection_counts.items():
                combination.record(lemma_term, inflection_term, count)

        for lemma_term, inflection_counts in other.counts.items():
            for inflection_term, count in inflection_counts.items():
                combination.record(lemma_term, inflection_term, count)

        return combination

    def record(self, lemma_term, inflection_term, number=1):
        check.check_none(self.lemma_to_inflection)
        logging.debug("record: %s->%s" % (lemma_term, inflection_term))
        check.check_instance(lemma_term, Term)
        check.check_instance(inflection_term, Term)

        if lemma_term not in self.counts:
            self.counts[lemma_term] = {}

        count = self.counts[lemma_term].get(inflection_term, 0)
        self.counts[lemma_term][inflection_term] = count + number

        if inflection_term not in self.inflections:
            self.inflections[inflection_term] = lemma_term
        else:
            if self.inflections[inflection_term] != lemma_term:
                raise ValueError("Inflection '%s' maps to multiple lemmas: [%s, %s]." % (inflection_term, self.inflections[inflection_term], lemma_term))

    def _finalize(self):
        if self.lemma_to_inflection is None:
            self.lemma_to_inflection = {}

            for lemma, inflections in self.counts.items():
                tmp = sorted(inflections.items(), key=lambda item: item[1], reverse=True)
                self.lemma_to_inflection[lemma] = tmp[0][0]

    def to_dominant_inflection(self, lemma_term):
        self._finalize()
        check.check_instance(lemma_term, Term)
        return self.lemma_to_inflection[lemma_term]

    def to_lemma(self, inflection_term):
        self._finalize()
        check.check_instance(inflection_term, Term)

        try:
            return self.inflections[inflection_term]
        except KeyError as e:
            return self.inflections[inflection_term.lower()]

    def lemma_counts(self):
        return [(lemma, sum(inflections.values())) for lemma, inflections in self.counts.items()]

    def inflection_counts(self):
        return [(lemma, inflection, count) for lemma, inflections in self.counts.items() for inflection, count in inflections.items()]


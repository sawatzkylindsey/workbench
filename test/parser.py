#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import os
from pytils.invigilator import create_suite
from unittest import TestCase


from workbench.nlp import Term
from workbench.parser import GLOSSARY_CSV, TERMS_CONTENT_TEXT, WIKIPEDIA_ARTICLES_LIST
from workbench.parser import parse_input, TermsContentText


logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().setLevel(logging.DEBUG)
root_handler = logging.FileHandler("%s.test.log" % os.path.splitext(os.path.basename(__file__))[0])
root_handler.setFormatter(logging.Formatter("%(levelname)s %(module)s..%(funcName)s: %(message)s"))
logging.getLogger().addHandler(root_handler)


class Tests(TestCase):
    def test_glossary_csv(self):
        stream = [
            ["Apple", "Goat explores. xyz querty apples crater . Explore apples"],
            ["Goat", "nadda."],
            ["explore", "Crater sphere\ntermy."],
            ["crater Sphere", "nadda."]
        ]
        parse = parse_input(stream, GLOSSARY_CSV)
        self.assertEqual(parse.terms, set([
            Term(["appl"]),
            Term(["goat"]),
            Term(["explor"]),
            Term(["crater", "sphere"]),
        ]))
        self.assertEqual(parse.cooccurrences[Term(["appl"])], {
            Term(["goat"]): ["Goat explores".split()],
            Term(["explor"]): ["Goat explores".split(), "Explore apples".split()],
        })
        self.assertEqual(parse.cooccurrences[Term(["goat"])], {})
        self.assertEqual(parse.cooccurrences[Term(["explor"])], {
            Term(["crater", "sphere"]): ["Crater sphere termy".split()],
        })
        self.assertEqual(parse.cooccurrences[Term(["crater", "sphere"])], {})

    def test_wikipedia_articles_list(self):
        # This test will rely on network connectivity to first locally save the wikipedia articles.
        stream = [
            "Paleozoic",
            "Gravity"
        ]
        parse = parse_input(stream, WIKIPEDIA_ARTICLES_LIST)
        self.assertIn(Term(["phanerozo"]), parse.terms)
        self.assertIn(Term(["permian"]), parse.terms)
        self.assertIn(Term(["gravit"]), parse.terms)
        self.assertIn(Term(["mass"]), parse.terms)

        self.assertGreater(len(parse.terms), 200)
        self.assertGreaterEqual(len(parse.cooccurrences[Term(["phanerozo"])][Term(["permian"])]), 1)
        self.assertEqual(len(parse.cooccurrences[Term(["permian"])][Term(["phanerozo"])]), len(parse.cooccurrences[Term(["phanerozo"])][Term(["permian"])]))
        self.assertGreaterEqual(len(parse.cooccurrences[Term(["gravit"])][Term(["mass"])]), 1)
        self.assertEqual(len(parse.cooccurrences[Term(["mass"])][Term(["gravit"])]), len(parse.cooccurrences[Term(["gravit"])][Term(["mass"])]))

        self.assertEqual(parse.inflections.to_dominant_inflection(Term(["phanerozo"])), Term(["phanerozoic"]))
        self.assertEqual(parse.inflections.to_dominant_inflection(Term(["gravit"])), Term(["gravitational"]))

    def test_term_content_text(self):
        stream = ["Apple. Goat .\nexplore. \ncrater Sphere" \
            + TermsContentText.TERMS_CONTENT_SEPARATOR \
            + "Apples something explores and goats.\nxyz querty apples crater. Explore Crater sphere\ntermy . explores apples"]
        parse = parse_input(stream, TERMS_CONTENT_TEXT)
        self.assertEqual(parse.terms, set([
            Term(["appl"]),
            Term(["goat"]),
            Term(["explor"]),
            Term(["crater", "sphere"]),
        ]))
        self.assertEqual(parse.cooccurrences[Term(["appl"])], {
            Term(["goat"]): ["Apples something explores and goats".split()],
            Term(["explor"]): ["Apples something explores and goats".split(), "explores apples".split()],
        })
        self.assertEqual(parse.cooccurrences[Term(["goat"])], {
            Term(["appl"]): ["Apples something explores and goats".split()],
            Term(["explor"]): ["Apples something explores and goats".split()],
        })
        self.assertEqual(parse.cooccurrences[Term(["explor"])], {
            Term(["appl"]): ["Apples something explores and goats".split(), "explores apples".split()],
            Term(["goat"]): ["Apples something explores and goats".split()],
            Term(["crater", "sphere"]): ["Explore Crater sphere termy".split()],
        })
        self.assertEqual(parse.cooccurrences[Term(["crater", "sphere"])], {
            Term(["explor"]): ["Explore Crater sphere termy".split()],
        })

    def test_term_content_text_one_sentence(self):
        stream = ["Apple. Goat .\nexplore. \ncrater Sphere" \
            + TermsContentText.TERMS_CONTENT_SEPARATOR \
            + "Apples something explores and goats."]

        for window in range(1, 4):
            parse = parse_input(stream, TERMS_CONTENT_TEXT, window)
            self.assertEqual(parse.terms, set([
                Term(["appl"]),
                Term(["goat"]),
                Term(["explor"]),
                Term(["crater", "sphere"]),
            ]), "window %d" % window)
            self.assertEqual(parse.cooccurrences[Term(["appl"])], {
                Term(["goat"]): ["Apples something explores and goats".split()],
                Term(["explor"]): ["Apples something explores and goats".split()],
            }, "window %d" % window)
            self.assertEqual(parse.cooccurrences[Term(["goat"])], {
                Term(["appl"]): ["Apples something explores and goats".split()],
                Term(["explor"]): ["Apples something explores and goats".split()],
            }, "window %d" % window)
            self.assertEqual(parse.cooccurrences[Term(["explor"])], {
                Term(["appl"]): ["Apples something explores and goats".split()],
                Term(["goat"]): ["Apples something explores and goats".split()],
            }, "window %d" % window)

    def test_term_content_text_paragraphs(self):
        stream = ["Apple. Goat .\n\nexplore. \n\ncrater\n\nSphere" \
            + TermsContentText.TERMS_CONTENT_SEPARATOR \
            + "Apples something explores and goats.\n\nxyz querty apples crater. Explore Crater sphere\n\ntermy . explores apples"]
        parse = parse_input(stream, TERMS_CONTENT_TEXT, 1, True)
        self.assertEqual(parse.terms, set([
            Term(["appl"]),
            Term(["goat"]),
            Term(["explor"]),
            Term(["crater", "sphere"]),
        ]))
        self.assertEqual(parse.cooccurrences[Term(["appl"])], {
            Term(["goat"]): ["Apples something explores and goats".split()],
            Term(["explor"]): ["Apples something explores and goats".split(), "xyz querty apples crater Explore Crater sphere".split(), "termy explores apples".split()],
            Term(["crater", "sphere"]): ["xyz querty apples crater Explore Crater sphere".split()],
        })
        self.assertEqual(parse.cooccurrences[Term(["goat"])], {
            Term(["appl"]): ["Apples something explores and goats".split()],
            Term(["explor"]): ["Apples something explores and goats".split()],
        })
        self.assertEqual(parse.cooccurrences[Term(["explor"])], {
            Term(["appl"]): ["Apples something explores and goats".split(), "xyz querty apples crater Explore Crater sphere".split(), "termy explores apples".split()],
            Term(["goat"]): ["Apples something explores and goats".split()],
            Term(["crater", "sphere"]): ["xyz querty apples crater Explore Crater sphere".split()],
        })
        self.assertEqual(parse.cooccurrences[Term(["crater", "sphere"])], {
            Term(["appl"]): ["xyz querty apples crater Explore Crater sphere".split()],
            Term(["explor"]): ["xyz querty apples crater Explore Crater sphere".split()],
        })

    def test_term_content_text_paragraphs_carriage_return(self):
        stream = ["Apple. Goat .\r\n\r\nexplore. \r\n\r\ncrater\r\n\r\nSphere" \
            + TermsContentText.TERMS_CONTENT_SEPARATOR \
            + "Apples something explores and goats.\r\n\r\nxyz querty apples crater. Explore Crater sphere\r\n\r\ntermy . explores apples"]
        parse = parse_input(stream, TERMS_CONTENT_TEXT, 1, True)
        self.assertEqual(parse.terms, set([
            Term(["appl"]),
            Term(["goat"]),
            Term(["explor"]),
            Term(["crater", "sphere"]),
        ]))
        self.assertEqual(parse.cooccurrences[Term(["appl"])], {
            Term(["goat"]): ["Apples something explores and goats".split()],
            Term(["explor"]): ["Apples something explores and goats".split(), "xyz querty apples crater Explore Crater sphere".split(), "termy explores apples".split()],
            Term(["crater", "sphere"]): ["xyz querty apples crater Explore Crater sphere".split()],
        })
        self.assertEqual(parse.cooccurrences[Term(["goat"])], {
            Term(["appl"]): ["Apples something explores and goats".split()],
            Term(["explor"]): ["Apples something explores and goats".split()],
        })
        self.assertEqual(parse.cooccurrences[Term(["explor"])], {
            Term(["appl"]): ["Apples something explores and goats".split(), "xyz querty apples crater Explore Crater sphere".split(), "termy explores apples".split()],
            Term(["goat"]): ["Apples something explores and goats".split()],
            Term(["crater", "sphere"]): ["xyz querty apples crater Explore Crater sphere".split()],
        })
        self.assertEqual(parse.cooccurrences[Term(["crater", "sphere"])], {
            Term(["appl"]): ["xyz querty apples crater Explore Crater sphere".split()],
            Term(["explor"]): ["xyz querty apples crater Explore Crater sphere".split()],
        })

def tests():
    return create_suite(Tests)


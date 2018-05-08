#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import os
from pytils.invigilator import create_suite
from unittest import TestCase


from workbench.nlp import Term
from workbench.parser import GLOSSARY_CSV, TERMS_CONTENT_TEXT, WIKIPEDIA_ARTICLES_LIST
from workbench.parser import parse_input, TermsContentText
from workbench.processor import FeConverter, GLOSSARY


logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().setLevel(logging.DEBUG)
root_handler = logging.FileHandler("%s.test.log" % os.path.splitext(os.path.basename(__file__))[0])
root_handler.setFormatter(logging.Formatter("%(levelname)s %(module)s..%(funcName)s: %(message)s"))
logging.getLogger().addHandler(root_handler)


class Tests(TestCase):
    def test_glossary_1(self):
        fec = FeConverter()
        (output_stream, output_format) = fec.from_text("=:bob:=bill.=:bill:=moot.", GLOSSARY)
        self.assertEqual(output_format, GLOSSARY_CSV)
        self.assertEqual(output_stream, [
            ["bob", "bill."],
            ["bill", "moot."]
        ])

    def test_glossary_2(self):
        fec = FeConverter()
        (output_stream, output_format) = fec.from_text("=:bob:= bill.=:bill:= moot.", GLOSSARY)
        self.assertEqual(output_format, GLOSSARY_CSV)
        self.assertEqual(output_stream, [
            ["bob", "bill."],
            ["bill", "moot."]
        ])

    def test_glossary_3(self):
        fec = FeConverter()
        (output_stream, output_format) = fec.from_text("=:bob:= bill with some extra stuff.=:bill:= moot.=:whatever:= bob is a cool whatever guy.", GLOSSARY)
        self.assertEqual(output_format, GLOSSARY_CSV)
        self.assertEqual(output_stream, [
            ["bob", "bill with some extra stuff."],
            ["bill", "moot."],
            ["whatever", "bob is a cool whatever guy."]
        ])


def tests():
    return create_suite(Tests)


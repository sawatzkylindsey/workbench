#!/usr/bin/python
# -*- coding: utf-8 -*-

#from argparse import ArgumentParser
#from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
#from http.server import BaseHTTPRequestHandler, HTTPServer
#import json
import logging
#import mimetypes
#import os
import pdb
import re
#import SocketServer
#import sys
#import urllib


#from workbench.graph import GraphBuilder, Graph
#from workbench.nlp import Term
from workbench import errors
from workbench import parser
from pytils.log import setup_logging, user_log
from workbench.termnet import build as build_termnet


CONTENT_TERMS = "content-terms"
GLOSSARY = "glossary"
WIKIPEDIA = "wikipedia"


class FeConverter:
    def __init__(self):
        self.cache = {}

    def from_data(self, data):
        try:
            web_format = data["format"][0]
        except KeyError as e:
            raise errors.Invalid("Submission invalid - missing 'format'.").with_traceback(e.__traceback__)

        try:
            content = data["content"][0]
        except KeyError as e:
            raise errors.Invalid("Submission invalid - missing 'content'.").with_traceback(e.__traceback__)

        if web_format == CONTENT_TERMS:
            try:
                terms = data["terms"][0]
            except KeyError as e:
                raise errors.Invalid("Submission invalid - missing 'terms'.").with_traceback(e.__traceback__)

            input_text = "%s %s. %s" % (terms, parser.TermsContentText.TERMS_CONTENT_SEPARATOR, content)
            return self.from_text(input_text, web_format)
        else:
            return self.from_text(content, web_format)

    def from_text(self, input_text, input_format):
        logging.debug("%s: %s" % (str(input_format), input_text))

        #if (input_text, input_format) in self.cache:
        #    return self.cache[(input_text, input_format)]

        if input_format == GLOSSARY:
            output_format = parser.GLOSSARY_CSV
            output_stream = []
            working_text = input_text
            left = None
            right = None

            while len(working_text) > 0:
                if left is None:
                    term_m = re.search("=:(.*?):=(.*)", working_text)

                    if term_m is not None:
                        left = term_m.group(1)
                        working_text = working_text[len(left) + 4:]
                    else:
                        raise ValueError("cannot parse: %s" % working_text)
                else:
                    definition_m = re.search("(.*?)(=:.*:=.*)", working_text, re.DOTALL)

                    if definition_m is not None:
                        right = definition_m.group(1)
                        working_text = working_text[len(right):]
                    else:
                        right = working_text
                        working_text = ""

                if left is not None and right is not None:
                    output_stream += [[parser.CLEANER(left), parser.CLEANER(right)]]
                    left = None
                    right = None
        else:
            if input_format == CONTENT_TERMS:
                output_stream = [parser.CLEANER(input_text)]
                output_format = parser.TERMS_CONTENT_TEXT
            elif input_format == WIKIPEDIA:
                output_stream = [input_text]
                output_format = parser.WIKIPEDIA_ARTICLES_LIST
            else:
                raise ValueError("unknown format '%s'" % input_format)

        #termnet = build_termnet(input_stream, input_format)
        #self.cache[(input_text, input_format)] = input_stream
        return (output_stream, output_format)

    #def from_stream(self, input_stream, input_format):
    #    return build_termnet(input_stream, input_format)


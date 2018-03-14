#!/usr/bin/python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import mimetypes
import os
import pdb
import SocketServer
import sys


from graph import GraphBuilder, Graph
from nlp import Term
import parser
from pytils.log import setup_logging, user_log
from termnet import Termnet


#worker = termnet.Termnet("glossary1.csv", termnet.GLOSSARY_CSV)
#worker = termnet.Termnet("glossary2.csv", termnet.GLOSSARY_CSV)
#worker = termnet.Termnet("Astronomy.csv", termnet.GLOSSARY_CSV)
#worker = termnet.Termnet(["cog.txt", "direct.txt", "mayer.txt", "reduce.txt"], termnet.LINE_TEXT)
#worker = termnet.Termnet(["astro1.txt", "astro2.txt", "astro3.txt"], termnet.LINE_TEXT)
global net
net = None


class ServerHandler(BaseHTTPRequestHandler):
    def _set_headers(self, ct):
        self.send_response(200)
        self.send_header('Content-type', ct)
        self.end_headers()

    def do_GET(self):
        logging.debug("GET %s" % self.path)
        file_path = os.path.join(".", "javascript", self.path.strip("/"))

        if os.path.exists(file_path):
            mimetype, _ = mimetypes.guess_type(self.path)
            self._set_headers(mimetype)

            with open(file_path, "r") as fh:
                for line in fh:
                    self.wfile.write(line)
        else:
            self.send_error(404,'File Not Found: %s ' % self.path)

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        logging.debug("POST %s: '%s'" % (self.path, post_data))

        if self.path == "/reset":
            net.reset()

        term = None

        if post_data != "":
            term = Term(post_data.lower().split("-"))

        thing = net.mark(term)
        self._set_headers("application/json")
        self.wfile.write(json.dumps(thing))
        ## Doesn't do anything with posted data
        #self._set_headers()
        #self.wfile.write("<html><body><h1>POST!</h1></body></html>")


def run(port):
    server_address = ('', port)
    httpd = HTTPServer(server_address, ServerHandler)
    user_log.info('Starting httpd %d...' % port)
    httpd.serve_forever()


if __name__ == "__main__":
    ap = ArgumentParser(prog="server")
    ap.add_argument("--verbose", "-v",
                        default=False,
                        action="store_true",
                        # Unfortunately, logging in python 2.7 doesn't have
                        # a built-in way to log asynchronously.
                        help="Turn on verbose logging.  " + \
                        "**This will SIGNIFICANTLY slow down the program.**")
    ap.add_argument("-p", "--port", default=8888, type=int)
    ap.add_argument("-f", "--input-format", default=parser.WIKIPEDIA_ARTICLES_LIST, help="One of %s" % parser.FORMATS)
    ap.add_argument("input_text", nargs="+")
    args = ap.parse_args()
    setup_logging(".%s.%s.log" % (os.path.splitext(os.path.basename(__file__))[0], "-".join([a.replace(".", "_") for a in args.input_text])), args.verbose, True)
    logging.debug(args)

    parse = parser.parse_input(args.input_text, args.input_format)
    builder = GraphBuilder(Graph.UNDIRECTED)

    for k, v in parse.cooccurrences.iteritems():
        builder.add(parse.inflections.to_inflection(k), [parse.inflections.to_inflection(i) for i in v])

    net = Termnet(builder.build())
    run(args.port)


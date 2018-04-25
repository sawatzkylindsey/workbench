#!/usr/bin/python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
#from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import mimetypes
import os
import pdb
#import SocketServer
import sys
import urllib


from workbench.graph import GraphBuilder, Graph
from workbench.nlp import Term
import workbench.parser
from pytils.log import setup_logging, user_log
from workbench.termnet import build as build_termnet


#worker = termnet.Termnet("glossary1.csv", termnet.GLOSSARY_CSV)
#worker = termnet.Termnet("glossary2.csv", termnet.GLOSSARY_CSV)
#worker = termnet.Termnet("Astronomy.csv", termnet.GLOSSARY_CSV)
#worker = termnet.Termnet(["cog.txt", "direct.txt", "mayer.txt", "reduce.txt"], termnet.LINE_TEXT)
#worker = termnet.Termnet(["astro1.txt", "astro2.txt", "astro3.txt"], termnet.LINE_TEXT)
#global net
#net = None
#global previous
#previous = None


class ServerHandler(BaseHTTPRequestHandler):
    #def __init__(self, termnet, *args, **kwargs):
    #    super(ServerHandler, self).__init__(*args, **kwargs)
    #    pdb.set_trace()
    #    self.server.termnet = check_not_none(termnet)
    #    self.previous = None

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
                    self._write(line)
        else:
            self.send_error(404,'File Not Found: %s ' % self.path)

    def do_POST(self):
        post_data = self._read()
        logging.debug("POST %s: '%s'" % (self.path, post_data))
        query = None

        if post_data != "":
            query = urllib.parse.parse_qs(post_data)

        #logging.debug(query)
        out = self.__getattribute__(self.path[1:].replace("/", "_"))(query)

        if out == None:
            out = {}

        self._set_headers("application/json")
        self._write(json.dumps(out))

    def term(self, query):
        return Term(query["term"][0].lower().split(" "))

    def mode(self, query):
        return query["mode"][0]

    def polarity(self, query):
        return query["polarity"][0]

    def reset(self, query):
        self.server.termnet.reset()

    def influence_configure(self, query):
        polarity = self.polarity(query)
        mode = self.mode(query)

        if polarity == "positive":
            self.server.termnet.positive_influence = self._influence_mode(mode)
        elif polarity == "negative":
            self.server.termnet.negative_influence = self._influence_mode(mode)
        else:
            raise ValueError("invalid polarity: %s" % polarity)

        return self.server.termnet.display(self.server.previous_term)

    def _influence_mode(self, mode):
        if mode == "none":
            return lambda x: 0
        elif mode == "linear":
            return lambda x: x
        elif mode == "cubic":
            return lambda x: x**3
        elif mode == "exponential":
            return lambda x: 2**x

    def influence(self, query):
        polarity = self.polarity(query)
        mode = self.mode(query)
        term = self.term(query)

        if polarity == "positive":
            if mode == "add":
                self.server.termnet.positive_add(term)
            elif mode == "remove":
                self.server.termnet.positive_remove(term)
            else:
                raise ValueError("invalid mode: %s" % mode)
        elif polarity == "negative":
            if mode == "add":
                self.server.termnet.negative_add(term)
            elif mode == "remove":
                self.server.termnet.negative_remove(term)
            else:
                raise ValueError("invalid mode: %s" % mode)
        else:
            raise ValueError("invalid polarity: %s" % polarity)

        return self.server.termnet.display(self.server.previous_term)

    def search(self, query):
        term = self.term(query)
        self.server.termnet.mark(term)
        return self.server.termnet.display(self.server.previous_term)

    def neighbourhood(self, query):
        term = None

        if query is not None:
            try:
                term = self.term(query)
            except KeyError as e:
                pass

            self.server.previous_term = term

        return self.server.termnet.display(term)

    def ignore(self, query):
        term = self.term(query)
        mode = self.mode(query)

        if mode == "add":
            self.server.termnet.ignore_add(term)
        elif mode == "remove":
            self.server.termnet.ignore_remove(term)
        else:
            raise ValueError("invalid mode: %s" % mode)

        return self.server.termnet.display(self.server.previous_term)

    def _read(self):
        content_length = int(self.headers["Content-Length"])
        return self.rfile.read(content_length).decode("utf-8")

    def _write(self, text):
        self.wfile.write(text.encode("utf-8"))


def run(port, termnet):
    server_address = ('', port)
    httpd = HTTPServer(server_address, ServerHandler)
    httpd.termnet = termnet
    httpd.previous_term = None
    user_log.info('Starting httpd %d...' % port)
    httpd.serve_forever()


def main(argv):
    ap = ArgumentParser(prog="server")
    ap.add_argument("--verbose", "-v",
                        default=False,
                        action="store_true",
                        # Unfortunately, logging in python 2.7 doesn't have
                        # a built-in way to log asynchronously.
                        help="Turn on verbose logging.  " + \
                        "**This will SIGNIFICANTLY slow down the program.**")
    ap.add_argument("-p", "--port", default=8888, type=int)
    ap.add_argument("-f", "--input-format", default=workbench.parser.WIKIPEDIA, help="One of %s" % workbench.parser.FORMATS)
    ap.add_argument("input_text", nargs="+")
    args = ap.parse_args(argv)
    setup_logging(".%s.log" % os.path.splitext(os.path.basename(__file__))[0], args.verbose, True)
    logging.debug(args)
    termnet = build_termnet(args.input_text, args.input_format)
    run(args.port, termnet)


if __name__ == "__main__":
    main(sys.argv[1:])


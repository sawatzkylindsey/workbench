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
from workbench.termnet import build as build_termnet, TermnetSession


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
    #    termnet_session = check_not_none(termnet)
    #    self.previous = None
    def _session(self, session_key):
        if session_key not in self.server.sessions:
            self.server.sessions[session_key] = TermnetSession(self.server.termnet)

        return self.server.sessions[session_key]

    def _set_headers(self, ct):
        self.send_response(200)
        self.send_header('Content-type', ct)
        self.end_headers()

    def do_GET(self):
        (path, session, content) = self._read()
        logging.debug("GET %s session: %s" % (path, session))
        file_path = os.path.join(".", "javascript", path.strip("/"))

        if os.path.exists(file_path):
            mimetype, _ = mimetypes.guess_type(path)
            self._set_headers(mimetype)

            with open(file_path, "r") as fh:
                for line in fh:
                    self._write(line)
        else:
            self.send_error(404,'File Not Found: %s ' % path)

    def do_POST(self):
        (path, session_key, content) = self._read()
        logging.debug("POST %s session: %s content: %s" % (path, session_key, content))
        termnet_session = self._session(session_key)
        out = self.__getattribute__(self.path[1:].replace("/", "_"))(termnet_session, content)

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

    def reset(self, termnet_session, query):
        termnet_session.reset()

    def influence_configure(self, termnet_session, query):
        polarity = self.polarity(query)
        mode = self.mode(query)

        if polarity == "positive":
            termnet_session.positive_influence = self._influence_mode(mode)
        elif polarity == "negative":
            termnet_session.negative_influence = self._influence_mode(mode)
        else:
            raise ValueError("invalid polarity: %s" % polarity)

        return termnet_session.display_previous()

    def _influence_mode(self, mode):
        if mode == "none":
            return lambda x: 0
        elif mode == "linear":
            return lambda x: x
        elif mode == "cubic":
            return lambda x: x**3
        elif mode == "exponential":
            return lambda x: 2**x

    def influence(self, termnet_session, query):
        polarity = self.polarity(query)
        mode = self.mode(query)
        term = self.term(query)

        if polarity == "positive":
            if mode == "add":
                termnet_session.positive_add(term)
            elif mode == "remove":
                termnet_session.positive_remove(term)
            else:
                raise ValueError("invalid mode: %s" % mode)
        elif polarity == "negative":
            if mode == "add":
                termnet_session.negative_add(term)
            elif mode == "remove":
                termnet_session.negative_remove(term)
            else:
                raise ValueError("invalid mode: %s" % mode)
        else:
            raise ValueError("invalid polarity: %s" % polarity)

        return termnet_session.display_previous()

    def search(self, termnet_session, query):
        term = self.term(query)
        termnet_session.mark(term)
        return termnet_session.display_previous()

    def neighbourhood(self, termnet_session, query):
        term = None

        if query is not None:
            try:
                term = self.term(query)
            except KeyError as e:
                pass

        return termnet_session.display(term)

    def ignore(self, termnet_session, query):
        term = self.term(query)
        mode = self.mode(query)

        if mode == "add":
            termnet_session.ignore_add(term)
        elif mode == "remove":
            termnet_session.ignore_remove(term)
        else:
            raise ValueError("invalid mode: %s" % mode)

        return termnet_session.display_previous()

    def _read(self):
        url = urllib.parse.urlparse(self.path)
        session_key = self.headers["Session-Key"]
        content_params = {}

        if "Content-Length" in self.headers:
            content_length = int(self.headers["Content-Length"])
            content_data = self.rfile.read(content_length).decode("utf-8")
            content_params = urllib.parse.parse_qs(content_data)

        return (url.path, session_key, content_params)

    def _write(self, text):
        self.wfile.write(text.encode("utf-8"))


def run(port, termnet):
    server_address = ('', port)
    httpd = HTTPServer(server_address, ServerHandler)
    httpd.termnet = termnet
    httpd.sessions = {}
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


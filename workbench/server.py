#!/usr/bin/python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import mimetypes
import os
import pdb
import random
from socketserver import ThreadingMixIn
import sys
from threading import Thread
import urllib


from workbench import errors
from workbench.handler import errorhandler
from workbench.graph import GraphBuilder, Graph
from workbench.nlp import Term
from workbench import parser
from pytils.log import setup_logging, user_log
from workbench.termnet import TermnetSession
from workbench.termnet import build as build_termnet
from workbench.processor import FeConverter


class ServerHandler(BaseHTTPRequestHandler):
    def _set_headers(self, content_type, others={}):
        self.send_response(200)
        self.send_header('Content-type', content_type)

        for key, value in others.items():
            self.send_header(key, value)

        self.end_headers()

    @errorhandler
    def do_GET(self):
        (path, session_key, data) = self._read_request()
        logging.debug("GET %s session_key: %s" % (path, session_key))
        file_path = os.path.join(".", "javascript", path.strip("/"))
        logging.debug(file_path)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            mimetype, _ = mimetypes.guess_type(path)

            if mimetype is None:
                mimetype = "text/plain"

            self._set_headers(mimetype)
            encode = "text" in mimetype
            self._read_write_file(file_path, encode)
        else:
            raise errors.NotFound(path)

    def _read_write_file(self, file_path, encode=True):
        if encode:
            with open(file_path, "r") as fh:
                self._write(fh.read())
        else:
            with open(file_path, "rb") as fh:
                self.wfile.write(fh.read())

    def _write(self, content):
        self.wfile.write(content.encode("utf-8"))

    @errorhandler
    def do_POST(self):
        (path, session_key, data) = self._read_request()
        logging.debug("POST %s session: %s data: %s" % (path, session_key, data))

        if path.startswith("/termnet.html"):
            self._set_headers("text/html")
            (input_stream, input_format) = self.server.fe_converter.from_data(data)
            termnet = build_termnet(input_stream, input_format, int(data["window"][0]), int(data["keep"][0]))
            termnet_session = TermnetSession(termnet)
            self.server.sessions[data["sessionKey"][0]] = termnet_session
            self._read_write_file("./javascript/termnet.html")
        else:
            try:
                termnet_session = self.server.sessions[session_key]
            except KeyError as e:
                raise errors.Invalid("Unknown session '%s'." % session_key).with_traceback(e.__traceback__)

            out = self.__getattribute__(self.path[1:].replace("/", "_"))(termnet_session, data)

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

    def properties(self, termnet_session, query):
        return termnet_session.termnet.meta_data()

    def _read_request(self):
        url = urllib.parse.urlparse(self.path)
        session_key = self.headers["Session-Key"]
        data = {}

        if "Content-Length" in self.headers:
            content_length = int(self.headers["Content-Length"])
            content_data = self.rfile.read(content_length).decode("utf-8")
            data = urllib.parse.parse_qs(content_data)

        return (url.path, session_key, data)


def run(port, fe_converter):
    class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
        pass

    #patch_Thread_for_profiling()
    server_address = ('', port)
    httpd = ThreadingHTTPServer(server_address, ServerHandler)
    httpd.daemon_threads = True
    httpd.fe_converter = fe_converter
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
    args = ap.parse_args(argv)
    setup_logging(".%s.log" % os.path.splitext(os.path.basename(__file__))[0], args.verbose, True)
    logging.debug(args)
    fe_converter = FeConverter()
    run(args.port, fe_converter)


def patch_Thread_for_profiling():
    Thread.stats = None
    thread_run = Thread.run

    def profile_run(self):
        import cProfile
        import pstats
        self._prof = cProfile.Profile()
        self._prof.enable()
        thread_run(self)
        self._prof.disable()
        (_, number) = self.name.split("-")
        self._prof.dump_stats("Thread-%.3d-%s.profile" % (int(number), "".join([chr(97 + random.randrange(26)) for i in range(0, 2)])))

    Thread.run = profile_run


if __name__ == "__main__":
    main(sys.argv[1:])


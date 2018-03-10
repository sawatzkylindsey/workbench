#!/usr/bin/python
# -*- coding: utf-8 -*-

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import logging
import os
import mimetypes
import json


from nlp import Term
import termnet

logging.getLogger().setLevel(logging.INFO)
root_handler = logging.FileHandler(".%s.log" % os.path.splitext(os.path.basename(__file__))[0])
root_handler.setFormatter(logging.Formatter("%(levelname)s %(module)s..%(funcName)s: %(message)s"))
logging.getLogger().addHandler(root_handler)

#worker = termnet.Termnet("glossary1.csv", termnet.GLOSSARY_CSV)
#worker = termnet.Termnet("glossary2.csv", termnet.GLOSSARY_CSV)
worker = termnet.Termnet("Astronomy.csv", termnet.GLOSSARY_CSV)
#worker = termnet.Termnet(["cog.txt", "direct.txt", "mayer.txt", "reduce.txt"], termnet.LINE_TEXT)
#worker = termnet.Termnet(["astro1.txt", "astro2.txt", "astro3.txt"], termnet.LINE_TEXT)



class S(BaseHTTPRequestHandler):
    def _set_headers(self, ct):
        self.send_response(200)
        self.send_header('Content-type', ct)
        self.end_headers()

    def do_GET(self):
        print("GET %s" % self.path)
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
        print("POST %s: '%s'" % (self.path, post_data))
        term = None

        if post_data != "":
            term = Term(post_data.lower().split("-"))

        thing = worker.mark(term)
        self._set_headers("application/json")
        self.wfile.write(json.dumps(thing))
        ## Doesn't do anything with posted data
        #self._set_headers()
        #self.wfile.write("<html><body><h1>POST!</h1></body></html>")


def run(server_class=HTTPServer, handler_class=S, port=80):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print 'Starting httpd...'
    httpd.serve_forever()


if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()


#!/usr/bin/python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
import logging
import markdown
import os
import sys


from pytils.log import setup_logging, user_log


html_prefix = """<html>
<head>
</head>
<body>
<div style='width: 800px; margin-right: auto; margin-left: auto;'>
"""
html_suffix = """</div>
</body>
</html>
"""


def main(argv):
    ap = ArgumentParser(prog="markdowner")
    ap.add_argument("--verbose", "-v",
                    default=False,
                    action="store_true",
                    help="Turn on verbose logging.  " + \
                    "**This will SIGNIFICANTLY slow down the program.**")
    ap.add_argument("markdown_file")
    ap.add_argument("output_html")
    args = ap.parse_args(argv)
    setup_logging(".%s.log" % os.path.splitext(os.path.basename(__file__))[0], args.verbose, True)
    logging.debug(args)

    with open(args.markdown_file, "r") as fh:
        html = markdown.markdown(fh.read(), extensions=['extra', 'smarty'], output_format="html5")

    with open(args.output_html, "w") as fh:
        fh.write(html_prefix)
        fh.write(html)
        fh.write(html_suffix)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import sys

USER = "user"
user_log = logging.getLogger(USER)


def setup_logging(root_log_file, verbose):
    logging.getLogger().setLevel(logging.DEBUG)

    if verbose:
        user_log.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        user_log.setLevel(logging.INFO)
        logging.getLogger().setLevel(logging.INFO)

    root_handler = logging.FileHandler(root_log_file)
    root_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logging.getLogger().addHandler(root_handler)

    user_handler = logging.StreamHandler(sys.stdout)
    user_handler.setFormatter(logging.Formatter("%(message)s"))
    user_log.addHandler(user_handler)


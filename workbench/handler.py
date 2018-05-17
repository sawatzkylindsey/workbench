#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import pdb
import traceback

from workbench import errors


MAPPING = {
    errors.NotFound: 404,
    errors.Invalid: 400
}


def errorhandler(function):
    def wrapper(self):
        try:
            function(self)
        except Exception as error:
            error_type = type(error)
            error_message = repr(error)
            traceback_message = "".join(traceback.format_exception(error_type, error, error.__traceback__, chain=False)).strip()
            logging.error("Handling %s.%s\n%s" % (error_type.__module__, error_message, traceback_message))

            if error_type in MAPPING:
                self.send_error(MAPPING[error_type], error_message)
            else:
                self.send_error(500, error_message)

    return wrapper


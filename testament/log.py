import logging
import sys


FMT = "%(asctime)s %(levelname)s %(message)s"


def setup_logging(level=logging.DEBUG, filename=None, stream=sys.stderr):
    if filename:
        logging.basicConfig(filename=filename, level=level, format=FMT)
    else:
        logging.basicConfig(stream=stream, level=level, format=FMT)

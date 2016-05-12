# daisy-extract
# Copyright (C) 2016 James Scholes
# This program is free software, licensed under the terms of the GNU General Public License (version 3 or later).
# See the file LICENSE for more details.

from __future__ import print_function
import argparse
from glob import iglob
import logging
import os
import sys
from xml.etree import ElementTree

from bs4 import BeautifulSoup


__version__ = '0.1'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_stream = logging.StreamHandler(sys.stdout)
log_stream.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(log_stream)


def main():
    logger.info('daisy-extract version {0}'.format(__version__))


if __name__ == '__main__':
    main()

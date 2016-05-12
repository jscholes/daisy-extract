# daisy-extract
# Copyright (C) 2016 James Scholes
# This program is free software, licensed under the terms of the GNU General Public License (version 3 or later).
# See the file LICENSE for more details.

import argparse
import glob
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

NCC_FILENAME = 'NCC.HTML'
MASTER_SMIL_FILENAME = 'MASTER.SMIL'
SMIL_GLOB = '*.[sS][mM][iI][lL]'


def main():
    logger.info('daisy-extract version {0}'.format(__version__))
    cli_args = parse_command_line()
    input_directory = os.path.abspath(cli_args.input_directory)
    output_directory = os.path.abspath(cli_args.output_directory)
    if not os.path.exists(input_directory) or not os.path.isdir(input_directory):
        logger.error('{0} does not exist or is not a directory'.format(input_directory))
        sys.exit(1)

    if not is_supported_daisy_book(input_directory):
        logger.error('The contents of {0} don\'t seem to be a valid DAISY 2.02 book.'.format(input_directory))
        sys.exit(1)

    logger.info('Extracting content from {0} to {1}'.format(input_directory, output_directory))


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-directory', nargs='?', required=True)
    parser.add_argument('-o', '--output-directory', nargs='?', required=True)
    args = parser.parse_args()
    return args


def is_supported_daisy_book(path):
    has_ncc = os.path.exists(os.path.join(path, NCC_FILENAME)) or os.path.exists(os.path.join(path, NCC_FILENAME.lower()))
    smil_files = glob.iglob(os.path.join(path, SMIL_GLOB))
    has_smils = len(list(filter(lambda smil: smil != MASTER_SMIL_FILENAME and smil != MASTER_SMIL_FILENAME.lower(), smil_files))) >= 1
    return has_ncc and has_smils


def make_safe_filename(filename):
    # strip out any disallowed chars and replace with underscores
    disallowed_ascii = [chr(i) for i in range(0, 32)]
    disallowed_chars = '<>:"/\\|?*^{0}'.format(''.join(disallowed_ascii))
    translator = dict((ord(char), '_') for char in disallowed_chars)
    safe_filename = filename.replace(': ', ' - ').translate(translator).rstrip('. ')
    return safe_filename


if __name__ == '__main__':
    main()

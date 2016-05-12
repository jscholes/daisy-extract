# daisy-extract
# Copyright (C) 2016 James Scholes
# This program is free software, licensed under the terms of the GNU General Public License (version 3 or later).
# See the file LICENSE for more details.

from collections import namedtuple
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

BookMetadata = namedtuple('BookMetadata', ('authors', 'title'))


class DaisyExtractError(Exception):
    pass


def main():
    logger.info('daisy-extract version {0}'.format(__version__))
    cli_args = parse_command_line()
    if cli_args.debug:
        logger.setLevel(logging.DEBUG)

    input_directory = os.path.abspath(cli_args.input_directory)
    output_directory = os.path.abspath(cli_args.output_directory)
    if not os.path.exists(input_directory) or not os.path.isdir(input_directory):
        logger.error('{0} does not exist or is not a directory'.format(input_directory))
        sys.exit(1)

    try:
        ncc_path = get_ncc_path(input_directory)
        smil_files = get_smil_filenames(input_directory)
    except DaisyExtractError as e:
        logger.error('The contents of {0} don\'t seem to be a valid DAISY 2.02 book.'.format(input_directory))
        sys.exit(1)

    logger.info('Extracting content from {0} to {1}'.format(input_directory, output_directory))


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-directory', nargs='?', required=True)
    parser.add_argument('-o', '--output-directory', nargs='?', required=True)
    parser.add_argument('-d', '--debug', dest='debug', action='store_true', default=False, help='Enable debug logging')
    args = parser.parse_args()
    return args


def get_ncc_path(directory):
    filenames = (NCC_FILENAME, NCC_FILENAME.lower())
    for filename in filenames:
        path = os.path.join(directory, filename)
        if os.path.exists(path) and os.path.isfile(path):
            logger.debug('Found NCC file: {0}'.format(path))
            return path

    logger.debug('Could not find NCC file in directory')
    raise DaisyExtractError('NCC file not found')


def get_smil_filenames(directory):
    smil_files = list(filter(lambda smil: smil != MASTER_SMIL_FILENAME and smil != MASTER_SMIL_FILENAME.lower(), glob.iglob(os.path.join(directory, SMIL_GLOB))))
    number_of_smil_files = len(smil_files)
    if number_of_smil_files >= 1:
        logger.debug('Found {0} SMIL files in directory'.format(number_of_smil_files))
        return smil_files
    else:
        logger.debug('No SMIL files found in directory')
        raise DaisyExtractError('No SMIL files found')


def make_safe_filename(filename):
    # strip out any disallowed chars and replace with underscores
    disallowed_ascii = [chr(i) for i in range(0, 32)]
    disallowed_chars = '<>:"/\\|?*^{0}'.format(''.join(disallowed_ascii))
    translator = dict((ord(char), '_') for char in disallowed_chars)
    safe_filename = filename.replace(': ', ' - ').translate(translator).rstrip('. ')
    return safe_filename


if __name__ == '__main__':
    main()

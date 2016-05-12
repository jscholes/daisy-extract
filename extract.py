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

from bs4 import BeautifulSoup
from natsort import natsorted


__version__ = '0.1'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_stream = logging.StreamHandler(sys.stdout)
log_stream.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(log_stream)

HTML_PARSER = 'html.parser'
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

    try:
        metadata = get_metadata_from_ncc(ncc_path)
    except DaisyExtractError as e:
        logger.error(str(e))
        sys.exit(1)

    output_directory = os.path.join(output_directory, make_safe_filename(metadata.authors), make_safe_filename(metadata.title))
    logger.info('Extracting content of book: {0} by {1} from {2} to {3}'.format(metadata.title, metadata.authors, input_directory, output_directory))

    audio_files = []
    for file in smil_files:
        smil = parse_smil_file(file)
        try:
            section_title = get_title_from_smil(smil)
            logger.debug('Found SMIL section: {0}'.format(section_title))
        except DaisyExtractError:
            logger.error('Could not retrieve SMIL metadata from: {0}'.format(file))
            sys.exit(1)

        section_audio_files = get_audio_filenames_from_smil(smil)
        section_audio_files = set(section_audio_files)
        logger.debug('SMIL section spans {0} audio file(s)'.format(len(section_audio_files)))

        for audio_file in section_audio_files:
            audio_files.append((section_title, os.path.join(input_directory, audio_file)))

    logger.info('Copying {0} audio files'.format(len(audio_files)))
    try:
        os.makedirs(output_directory)
        logger.debug('Created directory: {0}'.format(output_directory))
    except (FileExistsError, PermissionError):
        pass


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
    smil_files = list(filter(lambda smil: not smil.upper().endswith(MASTER_SMIL_FILENAME), glob.iglob(os.path.join(directory, SMIL_GLOB))))
    number_of_smil_files = len(smil_files)
    if number_of_smil_files >= 1:
        logger.debug('Found {0} SMIL files in directory'.format(number_of_smil_files))
        return natsorted(smil_files)
    else:
        logger.debug('No SMIL files found in directory')
        raise DaisyExtractError('No SMIL files found')


def get_metadata_from_ncc(ncc_path):
    with open(ncc_path, 'r', encoding='UTF-8') as f:
        ncc = BeautifulSoup(f, HTML_PARSER)

    title_tag = ncc.find('meta', attrs={'name': 'dc:title'})
    if title_tag is None:
        raise DaisyExtractError('The title of the DAISY book could not be found')
    title = title_tag.attrs.get('content')
    if not title:
        raise DaisyExtractError('The title of the DAISY book is blank')
    logger.debug('DAISY book title: {0}'.format(title))

    creator_tags = ncc.find_all('meta', attrs={'name': 'dc:creator'})
    if not creator_tags:
        raise DaisyExtractError('No authors are listed in the DAISY book')
    authors = ', '.join([tag.attrs.get('content') for tag in creator_tags])
    logger.debug('{0} author(s) listed in DAISY book metadata: {1}'.format(len(creator_tags), authors))

    return BookMetadata(authors, title)


def parse_smil_file(path):
    logger.debug('Parsing SMIL: {0}'.format(os.path.split(path)[-1]))
    with open(path, 'r', encoding='UTF-8') as f:
        return BeautifulSoup(f, HTML_PARSER)


def get_title_from_smil(smil):
    title_tag = smil.find('meta', attrs={'name': 'title'})
    if title_tag is None:
        raise DaisyExtractError('Unable to extract title from SMIL')
    title = title_tag.attrs.get('content')
    if not title:
        raise DaisyExtractError('SMIL section has no title')
    return title


def get_audio_filenames_from_smil(smil):
    return (audio.attrs.get('src') for audio in smil.find_all('audio'))


def make_safe_filename(filename):
    # strip out any disallowed chars and replace with underscores
    disallowed_ascii = [chr(i) for i in range(0, 32)]
    disallowed_chars = '<>:"/\\|?*^{0}'.format(''.join(disallowed_ascii))
    translator = dict((ord(char), '_') for char in disallowed_chars)
    safe_filename = filename.replace(': ', ' - ').translate(translator).rstrip('. ')
    return safe_filename


if __name__ == '__main__':
    main()

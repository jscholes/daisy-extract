# daisy-extract
# Copyright (C) 2016 James Scholes
# This program is free software, licensed under the terms of the GNU General Public License (version 3 or later).
# See the file LICENSE for more details.

from collections import namedtuple
import argparse
import glob
import logging
import os
import platform
import shutil
import sys

from bs4 import BeautifulSoup
from natsort import natsorted


__version__ = '0.1'
is_windows = 'windows' in platform.system().lower()

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


class InvalidDAISYBookError(Exception):
    pass


class ExtractMetadataError(Exception):
    pass


def main():
    logger.info('daisy-extract version {0}'.format(__version__))
    cli_args = parse_command_line()
    if cli_args.debug:
        logger.setLevel(logging.DEBUG)

    encoding = getattr(cli_args, 'encoding', 'utf-8')

    input_directory = os.path.abspath(cli_args.input_directory)
    output_directory = os.path.abspath(cli_args.output_directory)
    if not os.path.exists(input_directory) or not os.path.isdir(input_directory):
        exit_with_error('{0} does not exist or is not a directory'.format(input_directory))

    try:
        metadata = create_metadata_object_from_ncc(find_ncc_path(input_directory), encoding=encoding)
    except InvalidDAISYBookError as e:
        exit_with_error('The contents of {0} don\'t seem to be a valid DAISY 2.02 book: {1}'.format(input_directory, str(e)))
    except ExtractMetadataError as e:
        exit_with_error(str(e))

    output_directory = os.path.join(output_directory, make_safe_filename(metadata.authors), make_safe_filename(metadata.title))
    logger.info('Extracting content of book: {0} by {1} from {2} to {3}'.format(metadata.title, metadata.authors, input_directory, output_directory))

    source_audio_files = []
    destination_audio_files = []
    for doc in find_smil_documents(input_directory):
        parsed_doc = parse_smil_document(doc, encoding=encoding)
        try:
            section_title = find_document_title(parsed_doc)
            logger.debug('Found SMIL document: {0}'.format(section_title))
        except ExtractMetadataError as e:
            exit_with_error('Could not retrieve metadata from SMIL document ({0}): {1}'.format(file, str(e)))

        section_audio_files = get_audio_filenames_from_smil(parsed_doc)
        logger.debug('SMIL document spans {0} audio file(s)'.format(len(section_audio_files)))

        for audio_file in section_audio_files:
            source_audio_files.append((section_title, os.path.join(input_directory, audio_file)))

    logger.info('Copying {0} audio files'.format(len(source_audio_files)))
    try:
        os.makedirs(output_directory)
        logger.debug('Created directory: {0}'.format(output_directory))
    except (FileExistsError, PermissionError):
        pass

    track_number = 1
    for section_name, file_path in source_audio_files:
        destination_filename = '{0:02d} - {1}.{2}'.format(track_number, make_safe_filename(section_name), os.path.splitext(file_path)[-1][1:].lower())
        destination_path = os.path.join(output_directory, destination_filename)
        logger.debug('Copying file: {0} to: {1}'.format(file_path, destination_path))
        if is_windows:
            destination_path = add_path_prefix(destination_path)
        shutil.copyfile(file_path, destination_path)
        destination_audio_files.append(os.path.split(destination_path)[-1])
        track_number += 1

    logger.info('Creating M3U playlist')
    playlist_filename = '{0}.m3u'.format(make_safe_filename(metadata.title))
    playlist_path = os.path.join(output_directory, playlist_filename)
    logger.debug('M3U playlist path: {0}'.format(playlist_path))
    if is_windows:
        playlist_path = add_path_prefix(playlist_path)
    with open(playlist_path, 'w', newline=None) as f:
        f.write('\n'.join(destination_audio_files))

    logger.info('Done!')


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-directory', nargs='?', required=True)
    parser.add_argument('-o', '--output-directory', nargs='?', required=True)
    parser.add_argument('-e', '--encoding', nargs='?', required=False)
    parser.add_argument('-d', '--debug', dest='debug', action='store_true', default=False, help='Enable debug logging')
    args = parser.parse_args()
    return args


def exit_with_error(message):
    logger.error(message)
    sys.exit(1)


def find_ncc_path(directory):
    filenames = (NCC_FILENAME, NCC_FILENAME.lower())
    for filename in filenames:
        path = os.path.join(directory, filename)
        if os.path.exists(path) and os.path.isfile(path):
            logger.debug('Found NCC file: {0}'.format(path))
            return path

    raise InvalidDAISYBookError('Could not find NCC file')


def find_smil_documents(directory):
    documents = list(filter(lambda smil: not smil.upper().endswith(MASTER_SMIL_FILENAME), glob.iglob(os.path.join(directory, SMIL_GLOB))))
    if documents:
        logger.debug('Found {0} SMIL documents in directory'.format(len(documents)))
        return natsorted(documents)
    else:
        raise InvalidDAISYBookError('No SMIL documents found')


def create_metadata_object_from_ncc(ncc_path, encoding='utf-8'):
    with open(ncc_path, 'r', encoding=encoding) as f:
        ncc = BeautifulSoup(f, HTML_PARSER)

    title_tag = ncc.find('meta', attrs={'name': 'dc:title'})
    if title_tag is None:
        raise ExtractMetadataError('The title of the DAISY book could not be found')
    title = title_tag.attrs.get('content')
    if not title:
        raise ExtractMetadataError('The title of the DAISY book is blank')

    creator_tags = ncc.find_all('meta', attrs={'name': 'dc:creator'})
    if not creator_tags:
        raise ExtractMetadataError('No authors are listed in the DAISY book')
    authors = ', '.join([tag.attrs.get('content') for tag in creator_tags])

    return BookMetadata(authors, title)


def parse_smil_document(path, encoding='utf-8'):
    logger.debug('Parsing SMIL document: {0}'.format(os.path.split(path)[-1]))
    with open(path, 'r', encoding=encoding) as f:
        return BeautifulSoup(f, HTML_PARSER)


def find_document_title(doc):
    title_tag = doc.find('meta', attrs={'name': 'title'})
    if title_tag is None:
        raise ExtractMetadataError('Unable to extract title from SMIL document')
    title = title_tag.attrs.get('content')
    if not title:
        raise ExtractMetadataError('SMIL document has no title')
    return title


def get_audio_filenames_from_smil(smil):
    audio_files = [audio.attrs.get('src') for audio in smil.find_all('audio')]
    unique_audio_files = []
    for file in audio_files:
        if file not in unique_audio_files:
            unique_audio_files.append(file)
    return tuple(unique_audio_files)


def add_path_prefix(path):
    return '\\\\?\\{0}'.format(path)


def make_safe_filename(filename):
    # strip out any disallowed chars and replace with underscores
    disallowed_ascii = [chr(i) for i in range(0, 32)]
    disallowed_chars = '<>:"/\\|?*^{0}'.format(''.join(disallowed_ascii))
    translator = dict((ord(char), '_') for char in disallowed_chars)
    safe_filename = filename.replace(': ', ' - ').translate(translator).rstrip('. ')
    return safe_filename


if __name__ == '__main__':
    main()

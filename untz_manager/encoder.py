"""Encoding related operations"""
import logging
import os
import signal
import subprocess
import sys
import threading

import taglib

LOGGER = logging.getLogger(__name__)
LOCK = threading.Condition()


def _get_vorbis_comments(audio_file, pattern):
    macros = (('%g', 'GENRE'),
              ('%n', 'TRACKNUMBER'),
              ('%t', 'TITLE'),
              ('%d', 'DATE'))

    oggenc_macros = {}

    afp = taglib.File(audio_file) # pylint: disable=E1103

    LOGGER.debug('Tags: %s', afp.tags)

    for macro, tag in macros:
        if macro in pattern:
            oggenc_macros[macro] = afp.tags.get(tag, [None])[0] or '(none)'

    oggenc_macros['%a'] = (afp.tags.get('ALBUM_ARTIST', [None])[0] or
                           afp.tags.get('ALBUMARTIST', [None])[0] or
                           afp.tags.get('ALBUM ARTIST', [None])[0] or
                           afp.tags.get('COMPOSER', [None])[0] or
                           afp.tags.get('PERFORMER', [None])[0] or
                           afp.tags.get('ARTIST', [None])[0] or
                           'Unknown artist')
    oggenc_macros['%l'] = afp.tags.get('ALBUM', [None])[0] or 'Unknown album'

    afp.close()

    return oggenc_macros


def _create_subdirectories(filename):
    """Acquire lock and create subdirectories recursively."""
    with LOCK:
        target_path = os.path.dirname(filename)
        if not os.path.exists(target_path):
            os.makedirs(target_path)
            LOGGER.debug('Created "%s".', target_path)


def encode_file(audio_file, base_dir, pattern, quality, passthrough):
    """Run oggenc and encode file, storing in a logical manner.

    Args:
        audio_file (str): Path to input audio file.
        base_dir (str): Base output directory.
        pattern (str): Output file name template.
        quality (float/int): Constant quality factor for oggenc.
        passthrough (str): Additional CLI arguments for oggenc.
    """

    process_args = ['oggenc',
                    '-q', str(quality),
                    '-n']

    oggenc_macros = _get_vorbis_comments(audio_file, pattern)

    # Handle patterns on our side.
    output_filename = '{base_dir}/%a/%l/{pattern}.ogg'.format(base_dir=base_dir, pattern=pattern)

    for macro, value in oggenc_macros.items():
        output_filename = output_filename.replace(macro, value)
    process_args.append(output_filename)

    if passthrough:
        process_args.append(passthrough)
    process_args.append(audio_file)

    _create_subdirectories(output_filename)

    LOGGER.debug('Running "%s"', ' '.join(process_args))
    process = subprocess.Popen(process_args)
    process.communicate()

    if process.returncode:
        LOGGER.critical('Non-zero return code %d. Exiting.', process.returncode)
        os.kill(os.getpid(), signal.SIGTERM)


def apply_gain(base_dir):
    """Run vorbisgain on the given folder.

    Args:
        base_dir (str): Directory to recursively apply vorbisgain to.
    """
    process = subprocess.Popen(['vorbisgain', '-asfr', base_dir])
    process.communicate()

    if process.returncode:
        LOGGER.critical('Non-zero return code. Exiting.')
        sys.exit(process.returncode)

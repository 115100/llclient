"""Encoding related operations"""
import logging
import subprocess
import sys

import taglib

LOGGER = logging.getLogger(__name__)


def _get_vorbis_comments(audio_file, pattern):
    macros = (('%g', 'GENRE'),
              ('%n', 'TRACKNUMBER'),
              ('%t', 'TITLE'),
              ('%d', 'DATE'))

    params_dict = {'%g': '-G',
                   '%n': '-N',
                   '%t': '-t',
                   '%d': '-d'}

    vorbis_comments = {}

    afp = taglib.File(audio_file) # pylint: disable=E1103

    for macro, tag in macros:
        if macro in pattern:
            vorbis_comments[params_dict[macro]] = afp.tags.get(tag)[0] or '(none)'

    vorbis_comments['-a'] = (afp.tags.get('ALBUM_ARTIST', [None])[0] or
                             afp.tags.get('ALBUMARTIST', [None])[0] or
                             afp.tags.get('ALBUM ARTIST', [None])[0] or
                             afp.tags.get('ARTIST', [None])[0] or
                             'Unknown artist')
    vorbis_comments['-l'] = afp.tags.get('ALBUM', [None])[0] or 'Unknown album'

    afp.close()

    return vorbis_comments


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
                    '-n', '{base_dir}/%a/%l/{pattern}.ogg'.format(base_dir=base_dir,
                                                                  pattern=pattern)]

    if passthrough:
        process_args.append(passthrough)

    vorbis_comments = _get_vorbis_comments(audio_file, pattern)

    for tag, value in vorbis_comments.items():
        process_args.append(tag)
        process_args.append(value)

    process_args.append(audio_file)

    LOGGER.debug('Running "%s"', ' '.join(process_args))
    process = subprocess.Popen(process_args)
    process.communicate()

    if process.returncode:
        LOGGER.critical('Non-zero return code. Exiting.')
        sys.exit(process.returncode)


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

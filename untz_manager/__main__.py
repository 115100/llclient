"""Main entry point for untz."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import logging
import os

from . import __version__
from .encoder import apply_gain, encode_file
from .utils import preflight_checks, recursive_file_search

ARGS = get_args()
LOGGER = logging.getLogger(__name__)
threads = [] # pylint: disable=C0103


def get_args():
    """Parse and return arguments."""
    parser = argparse.ArgumentParser(description='Convert FLACs to OGGs and '
                                                 'sort into a sensible folder hierarchy.')
    parser.add_argument('-b', '--base',
                        dest='base_dir',
                        help='Base directory to store output files to.', required=True)
    parser.add_argument('-n', '--names',
                        default='%n - %t',
                        dest='pattern',
                        help='Produce filenames as this string, with %%g, %%a, %%l, %%n, %%t, %%d '
                             'replaced by genre, artist, album, track number, title, '
                             'and date, respectively. Also, %%%% gives a literal %%. '
                             'Defaults to %%n - %%t.')
    parser.add_argument('-p', '--passthrough',
                        dest='ogg_cli_parameters',
                        help='Additional CLI arguments to pass through to oggenc.',
                        default='')
    parser.add_argument('-q', '--quality',
                        dest='quality',
                        type=float,
                        default=10,
                        help='Sets encoding quality to n, between -1 (low) and 10 (high). '
                             'Fractional quality levels such as 2.5 are permitted.')
    parser.add_argument('-r', '--replaygain',
                        dest='replaygain',
                        action='store_true',
                        help='Apply replaygain tags with vorbisgain.')
    parser.add_argument('-t', '--threads',
                        dest='threads',
                        type=int,
                        default=cpu_count(),
                        help='Thread pool size to spawn.')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        dest='verbose',
                        help='Set verbose logging.')
    parser.add_argument('-V', '--version',
                        action='version',
                        version=__version__,
                        help='Print version and exit.')
    parser.add_argument(dest='inputs', help='List of folder/file inputs.', nargs='+')

    return parser.parse_args()


def _encode_on_filter(args, queue):
    if file_entry.lower().endswith('.flac'):
        encode_file(file_entry,
                    ARGS.base_dir.rstrip('/'),
                    ARGS.pattern,
                    ARGS.quality,
                    ARGS.ogg_cli_parameters)


def main():
    """Main logic for untz."""

    if ARGS.verbose:
        logging.basicConfig(level=logging.DEBUG)

    preflight_checks()

    LOGGER.info('Starting %d threads.', ARGS.threads)
    with ThreadPoolExecutor(max_workers=ARGS.threads) as tpe:
        for i in ARGS.inputs:
            if os.path.isdir(i):
                tpe.map(_encode_on_filter, recursive_file_search(i))
            else:
                tpe.submit(_encode_on_filter, i)

    if ARGS.replaygain:
        apply_gain(ARGS.base_dir)

    LOGGER.warning('Program exiting now.')

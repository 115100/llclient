"""Useful functions to use."""
import argparse
from multiprocessing import cpu_count
import os
import shutil

from . import __version__


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


def preflight_checks():
    """Check required executables are present in $PATH.

    Raises:
        FileNotFoundError: when executables are not present.
    """
    if not shutil.which('oggenc'):
        raise FileNotFoundError('Oggenc must be in $PATH and be executable.')
    if not shutil.which('flac'):
        raise FileNotFoundError('Flac must be in $PATH and be executable.')


def recursive_file_search(entry):
    """Recursively yield paths of all files in `entry`.

    Args:
        entry (str): Folder to walk.

    Yields:
        str, paths to all file entries.
    """
    for root, _, files in os.walk(entry):
        for file_entry in files:
            yield os.path.join(root, file_entry)

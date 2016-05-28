"""Main entry point for untz."""
import argparse
import logging
import multiprocessing
import os

from .encoder import apply_gain, encode_file
from .utils import preflight_checks, recursive_file_search

LOGGER = logging.getLogger(__name__)


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
                        default=multiprocessing.cpu_count(),
                        help='Thread pool size to spawn.')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        dest='verbose',
                        help='Set verbose logging.')
    parser.add_argument(dest='inputs', help='List of folder/file inputs.', nargs='+')

    return parser.parse_args()


def _encode_on_filter(args, queue):
    while True:
        file_entry = queue.get()

        # FIFO queue so we can do this
        if file_entry is None:
            LOGGER.info("PID %d received poison signal. Breaking.", os.getpid())
            break

        if file_entry.lower().endswith('.flac'):
            encode_file(file_entry,
                        args.base_dir.rstrip('/'),
                        args.pattern,
                        args.quality,
                        args.ogg_cli_parameters)


def main():
    """Main logic for untz."""
    args = get_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    preflight_checks()

    queue = multiprocessing.Queue()

    LOGGER.info('Starting %d threads.', args.threads)
    processes = [multiprocessing.Process(target=_encode_on_filter,
                                         args=(args, queue)) for i in range(args.threads)]

    for process in processes:
        process.start()

    for i in args.inputs:
        if os.path.isdir(i):
            for file_entry in recursive_file_search(i):
                LOGGER.debug('Encoding "%s"', file_entry)
                queue.put_nowait(file_entry)
        else:
            LOGGER.debug('Encoding "%s"', i)
            queue.put(i)

    # Send stop signal
    LOGGER.debug('Sending poison signal.')
    for _ in range(args.threads):
        queue.put(None)

    LOGGER.info('Waiting for processes to die.')
    for process in processes:
        process.join()

    if args.replaygain:
        apply_gain(args.base_dir)

    LOGGER.warning('Program exiting now.')

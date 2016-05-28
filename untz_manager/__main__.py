"""Main entry point for untz."""
from concurrent.futures import ThreadPoolExecutor
import logging
import os

from .encoder import apply_gain, encode_file
from .utils import get_args, preflight_checks, recursive_file_search

ARGS = get_args()
LOGGER = logging.getLogger(__name__)


def _encode_on_filter(file_entry):
    if file_entry.lower().endswith('.flac'):
        LOGGER.info('Encoding "%s"', file_entry)
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

    LOGGER.info('Program exiting now.')

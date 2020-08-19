"""Main entry point for untz."""
from concurrent.futures import ThreadPoolExecutor
import logging
import os

from .encoder import OpusEncoder, VorbisEncoder
from .utils import get_args, recursive_file_search

LOGGER = logging.getLogger(__name__)


def _encode_flac(encoder):
    def _encoder(file_entry):
        if file_entry.lower().endswith(".flac"):
            LOGGER.info('Encoding "%s".', file_entry)
            encoder.encode_file(file_entry)

    return _encoder


def main():
    """Main logic for untz."""
    ARGS = get_args()
    if ARGS.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if ARGS.encoder == "opus":
        encoder = OpusEncoder(ARGS.base_dir, ARGS.pattern, ARGS.bitrate)
    elif ARGS.encoder == "vorbis":
        encoder = VorbisEncoder(ARGS.base_dir, ARGS.pattern, ARGS.quality)
    else:
        raise ValueError("invalid encoder: {}".format(ARGS.encoder))

    flac_encoder = _encode_flac(encoder)

    LOGGER.info("Starting %d threads.", ARGS.threads)
    with ThreadPoolExecutor(max_workers=ARGS.threads) as tpe:
        futures = []
        for i in ARGS.inputs:
            if os.path.isdir(i):
                for fe in recursive_file_search(i):
                    futures.append(tpe.submit(flac_encoder, fe))
            else:
                futures.append(tpe.submit(flac_encoder, i))
        for future in futures:
            future.result()

    if ARGS.replaygain:
        encoder.apply_gain()
    LOGGER.info("Program exiting now.")

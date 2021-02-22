"""Main entry point for untz."""
from concurrent.futures import ThreadPoolExecutor
import logging
import os
from typing import Callable

from .encoder import Encoder, OpusEncoder, VorbisEncoder
from .utils import get_args, recursive_file_search
from .collection import Collection, Cue, Directory, Singlet

LOGGER = logging.getLogger(__name__)


def main() -> None:
    """Main logic for untz."""
    ARGS = get_args()
    if ARGS.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if ARGS.encoder == "opus":
        encoder = OpusEncoder(
            ARGS.base_dir, ARGS.pattern, ARGS.bitrate
        )  # type: Encoder
    elif ARGS.encoder == "vorbis":
        encoder = VorbisEncoder(ARGS.base_dir, ARGS.pattern, ARGS.quality)
    else:
        raise ValueError("invalid encoder: {}".format(ARGS.encoder))

    LOGGER.info("Starting %d threads.", ARGS.threads)
    with ThreadPoolExecutor(max_workers=ARGS.threads) as tpe:
        futures = []
        for i, path in enumerate(ARGS.inputs):
            if ".cue" in path:
                collection = Cue(path)  # type: Collection
            elif os.path.isdir(path):
                collection = Directory(path)
            else:
                collection = Singlet(path)

            for entry in collection:
                futures.append(tpe.submit(encoder.encode_file, entry))
        for future in futures:
            future.result()

    if ARGS.replaygain:
        encoder.apply_gain()

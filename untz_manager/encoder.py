"""Encoding related operations"""
import logging
import os
import re
import signal
import subprocess
import sys
import threading
from typing import List, Mapping

import taglib  # type: ignore


class Encoder:
    def __init__(self, base_dir: str, pattern: List[str], ext: str):
        self.lock = threading.Condition()
        self.logger = logging.getLogger("encoder")
        self.base_dir = base_dir
        self.pattern = pattern
        self.ext = ext

    def _get_vorbis_comments(self, audio_file: str) -> Mapping[str, str]:
        macros = (
            ("%g", "GENRE"),
            ("%n", "TRACKNUMBER"),
            ("%t", "TITLE"),
            ("%d", "DATE"),
        )

        try:
            afp = taglib.File(audio_file)  # pylint: disable=E1103
            self.logger.debug('Tags: "%s".', afp.tags)

            oggenc_macros = {}
            for macro, tag in macros:
                if macro in self.pattern:
                    oggenc_macros[macro] = afp.tags.get(tag, ["(none)"])[0]
            # Artist tag is non-standard, so get the first one that matches
            oggenc_macros["%a"] = (
                afp.tags.get("ALBUM_ARTIST", [None])[0]
                or afp.tags.get("ALBUMARTIST", [None])[0]
                or afp.tags.get("ALBUM ARTIST", [None])[0]
                or afp.tags.get("COMPOSER", [None])[0]
                or afp.tags.get("PERFORMER", [None])[0]
                or afp.tags.get("ARTIST", [None])[0]
                or "Unknown artist"
            )
            oggenc_macros["%l"] = afp.tags.get("ALBUM", ["Unknown album"])[0]
        finally:
            afp.close()

        return oggenc_macros

    def encode_file(self, audio_file: str) -> None:
        """Encode a given audio file, storing in a logical manner.

        Args:
            audio_file (str): Path to input audio file.
        """
        oggenc_macros = self._get_vorbis_comments(audio_file)

        # Handle patterns on our side.
        output_filename = "{base_dir}/%a/%l/{pattern}.{ext}".format(
            base_dir=self.base_dir, pattern=self.pattern, ext=self.ext
        )
        for macro, value in oggenc_macros.items():
            output_filename = output_filename.replace(
                macro, re.sub(r"[\"*/:<>?\\|]", "_", value)
            )

        with self.lock:
            target_path = os.path.dirname(output_filename)
            if not os.path.exists(target_path):
                os.makedirs(target_path)
                self.logger.debug('Created "%s".', target_path)

        self._run_encoder(audio_file, output_filename)

    def _run_encoder(self, audio_file: str, output_filename: str) -> None:
        raise NotImplementedError

    def apply_gain(self) -> None:
        """Run gain tagging on base_dir."""
        subprocess.run(
            ["rgbpm", "-b", self.base_dir], capture_output=True, check=True
        )


class OpusEncoder(Encoder):
    def __init__(self, base_dir: str, pattern: List[str], bitrate: int):
        self.base_dir = base_dir.rstrip("/")
        self.bitrate = bitrate
        super().__init__(base_dir=base_dir, pattern=pattern, ext="opus")

    def _run_encoder(self, audio_file: str, output_filename: str) -> None:
        process_args = [
            "opusenc",
            "--bitrate",
            str(self.bitrate),
            audio_file,
            output_filename,
        ]
        self.logger.debug('Running "%s".', " ".join(process_args))
        subprocess.run(process_args, capture_output=True, check=True)


class VorbisEncoder(Encoder):
    def __init__(self, base_dir: str, pattern: List[str], quality: float):
        self.base_dir = base_dir.rstrip("/")
        self.quality = quality
        super().__init__(base_dir=base_dir, pattern=pattern, ext="ogg")

    def _run_encoder(self, audio_file: str, output_filename: str) -> None:
        process_args = ["oggenc", "-q", str(self.quality), "-o", output_filename]
        process_args.append(audio_file)

        self.logger.debug('Running "%s".', " ".join(process_args))
        subprocess.run(process_args, capture_output=True, check=True)

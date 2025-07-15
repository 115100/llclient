"""Logic for polling and uploading files to load link."""

import argparse
import glob
import os
import struct
import subprocess
import tempfile
from typing import List, Optional
import wave

from wand.image import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler

from .service import Service

PATTERNS = [
    "*.flac",
    "*.jpg",
    "*.jpeg",
    "*.json",
    "*.mkv",
    "*.mp3",
    "*.mp4",
    "*.png",
    "*.torrent",
    "*.txt",
    "*.wav",
]


class _UploadHandler(PatternMatchingEventHandler):
    def __init__(
        self,
        args: argparse.Namespace,
        patterns: List[str],
        ignore_patterns: Optional[List[str]] = None,
        case_sensitive: bool = False,
        ignore_directories: bool = True,
    ):
        super(_UploadHandler, self).__init__(
            patterns=patterns,
            ignore_patterns=ignore_patterns,
            ignore_directories=ignore_directories,
            case_sensitive=case_sensitive,
        )
        self.service = Service()

        self.base_dir = args.base_dir
        self.compress = args.compress
        self.volume = args.volume
        self.sound: Optional[str] = None
        self.new_wav: Optional[str] = None

        self._init_sound()
        if os.path.isdir(args.base_dir):
            self._reprocess()
        else:
            try:
                os.makedirs(args.base_dir, 0o755)
            except os.error:  # may arise from races outside of the script
                pass

    def on_closed(self, event: FileSystemEvent) -> None:
        self._upload_file(event.src_path)

    def cleanup(self) -> None:
        """Remove temporary files."""
        if self.new_wav:
            os.remove(self.new_wav)

    def _upload_file(self, path: str) -> None:
        ul_fn = path

        _, ext = os.path.splitext(path)
        if ext == ".png" and self.compress:
            fd, tmp_fn = tempfile.mkstemp(suffix=".jpeg")
            os.close(fd)

            with Image(filename=path) as img:
                img.compression_quality = 75
                img.save(filename=tmp_fn)
            ul_fn = tmp_fn
            os.remove(path)

        link = self.service.upload(ul_fn, os.path.basename(path))
        os.remove(ul_fn)

        print(f"\nUploaded {path} to {link}")
        subprocess.Popen(f"echo -n {link} | wl-copy", shell=True)
        if self.sound:
            subprocess.Popen(f"aplay -q {self.sound}", shell=True)

    def _init_sound(self) -> None:
        wav_loc = os.path.expanduser("~/.config/llclient/completed.wav")
        if not os.path.isfile(wav_loc):
            print(
                "No completed.wav found. "
                "If you'd like to play a sound on upload, "
                "place a wav file at ~/.config/llclient/completed.wav."
            )
            return

        self.sound = wav_loc
        # Raising volume is a no-op as we don't handle overflow.
        if self.volume >= 100:
            return

        with wave.open(wav_loc, "rb") as wav:
            # FIXME: Volume changing only works on 16-bit/sample wav.
            if wav.getsampwidth() != 2:
                return

            fd, new_wave_filename = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            with wave.open(new_wave_filename, "wb") as new_wave:
                new_wave.setparams(wav.getparams())

                for _ in range(wav.getnframes()):
                    frame_format = "<" + "h" * wav.getnchannels()

                    new_wave.writeframes(
                        struct.pack(
                            frame_format,
                            *[
                                round(sample * self.volume / 100)
                                for sample in struct.unpack(
                                    frame_format, wav.readframes(1)
                                )
                            ],
                        )
                    )

            self.new_wav = new_wave_filename
            self.sound = new_wave_filename

    def _reprocess(self) -> None:
        for pattern in PATTERNS:
            for file_path in glob.glob(os.path.join(self.base_dir, pattern)):
                self._upload_file(file_path)


def main() -> None:  # pylint: disable=missing-docstring
    args = _parse_args()
    handler = _UploadHandler(args, patterns=PATTERNS)
    observer = Observer()
    observer.schedule(handler, path=args.base_dir)
    observer.start()

    try:
        observer.join()
    finally:
        if observer.is_alive():
            observer.stop()
            observer.join()
        handler.cleanup()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload all files in dir to load_link server."
    )
    parser.add_argument(
        "-b",
        "--base",
        dest="base_dir",
        help="Base directory to upload.",
        required=True,
    )
    parser.add_argument(
        "-c",
        "--compress",
        dest="compress",
        default=False,
        action="store_true",
        help="Compress files before uploading (lossy)",
    )
    parser.add_argument(
        "--volume",
        dest="volume",
        type=int,
        default=100,
        help="Sound notification volume.",
    )
    return parser.parse_args()

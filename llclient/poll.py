import argparse
from os.path import basename, expanduser, isfile, splitext
import os
import struct
import subprocess
import tempfile
from time import sleep
import wave

from wand.image import Image
import numpy
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import yaml

from .service import Service

class _UploadHandler(PatternMatchingEventHandler):
    def __init__(self, args, patterns=None, ignore_patterns=None, case_sensitive=False, ignore_directories=True):
        super(_UploadHandler, self).__init__(
            patterns=patterns,
            ignore_patterns=ignore_patterns,
            ignore_directories=ignore_directories,
            case_sensitive=case_sensitive
        )
        self.service = Service()

        self.volume = args.volume
        self.sound = None
        self.new_wav = None

        self._init_sound()

    def on_created(self, event):
        sleep(1)
        ul_fn = event.src_path
        _, ext = splitext(event.src_path)
        if ext == '.png':
            _, tmp_fn = tempfile.mkstemp()
            with Image(filename=event.src_path) as img:
                img.compression_quality = 9
                img.save(filename=tmp_fn)
            ul_fn = tmp_fn
            os.remove(event.src_path)

        link = self.service.upload(ul_fn, basename(event.src_path))
        os.remove(ul_fn)

        print('\nUploaded {} to {}'.format(event.src_path, link))
        subprocess.Popen('echo -n %s | xclip' % link, shell=True)
        if self.sound:
            subprocess.Popen('aplay -q ' + self.sound, shell=True)

    def cleanup(self):
        if self.new_wav:
            os.remove(self.new_wav)

    def _init_sound(self):
        wav_loc = expanduser('~/.config/llclient/completed.wav')
        if not isfile(wav_loc):
            print('No completed.wav found. If you\'d like to play a sound on upload, place a wav file at ~/.config/llclient/completed.wav.')
            return

        self.sound = wav_loc
        if self.volume == 100:
            return

        old_wave = wave.open(wav_loc, 'rb')
        params = old_wave.getparams()
        sound = old_wave.readframes(params.nframes)
        old_wave.close()

        sound = numpy.fromstring(sound, numpy.int16) * (args.volume / 100)
        sound = struct.pack('h' * len(sound), *sound.astype(int))

        _, new_wave_filename = tempfile.mkstemp()
        new_wave = wave.open(new_wave_filename, 'wb')
        new_wave.setparams(params)
        new_wave.writeframes(sound)
        new_wave.close()

        self.new_wav = new_wave_filename
        self.sound = new_wave_filename


def main():
    args = _parse_args()
    handler = _UploadHandler(args, patterns='*')
    observer = Observer()
    observer.schedule(handler, path=args.base_dir)
    observer.start()

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
        handler.cleanup()
        raise

def _parse_args():
    parser = argparse.ArgumentParser(description='Upload all files in dir to '
                                                 'load_link server.')
    parser.add_argument('-b', '--base',
                        dest='base_dir',
                        help='Base directory to upload.',
                        required=True,
    )
    parser.add_argument('--volume',
                        dest='volume',
                        type=int,
                        default=100,
                        help='Sound notification volume.',
    )
    return parser.parse_args()

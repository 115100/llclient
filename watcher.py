#!/usr/bin/env python3
from glob import glob
import numpy
from os import remove
from os.path import expanduser
import platform
import struct
import subprocess
import tempfile
from time import sleep
import wave
import yaml

from ll_functions import upload

def upload_all_files(upload_path=None):
    """
        Upload all files within ./files/
    """

    upload_path = upload_path or expanduser("~/ll_files/")

    with open(expanduser("~/.ll_config"), 'r') as fp:
        try:
            volume = yaml.load(fp)["volume"]
        except KeyError:
            volume = 100

    try:
        old_wave = wave.open(expanduser("~/.completed.wav"), "rb")
    except FileNotFoundError:
        print("Place a sound file at ~/.completed.wav")
        raise

    params = old_wave.getparams()
    sound = old_wave.readframes(params.nframes)
    old_wave.close()

    sound = numpy.fromstring(sound, numpy.int16) * (volume / 100)
    sound = struct.pack('h' * len(sound), *sound.astype(int))

    _, new_wave_filename = tempfile.mkstemp()
    new_wave = wave.open(new_wave_filename, "wb")
    new_wave.setparams(params)
    new_wave.writeframes(sound)
    new_wave.close()

    if "cygwin" in platform.platform().lower():
        clipboard = "> /dev/clipboard"
        sound = "cat " + new_wave_filename + " > /dev/dsp"
    else:
        clipboard = "| xclip"
        sound = "aplay " + new_wave_filename

    try:
        while True:
            for filename in glob(upload_path + '*'):
                sleep(0.1)

                print("File: " + filename)
                upload_link = upload(filename)

                if upload_link:
                    try:
                        print(upload_link)
                        subprocess.Popen(
                            "echo -n %s %s" % (upload_link, clipboard),
                            shell=True)
                        subprocess.Popen(sound, shell=True)
                        remove(filename)
                    except KeyboardInterrupt:
                        remove(filename)
                        raise
            sleep(0.5)
    except KeyboardInterrupt:
        remove(new_wave_filename)
        raise

if __name__ == "__main__":
    upload_all_files()

#!/usr/bin/env python3
from glob import glob
import numpy
from os import getcwd, remove
from os.path import expanduser
import platform
import struct
import subprocess
import sys
import tempfile
from time import sleep
import wave
import yaml

from ll_functions import upload

sys.path.insert(0, getcwd())

def upload_all_files():
    """
        Upload all files within ./files/
    """

    with open(expanduser("~/.ll_config"), 'r') as f:
        try:
            volume = yaml.load(f)["volume"]
        except KeyError:
            volume = 100

    old_wave = wave.open("completed.wav", "rb")
    params = old_wave.getparams()
    sound = old_wave.readframes(params.nframes)
    old_wave.close()

    sound = numpy.fromstring(sound, numpy.int16) * (volume / 100)
    sound = struct.pack('h' * len(sound), *sound.astype(int))

    new_wave_file, new_wave_filename = tempfile.mkstemp()
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
            for file in glob("./files/*"):
                sleep(0.1)

                print("File: " + file)
                upload_link = upload(file)

                if upload_link:
                    try:
                        print(upload_link)
                        subprocess.Popen(
                            "echo -n %s %s" % (upload_link, clipboard),
                            shell=True)
                        subprocess.Popen(sound, shell=True)
                        remove(file)
                    except KeyboardInterrupt:
                        remove(file)
                        raise
            sleep(0.5)
    except KeyboardInterrupt:
        remove(new_wave_filename)
        raise

if __name__ == "__main__":
    upload_all_files()

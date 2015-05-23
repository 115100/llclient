#!/usr/bin/env python3
import glob
import os
import platform
import subprocess
import sys
sys.path.insert(0, os.getcwd())
from time import sleep

from ll_functions import upload

def upload_all_files():

    if "cygwin" in platform.platform().lower():
        clipboard = "> /dev/clipboard"
        sound = "cat completed.wav > /dev/dsp"
    else:
        clipboard = "| xclip"
        sound = "aplay completed.wav"

    while True:
        for file in glob.glob("./files/*"):
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
                    os.remove(file)
                except KeyboardInterrupt:
                    os.remove(file)

        sleep(0.5)

if __name__ == "__main__":
    upload_all_files()

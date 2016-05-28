"""Useful functions to use."""
import os
import shutil


def preflight_checks():
    """Check required executables are present in $PATH.

    Raises:
        FileNotFoundError: when executables are not present.
    """
    if not shutil.which('oggenc'):
        raise FileNotFoundError('Oggenc must be in $PATH and be executable.')
    if not shutil.which('flac'):
        raise FileNotFoundError('Flac must be in $PATH and be executable.')


def recursive_file_search(entry):
    """Recursively yield paths of all files in `entry`.

    Args:
        entry (str): Folder to walk.

    Yields:
        str, paths to all file entries.
    """
    for root, _, files in os.walk(entry):
        for file_entry in files:
            yield os.path.join(root, file_entry)

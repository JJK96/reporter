from pathlib import Path
import os
import re
from importlib.metadata import version
from dataclasses import dataclass

reporter_version = version('reporter')


class ReportRootNotFound(Exception):
    pass


def find_report_root():
    """Find the root directory of the report"""

    current_dir = Path(".")

    # Go up a directory 3 times
    for i in range(3):
        if "issues" in os.listdir(current_dir):
            return os.path.realpath(current_dir)
        else:
            current_dir = current_dir.resolve().parent
    raise ReportRootNotFound("Could not find issue dir, ensure that you are running the script from your report directory.")


@dataclass
class CascadedFile:
    # Root directory
    dir: str
    # Relative path from dir to directory containing file
    relpath: str
    # Path to directory containing file
    dirpath: str
    # Filename
    fname: str

def cascade_directories(directories):
    """
    Return files from a list of directories, where files in later directories are fallbacks if a file is not found in an earlier directory
    
    :return: generator(CascadedFile)
    """
    processed = set()
    for dir in directories:
        for dirpath, dnames, fnames in os.walk(dir):
            relpath = os.path.relpath(dirpath, dir)
            for f in fnames:
                key = (relpath, f)
                if key in processed:
                    continue
                else:
                    processed.add(key)
                    yield CascadedFile(
                        dir=dir, relpath=relpath, dirpath=dirpath, fname=f
                    )


def slugify(filename):
    disallowed = r'[\\/:*?"<>|]'
    return re.sub(disallowed, "_", filename)

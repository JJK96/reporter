from pathlib import Path
import os
import re


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


def slugify(filename):
    disallowed = r'[\\/:*?"<>|]'
    return re.sub(disallowed, "_", filename)

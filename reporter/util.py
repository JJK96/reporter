from pathlib import Path
import os
import re
import shutil
from importlib.metadata import version
from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader
from jinja2 import StrictUndefined

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

def cascade_directories(directories, excluded=[]):
    """
    Return files from a list of directories, where files in later directories are fallbacks if a file is not found in an earlier directory
    
    :return: generator(CascadedFile)
    """
    processed = set()
    def should_exclude(relpath):
        for e in excluded:
            if relpath.startswith(e):
                return True
        return False

    for dir in directories:
        for dirpath, dnames, fnames in os.walk(dir):
            relpath = os.path.relpath(dirpath, dir)
            if should_exclude(relpath):
                continue
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


def get_latex_env(template_dir):
    return Environment(
        loader=FileSystemLoader(template_dir),
        block_start_string=r'\BLOCK{',
        block_end_string='}',
        variable_start_string=r'\VAR{',
        variable_end_string='}',
        comment_start_string=r'\#{',
        comment_end_string='}',
        line_statement_prefix='%%',
        line_comment_prefix='%#',
        trim_blocks=True,
        autoescape=False,
        undefined=StrictUndefined)


def template(content, output_dir, template_dirs, no_overwrite=[], extensions=[".tex", ".cls"], templates_output_dir=None, excluded_dirs=[]):
    """ For each unique path in template_dirs read it, perform jinja templating and write to output dir

        :param template_dirs: List of template_directories, files in later directories are fallbacks in case the filename does not exist in earlier template_dirs.
            (So, earlier directories override later directories)
    """
    if templates_output_dir:
        os.makedirs(templates_output_dir, exist_ok=True)
    for f in cascade_directories(template_dirs, excluded_dirs):
        output_dir_path = os.path.join(output_dir, f.relpath)
        _, ext = os.path.splitext(f.fname)
        if ext not in extensions:
            continue
        path = os.path.join(f.relpath, f.fname)
        output_path = os.path.normpath(os.path.join(output_dir, path))
        if output_path in no_overwrite:
            continue
        output_path = Path(output_path)
        if output_path.is_symlink() and not output_path.exists():
            # Remove broken symlinks
            os.remove(output_path)
        if f.relpath != '.':
            os.makedirs(output_dir_path, exist_ok=True)
        if templates_output_dir:
            src_path= os.path.normpath(os.path.join(f.dir, path))
            dst_path = os.path.normpath(os.path.join(templates_output_dir, path))
            shutil.copy(src_path, dst_path)
        env = get_latex_env(f.dir)
        template = env.get_template(path)
        rendered = template.render(content)
        with open(output_path, 'w') as f:
            f.write(rendered)

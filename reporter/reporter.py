from textile_parser import parse_textile_file, check_issue
from pathlib import Path
from os.path import join
from dataclasses import dataclass
from collections import defaultdict, OrderedDict

from .util import find_report_root, template
from .cvss import score_to_severity
from .config import (severities, TEMPLATES_DIR, STATIC_CONTENT_DIR, STATIC_IMAGES_DIR,
                     NECESSARY_FILES_DIR, REPORT_TEMPLATE_DIR,
                     DYNAMIC_TEXT_LIB, BASE_TEMPLATE, CONFIG_LIB, REPORTER_LIB, config)
import importlib
import yaml
import subprocess
import os
import shutil
from deepmerge import always_merger
from .commandline import Commandline
from .report_manager import ReportManager


def load_content(filename):
    with open(filename) as f:
        return yaml.safe_load(f)


def read_file(filename):
    with open(filename) as f:
        return f.read()


def copy_output(output_file, root):
    try:
        shutil.copy(output_file, root)
    except shutil.SameFileError:
        pass


def load_issue_evidence(filename):
    _, extension = os.path.splitext(filename)
    match extension:
        case (".yaml"|".yml"):
            return load_content(filename)
        case _:
            return parse_textile_file(filename)


def load_evidence(filename):
    """Load evidence from a given evidence file"""
    content = load_issue_evidence(filename)
    if not content.get('location'):
        content['location'] = config.get('default_location')
        if not content['location']:
            raise Exception(f"Evidence: {filename} has no location and no default location is set")
    return content


@dataclass
class Issue:
    content: dict

    def __getattr__(self, name):
        try:
            return self.content[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name == "content":
            super().__setattr__(name, value)
        else:
            self.content[name] = value

    # def __hasattr__(self, name):
    #     return 'name' in self.content

    @property
    def severity(self):
        return score_to_severity(self.cvss_score)


def load_issue(issue):
    _, extension = os.path.splitext(issue)
    if extension == "tex":
        # The file is already a complete issue
        return read_file(issue)
    content = load_issue_evidence(issue)
    check_issue(content)
    return Issue(content)


def load_issue_with_evidences(issue, evidences):
    try:    
        issue = load_issue(issue)
    except Exception as e:
        print(f"Exception while loading issue: {issue}")
        raise e
    evidences = map(load_evidence, evidences)
    issue.content['evidences'] = list(evidences)
    return issue


def find_issues_and_evidences(issue_dir=config.get('issue_dir')):
    """Yield tuples of an issue path and a list of evidence paths"""
    for dirpath, dnames, fnames in os.walk(issue_dir):
        relpath = os.path.relpath(dirpath, issue_dir)
        if relpath == '.':
            continue
        # Get Issue file
        issue = None
        evidences = []
        for filename in sorted(fnames):
            path = os.path.join(dirpath, filename)
            if filename.startswith("issue") or filename.endswith(".issue"):
                issue = path
            else:
                evidences.append(path)
        if issue:
            yield issue, evidences


def load_issues_with_evidences(issue_dir=config.get('issue_dir')):
    for issue, evidences in find_issues_and_evidences(issue_dir):
        yield load_issue_with_evidences(issue, evidences)


def load_issues(**kwargs):
    for issue, _ in find_issues_and_evidences(**kwargs):
        yield load_issue(issue)


def create_issue_dict(issues):
    issue_dict = defaultdict(list)
    for issue in issues:
        issue_dict[issue.severity].append(issue)
    ordered = OrderedDict()
    taken = set()
    i = 1
    for k in severities:
        v = sorted(issue_dict[k], key=lambda x: x.cvss_score, reverse=True)
        # Number the issues
        for issue in v:
            while i in taken:
                i += 1
            if not hasattr(issue, 'number'):
                issue.number = i
            taken.add(issue.number)
        ordered[k] = v
    return ordered


class Template:
    def __init__(self, name=BASE_TEMPLATE, language=config.get('language'), **kwargs):
        self.name = name
        self.language = language
        self.dir = os.path.join(TEMPLATES_DIR, name)
        self.STATIC_CONTENT_DIR = os.path.join(self.dir, STATIC_CONTENT_DIR)
        self.REPORT_TEMPLATE_DIR = os.path.join(self.dir, REPORT_TEMPLATE_DIR)
        self.STATIC_IMAGES_DIR = os.path.join(self.dir, STATIC_IMAGES_DIR)
        self.DYNAMIC_TEXT_LIB = os.path.join(self.dir, DYNAMIC_TEXT_LIB)
        self.CONFIG_LIB = os.path.normpath(os.path.join(self.dir, CONFIG_LIB))
        self.REPORTER_LIB = os.path.normpath(os.path.join(self.dir, REPORTER_LIB))
        self.reporter_args = kwargs
        self.commandline = Commandline(self)
        self.report_manager = ReportManager(self)

    @property
    def reporter(self):
        return self.reporter_class(self, **self.reporter_args)

    @property
    def reporter_class(self):
        if Path(self.REPORTER_LIB).exists():
            spec = importlib.util.spec_from_file_location("template_reporter", self.REPORTER_LIB)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.Reporter
        else:
            return Reporter

    def load_static_content(self):
        lang = load_content(os.path.join(self.STATIC_CONTENT_DIR, f"{self.language}.yaml"))
        general = load_content(os.path.join(self.STATIC_CONTENT_DIR, "general.yaml"))
        return always_merger.merge(lang, general)


class Reporter:
    # Cache for content
    _content = None

    def __init__(self, template=None, output_dir=config.get('output_dir'), report_filename=config.get('report_output_file'), issue_dir=config.get('issue_dir'), report_dir=None):
        if template:
            self.template = template
        else:
            self.template = Template(BASE_TEMPLATE)
        self.report_filename = report_filename
        if report_dir:
            self.root = report_dir
        else:
            self.root = find_report_root()
        self.output_dir = join(self.root, output_dir)
        self.issue_dir = join(self.root, issue_dir)
        self.output_file = join(self.output_dir, self.report_filename)

    @property
    def final_report_filename(self):
        return "final_report", ".pdf"

    def inc_version(self, version):
        if not version:
            return "_v1"
        else:
            cur_version = int(version[2:])
            return "_v{}".format(cur_version + 1)

    def finalize(self):
        src = self.output_file
        dst, ext = self.final_report_filename
        version = ""
        while Path(dst + version + ext).exists():
            version = self.inc_version(version)
        shutil.copy(src, dst + version + ext)

    def copy_files(self, dir, no_overwrite=[]):
        for path in os.listdir(dir):
            src = os.path.join(dir, path)
            dst = os.path.join(self.output_dir, path)
            if dst in no_overwrite:
                continue
            try:
                shutil.copytree(src, dst, dirs_exist_ok=True)
            except NotADirectoryError:
                shutil.copy(src, dst)

    def symlink_report_files(self):
        paths = []
        for path in os.listdir():
            if path.startswith('.') or os.path.realpath(path) == os.path.realpath(self.output_dir):
                # Don't symlink hidden files or the output dir
                continue
            output_path = Path(os.path.join(self.output_dir, path))
            if output_path.exists() and not output_path.is_symlink():
                # Remove file that is not the correct symlink
                os.remove(output_path)
            if not output_path.is_symlink():
                os.symlink(os.path.realpath(path), output_path)
            paths.append(output_path.__fspath__())
        return paths

    def load_dynamic_content(self, content):
        try:
            spec = importlib.util.spec_from_file_location("template_dynamic_text", self.template.DYNAMIC_TEXT_LIB)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            generator_class = mod.generators.get(self.template.language)
            generator = generator_class(content)
            generator.generate()
        except (FileNotFoundError, NotImplementedError):
            # If there is no dynamic content, don't fail
            pass

    def process_issues(self, content, issues):
        """ Override to process issues based on content """
        pass

    def add_issues_and_stats(self, content):
        issues = list(load_issues_with_evidences(self.issue_dir))
        self.process_issues(content, issues)
        content['issues'] = create_issue_dict(issues)
        content['num_issues'] = len(issues)
        content['num_severity'] = {k: len(v) for k, v in content['issues'].items()}

    def add_config(self, content):
        content['config'] = config

    def get_locations(self):
        locations = set()
        for _, evidences in find_issues_and_evidences(self.issue_dir):
            for evidence in evidences:
                evidence = load_evidence(evidence)
                locations.add(evidence['location'])
        return locations

    def get_content(self):
        # Load static content used for jinja templating
        content = self.template.load_static_content()

        # Load issues from issue_dir and add to the jinja content
        self.add_issues_and_stats(content)

        # Add config to the content object
        self.add_config(content)

        # Add dynamic content/text to the content object
        self.load_dynamic_content(content)

        return content

    @property
    def content(self):
        if not self._content:
            self._content = self.get_content()
        return self._content

    def generate(self, preprocess_only=False):
        """Generate a report"""

        # Check if REPORT_FILE exists
        if not Path(config.get('report_file')).exists():
            raise Exception(f"{config.get('report_file')} does not exist, are you in the right directory?")

        # Get content
        content = self.content

        # Create output dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Make files from current dir accessible in output_dir
        no_overwrite = self.symlink_report_files()

        # Perform jinja templating using jinja context
        default_template = Template(BASE_TEMPLATE)
        template(content, self.output_dir, [self.template.REPORT_TEMPLATE_DIR, default_template.REPORT_TEMPLATE_DIR], no_overwrite=no_overwrite)

        # Copy some necessary files (makefile, latex packages)
        self.copy_files(NECESSARY_FILES_DIR, no_overwrite=no_overwrite)

        # Copy static images
        if Path(self.template.STATIC_IMAGES_DIR).exists():
            shutil.copytree(self.template.STATIC_IMAGES_DIR, os.path.join(self.output_dir, STATIC_IMAGES_DIR), dirs_exist_ok=True)

        if not preprocess_only:
            # Run make to compile the report
            make = subprocess.run(['make', '-C', self.output_dir])

            # Raise exception if make was not succesful
            make.check_returncode()

            # Copy the report from the output_dir to the current directory
            copy_output(self.output_file, self.root)

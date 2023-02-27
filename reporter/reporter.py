from pathlib import Path
from os.path import join
from collections import defaultdict, OrderedDict

from .util import find_report_root, template
from .config import (COMMANDLINE_LIB, REPORT_MANAGER_LIB, severities, TEMPLATES_DIR, STATIC_CONTENT_DIR, STATIC_IMAGES_DIR,
                     NECESSARY_FILES_DIR, REPORT_TEMPLATE_DIR, PARENTS_FILE,
                     DYNAMIC_TEXT_LIB, BASE_TEMPLATE, CONFIG_LIB, REPORTER_LIB, config)
import importlib
import subprocess
import os
import shutil
from functools import reduce
from deepmerge import always_merger
from .commandline import Commandline
from .report_manager import ReportManager
from .issues import load_content, load_issues_with_evidences, find_issues_and_evidences, load_evidence, copy_output


def merge_dicts(dict_list):
    if not dict_list:
        return {}
    return reduce(lambda x, y: always_merger.merge(y, x), dict_list)


def create_issue_dict(issues):
    issue_dict = defaultdict(list)
    for issue in issues:
        issue_dict[issue.severity].append(issue)
    ordered = OrderedDict()
    taken = set([issue.number for issue in issues if hasattr(issue, 'number')])
    i = 1
    for k in severities:
        v = sorted(issue_dict[k], key=lambda x: float(x.cvss_score), reverse=True)
        # Number the issues
        for issue in v:
            while i in taken:
                i += 1
            if not hasattr(issue, 'number'):
                issue.number = i
                i += 1
        ordered[k] = v
    return ordered


class Template:
    def __init__(self, name=BASE_TEMPLATE, language=config.get('language'), **kwargs):
        self.name = name
        self.language = language
        self.dir = os.path.join(TEMPLATES_DIR, name)
        self.REPORT_TEMPLATE_DIR = os.path.join(self.dir, REPORT_TEMPLATE_DIR)
        self.STATIC_CONTENT_DIR = os.path.join(self.dir, STATIC_CONTENT_DIR)
        self.STATIC_IMAGES_DIR = os.path.join(self.dir, STATIC_IMAGES_DIR)
        self.DYNAMIC_TEXT_LIB = os.path.join(self.dir, DYNAMIC_TEXT_LIB)
        self.CONFIG_LIB = os.path.normpath(os.path.join(self.dir, CONFIG_LIB))
        self.REPORTER_LIB = os.path.normpath(os.path.join(self.dir, REPORTER_LIB))
        self.COMMANDLINE_LIB = os.path.normpath(os.path.join(self.dir, COMMANDLINE_LIB))
        self.REPORT_MANAGER_LIB = os.path.normpath(os.path.join(self.dir, REPORT_MANAGER_LIB))
        self.reporter_args = kwargs
        self.inheritance_tree = self.load_inheritance_tree()

    def load_inheritance_tree(self):
        path = os.path.join(self.dir, PARENTS_FILE)
        if Path(path).exists():
            with open(path, 'r') as f:
                parent_names = f.read().split()
            return [self] + [Template(parent) for parent in parent_names]
        else:
            return [self]

    @property
    def reporter(self):
        return self.reporter_class(self, **self.reporter_args)

    @property
    def reporter_class(self):
        for t in self.inheritance_tree:
            if Path(t.REPORTER_LIB).exists():
                spec = importlib.util.spec_from_file_location("template_reporter", t.REPORTER_LIB)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return mod.Reporter
        return Reporter

    @property
    def commandline(self):
        return self.commandline_class(self)

    @property
    def commandline_class(self):
        for t in self.inheritance_tree:
            if Path(t.COMMANDLINE_LIB).exists():
                spec = importlib.util.spec_from_file_location("template_commandline", t.COMMANDLINE_LIB)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return mod.Commandline
        return Commandline

    @property
    def report_manager(self):
        return self.report_manager_class(self)

    @property
    def report_manager_class(self):
        for t in self.inheritance_tree:
            if Path(t.REPORT_MANAGER_LIB).exists():
                spec = importlib.util.spec_from_file_location("template_report_manager", t.REPORT_MANAGER_LIB)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return mod.ReportManager
        return ReportManager

    def load_static_content(self):
        static_content = []
        for t in self.inheritance_tree:
            if Path(t.STATIC_CONTENT_DIR).exists():
                lang = load_content(os.path.join(t.STATIC_CONTENT_DIR, f"{self.language}.yaml"))
                general = load_content(os.path.join(t.STATIC_CONTENT_DIR, "general.yaml"))
                static_content.append(always_merger.merge(lang, general))
        return merge_dicts(static_content)


class Reporter:
    # Cache for content
    _content = None

    def __init__(self, template=None, output_dir=join(config.get('cache_dir'), config.get('output_dir')), report_filename=config.get('report_output_file'), issue_dir=config.get('issue_dir'), report_dir=None):
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
        self.templates_output_dir = join(self.root, config.get('cache_dir'), config.get('templates_output_dir'))
        self.issue_dir = join(self.root, issue_dir)
        self.images_dir = join(self.root, 'images')
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
        for path in os.listdir(self.root):
            _, ext = os.path.splitext(path)
            if ext in [".tex", ".yaml"]:
                # Do not symlink tex or yaml files, they are templated later
                continue
            full_path = os.path.realpath(os.path.join(self.root, path))
            if path.startswith('.') or full_path == os.path.realpath(self.output_dir):
                # Don't symlink hidden files or the output dir
                continue
            output_path = Path(os.path.join(self.output_dir, path))
            if output_path.exists() and not output_path.is_symlink():
                # Remove file that is not the correct symlink
                os.remove(output_path)
            if not output_path.is_symlink():
                os.symlink(full_path, output_path)
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

    def get_issues(self):
        yield from load_issues_with_evidences(self.issue_dir)

    def add_issues_and_stats(self, content):
        issues = list(self.get_issues())
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

    def get_images(self):
        for f in os.listdir(self.images_dir):
            if f.endswith('.png'):
                yield f

    def diff_standard_issues(self):
        titles = set()
        for standard_issue in self.template.report_manager.get_standard_issues(contents=True):
            titles.add(standard_issue.title)
        for issue in self.get_issues():
            if issue.title not in titles:
                yield issue

    def load_local_static_content(self):
        new_content = []
        for path in os.listdir(self.root):
            if not path.endswith('.yaml'):
                continue
            abs_path = os.path.join(self.root, path)
            file_content = load_content(abs_path)
            new_content.append(file_content)
        return merge_dicts(new_content)

    def get_content(self):
        # Load static content used for jinja templating
        content = self.template.load_static_content()
        local_content = self.load_local_static_content()
        content = always_merger.merge(content, local_content)

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

        # Get content
        content = self.content

        # Create output dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Make files from current dir accessible in output_dir
        no_overwrite = self.symlink_report_files()

        # Perform jinja templating using jinja context
        template_dirs = [self.root] + [t.REPORT_TEMPLATE_DIR for t in self.template.inheritance_tree]
        template(content, self.templates_output_dir, self.output_dir, template_dirs, no_overwrite=no_overwrite, excluded_dirs=[config.get('cache_dir'), '.git'])

        # Copy some necessary files (makefile, latex packages)
        self.copy_files(NECESSARY_FILES_DIR, no_overwrite=no_overwrite)

        # Copy static images
        for t in self.template.inheritance_tree[::-1]:
            if Path(t.STATIC_IMAGES_DIR).exists():
                shutil.copytree(t.STATIC_IMAGES_DIR, os.path.join(self.output_dir, STATIC_IMAGES_DIR), dirs_exist_ok=True)

        if not preprocess_only:
            # Run make to compile the report
            make = subprocess.run(['make', '-C', self.output_dir])

            # Raise exception if make was not succesful
            make.check_returncode()

            # Copy the report from the output_dir to the current directory
            copy_output(self.output_file, self.root)

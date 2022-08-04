from .config import ISSUE_TEMPLATES_DIR, STANDARD_ISSUE_DIR, config, REPORT_INIT_DIR
from .util import find_report_root, reporter_version, slugify, template

import shutil
import os
from deepmerge import always_merger
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

class ReportManager:
    def __init__(self, template):
        self.template = template

    def init(self, output_dir='.', type="pentest", 
             title="Title of the project", company="Company B.V.", testtime=40,
             startdate=None, enddate=None, additional_content=None, include_sample_issue=True):
        """Initiate a new report"""
        base_dir = os.path.join(REPORT_INIT_DIR, "base")
        shutil.copytree(base_dir, output_dir)
        # Move git directory to .git
        git_path = Path(os.path.join(output_dir, 'git'))
        if git_path.exists():
            os.rename(git_path, os.path.join(output_dir, '.git'))

        static = self.template.load_static_content()
        content = always_merger.merge({
            "report_type": type,
            "title": title,
            "company": company,
            "testtime": testtime,
            "startdate": startdate,
            "enddate": enddate,
            "language": self.template.language,
            "template": self.template.name,
            "reporter_version": reporter_version,
        }, static)
        if additional_content:
            content = always_merger.merge(content, additional_content)
        types_dir = os.path.join(REPORT_INIT_DIR, "types")    
        if type in os.listdir(types_dir):
            type_dir = os.path.join(types_dir, type)
        else:
            type_dir = os.path.join(types_dir, "default")
        template(content, output_dir, [type_dir, base_dir], extensions=[".tex", ".dradis", ".issue", ".ini"])
        print(f"Created a new report in {output_dir}")
        if include_sample_issue:
            self.create_issue(os.path.join(output_dir, config.get('issue_dir'), "example_issue", config.get('issue_filename')))

    def create_issue(self, 
            output_file,
            title="Issue title",
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N",
            cvss_score="0.0",
            description="",
            solution="",
            references="",
            do_create_evidence=True,
            ):
        """Create a new issue"""
        content = {
            "title": title,
            "cvss_vector": cvss_vector,
            "cvss_score": cvss_score,
            "description": description,
            "solution": solution,
            "references": references,
        }
        env = Environment(loader=FileSystemLoader(ISSUE_TEMPLATES_DIR))
        template = env.get_template("issue.dradis")
        rendered = template.render(content)
        dirname = os.path.dirname(output_file)
        os.makedirs(dirname, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(rendered)
        print(f"Created issue in {output_file}")
        if do_create_evidence:
            self.create_evidence(location=config.get('default_location'), output_dir=dirname)


    def create_standard_issue(self, input_file, output_file=None, do_create_evidence=True):
        if not output_file:
            basename = os.path.basename(input_file)
            lang, _, rest = basename.partition("_")
            dirname, _ = os.path.splitext(rest)
            output_file = os.path.join(find_report_root(), config.get('issue_dir'), dirname, config.get('issue_name'))
        dirname = os.path.dirname(output_file)
        os.makedirs(dirname, exist_ok=True)
        src = os.path.join(STANDARD_ISSUE_DIR, input_file)
        shutil.copy(src, output_file)
        print(f"Created issue in {output_file}")
        if do_create_evidence:
            self.create_evidence(location=config.get('default_location'), output_dir=dirname)
        return dirname


    def create_evidence_path(self, location, output_dir='.'):
        filename = slugify(f"{location}.dradis")
        i = 0
        while Path(output_dir, filename).exists():
            i += 1
            filename = slugify(f"{location}{i}.dradis")
        return filename


    def create_evidence(self, location="evidence", output_file=None, output_dir='.', description="Describe how you found the evidence"):
        """Create a new evidence"""
        if not output_file:
            output_file = os.path.join(output_dir, self.create_evidence_path(location, output_dir))
        env = Environment(loader=FileSystemLoader(ISSUE_TEMPLATES_DIR))
        template = env.get_template("evidence.dradis")
        rendered = template.render(location=location, description=description)
        with open(output_file, 'w') as f:
            f.write(rendered)
        print(f"Created evidence in {output_file}")


    def clean(self):
        """Clean current report of build files"""
        root = find_report_root()
        shutil.rmtree(os.path.join(root, config.get('output_dir')))


    def get_standard_issues(self):
        for folder, subfolders, files in os.walk(STANDARD_ISSUE_DIR):
            for file in files:
                _, extension = os.path.splitext(file)
                filePath = os.path.relpath(os.path.join(folder, file), STANDARD_ISSUE_DIR)
                if extension == ".issue":
                    yield filePath

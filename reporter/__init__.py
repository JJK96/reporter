from .reporter import Template, template
from .config import (STANDARD_ISSUE_DIR, REPORT_INIT_DIR,
                     BIN_DIR, ISSUE_TEMPLATES_DIR, config)
from .util import find_report_root
from jinja2 import Environment, FileSystemLoader
import re
import os
import shutil
from pathlib import Path
from datetime import date
from deepmerge import always_merger


def init(template_name=config.get('template'), language=config.get('language'), output_dir='.', type="pentest", 
         title="Title of the project", company="Company B.V.", testtime=40,
         startdate=None, enddate=None):
    """Initiate a new report"""
    shutil.copytree(REPORT_INIT_DIR, output_dir)
    # Move git directory to .git
    git_path = Path(os.path.join(output_dir, 'git'))
    if git_path.exists():
        os.rename(git_path, os.path.join(output_dir, '.git'))

    tmpl = Template(template_name, language=language)
    static = tmpl.load_static_content()
    content = always_merger.merge({
        "report_type": type,
        "title": title,
        "company": company,
        "testtime": testtime,
        "startdate": startdate,
        "enddate": enddate,
        "language": language,
        "template": template_name,
    }, static)
    template(content, output_dir, [REPORT_INIT_DIR], extensions=[".tex", ".dradis", ".issue", ".ini"])
    print(f"Created a new report in {output_dir}")


def create_issue(
        output_file,
        title="Issue title",
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N",
        cvss_score="0.0",
        do_create_evidence=True,
        ):
    """Create a new issue"""
    content = {
        "title": title,
        "cvss_vector": cvss_vector,
        "cvss_score": cvss_score,
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
        create_evidence(location=config.get('default_location'), output_dir=dirname)


def create_standard_issue(input_file, output_file=None, do_create_evidence=True):
    if not output_file:
        basename = os.path.basename(input_file)
        lang, rest = basename.split("_")
        dirname, _ = os.path.splitext(rest)
        output_file = os.path.join(find_report_root(), config.get('issue_dir'), dirname, config.get('issue_name'))
    dirname = os.path.dirname(output_file)
    os.makedirs(dirname)
    src = os.path.join(STANDARD_ISSUE_DIR, input_file)
    shutil.copy(src, output_file)
    print(f"Created issue in {output_file}")
    if do_create_evidence:
        create_evidence(location=config.get('default_location'), output_dir=dirname)

def slugify(filename):
    disallowed = r'[\\/:*?"<>|]'
    return re.sub(disallowed, "_", filename)


def create_evidence_path(location):
    filename = slugify(f"{location}.dradis")
    i = 0
    while Path(filename).exists():
        i += 1
        filename = slugify(f"{location}{i}.dradis")
    return filename


def create_evidence(location=None, output_file=None, output_dir='.'):
    """Create a new evidence"""
    if not location:
        location="unknown"
    if not output_file:
        output_file = os.path.join(output_dir, create_evidence_path(location))
    env = Environment(loader=FileSystemLoader(ISSUE_TEMPLATES_DIR))
    template = env.get_template("evidence.dradis")
    rendered = template.render(location=location)
    with open(output_file, 'w') as f:
        f.write(rendered)
    print(f"Created evidence in {output_file}")


def clean():
    """Clean current report of build files"""
    root = find_report_root()
    shutil.rmtree(os.path.join(root, config.get('output_dir')))


def main():
    import argparse

    def generate_caller(args):
        template = Template(args.template, language=args.language)
        template.reporter.generate()

    def init_caller(args):
        init(
            args.template,
            args.language,
            output_dir=args.output_dir,
            type=args.type,
            title=args.title,
            company=args.company,
            testtime=args.testtime,
            startdate=args.startdate,
            enddate=args.enddate,
        )

    def clean_caller(args):
        clean()

    def create_issue_caller(args):
        if args.standard_issue:
            create_standard_issue(args.standard_issue, args.output_file)
            return
        if not args.output_file:
            if not args.title:
                raise Exception("Title is required when no output file or standard issue is given")
            args.output_file = os.path.join(find_report_root(), config.get('issue_dir'), slugify(args.title), config.get('issue_filename'))
        create_issue(
            args.output_file,
            args.title,
            args.cvss_vector,
            args.cvss_score,
        )

    def create_evidence_caller(args):
        create_evidence(args.location, args.output_file)

    def run_command(command):
        os.system(os.path.join(BIN_DIR, command))

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='Subcommands')

    generate_parser = subparsers.add_parser("generate", help="Generate a report")
    generate_parser.add_argument("--template", "-t", help="Template to use", default=config.get('template'))
    generate_parser.add_argument("--language", "-l", help="Language", default=config.get('language'))
    generate_parser.set_defaults(func=generate_caller)

    init_parser = subparsers.add_parser("init", help="Inititate a new report")
    init_parser.add_argument("output_dir", help="Directory to create the new report in")
    init_parser.add_argument("--type", choices=["pentest"], default="pentest", help="Type of the report")
    init_parser.add_argument("--title", help="Title of the project", default="Title of the project")
    init_parser.add_argument("-c", "--company", help="Company name", default="Company B.V.")
    init_parser.add_argument("--testtime", help="Time for the test in hours", default=40, type=int)
    init_parser.add_argument("--startdate", help="Start date of the test", default=date.today().strftime("%d-%m-%Y"))
    init_parser.add_argument("--enddate", help="End date of the test", default=date.today().strftime("%d-%m-%Y"))
    init_parser.add_argument("--template", "-t", help="Template to use", default=config.get('template'))
    init_parser.add_argument("--language", "-l", help="Language", default=config.get('language'))
    init_parser.set_defaults(func=init_caller)

    create_issue_parser = subparsers.add_parser("create-issue", aliases=['ci'], help="Create a new issue",)
    create_issue_parser.add_argument("-s", "--standard-issue", help="Create based on the given standard issue")
    create_issue_parser.add_argument("--output_file", help="Output file to store the issue")
    create_issue_parser.add_argument("--title", help="Title of the issue")
    create_issue_parser.add_argument("--cvss-vector", help="CVSS vector", default=config.get('cvss_vector'))
    create_issue_parser.add_argument("--cvss-score", help="CVSS score", default=config.get('cvss_score'))
    create_issue_parser.set_defaults(func=create_issue_caller)

    create_evidence_parser = subparsers.add_parser("create-evidence", aliases=['ce'], help="Create a new evidence")
    create_evidence_parser.add_argument("-l", "--location", help="Where you found the issue", required=config.get('default_location') is None, default=config.get('default_location'))
    create_evidence_parser.add_argument("-o", "--output_file", default=None)
    create_evidence_parser.set_defaults(func=create_evidence_caller)

    clean_parser = subparsers.add_parser("clean", help="Clean the given directory of build files")
    clean_parser.set_defaults(func=clean_caller)

    create_standard_issue_parser = subparsers.add_parser("create-standard-issue", aliases=['csi'], help="Search for a standard issue and create it (requires fzf)")
    create_standard_issue_parser.set_defaults(func=lambda _: run_command("create_standard_issue"))

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_usage()


if __name__ == "__main__":
    main()

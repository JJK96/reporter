import argparse
import argcomplete
from .completers import LocationsCompleter
from .config import REPORT_CONFIG, config, ENFORCE_VERSION, BIN_DIR
from .util import reporter_version, find_report_root, slugify
from datetime import date
import logging
import os

def run_command(command):
    os.system(os.path.join(BIN_DIR, command))

class Commandline:
    subparsers_dict = {}

    def generate_caller(self, args):
        if config.get('reporter_version') != reporter_version:
            message = "This report should be compiled with reporter version {}, while you are using {}. Please install the correct version or change the reporter_version in the configuration file ({})".format(config.get('reporter_version'), reporter_version, REPORT_CONFIG)
            if ENFORCE_VERSION:
                raise Exception(message)
            else:
                logging.warning(message)

        self.template.reporter.generate(preprocess_only=args.preprocess_only)

    def init_caller(self, args):
        self.template.report_manager.init(
            output_dir=args.output_dir,
            type=args.type,
            title=args.title,
            company=args.company,
            testtime=args.testtime,
            startdate=args.startdate,
            enddate=args.enddate,
        )

    def clean_caller(self, args):
        self.template.report_manager.clean()

    def create_issue_caller(self, args):
        if not args.output_file:
            if not args.title:
                raise Exception("Title is required when no output file or standard issue is given")
            args.output_file = os.path.join(find_report_root(), config.get('issue_dir'), slugify(args.title), config.get('issue_filename'))
        self.template.report_manager.create_issue(
            args.output_file,
            title=args.title,
            cvss_vector=args.cvss_vector,
            do_create_evidence=not args.no_evidence,
        )

    def create_standard_issue_caller(self, args):
        if args.standard_issue:
            self.template.report_manager.create_standard_issue(args.standard_issue, args.output_file, do_create_evidence=not args.no_evidence)
            return
        run_command("create_standard_issue")

    def create_evidence_caller(self, args):
        self.template.report_manager.create_evidence(args.location, args.output_file)

    def finalize_caller(self, args):
        self.template.reporter.finalize()

    def locations_caller(self, args):
        for location in self.template.reporter.get_locations():
            print(location)

    def images_caller(self, args):
        for image in self.template.reporter.get_images():
            print(image)

    def find_root_caller(self, args):
        print(find_report_root())

    def standard_issues_caller(self, args):
        for issue in self.template.report_manager.get_standard_issues():
            print(issue)

    def diff_standard_issues_caller(self, args):
        for issue, reason, diff in self.template.reporter.diff_standard_issues(args.show_diff):
            if reason == "new":
                print("Not a standard issue: " + issue.title)
            else:
                differences = reason
                different_fields = '(' + ', '.join(differences) + ')'
                print("Issue differs from standard issue: " + issue.title + " " + different_fields)
                if args.show_diff:
                    import textwrap
                    print(textwrap.indent(diff.decode(), prefix='    '))

    def write_number_caller(self, args):
        self.template.reporter.write_issue_numbers()

    def add_generate_parser(self):
        generate_parser = self.subparsers.add_parser("generate", help="Generate a report")
        self.subparsers_dict['generate'] = generate_parser
        generate_parser.add_argument("--format", "-f", help="Output format", choices=["pdf", "csv"], default="pdf")
        generate_parser.add_argument("--preprocess-only", "-pp", action="store_true", help="Only perform the preprocessing step")
        generate_parser.set_defaults(func=self.generate_caller)

    def add_init_parser(self):
        init_parser = self.subparsers.add_parser("init", help="Inititate a new report")
        self.subparsers_dict['init'] = init_parser
        init_parser.add_argument("output_dir", help="Directory to create the new report in")
        init_parser.add_argument("--type", choices=["pentest"], default="pentest", help="Type of the report")
        init_parser.add_argument("--title", help="Title of the project", default="Title of the project")
        init_parser.add_argument("-c", "--company", help="Company name", default="Company B.V.")
        init_parser.add_argument("--testtime", help="Time for the test in hours", default=40, type=int)
        init_parser.add_argument("--startdate", help="Start date of the test", default=date.today().strftime("%d-%m-%Y"))
        init_parser.add_argument("--enddate", help="End date of the test", default=date.today().strftime("%d-%m-%Y"))
        init_parser.set_defaults(func=self.init_caller)

    def add_create_issue_parser(self):
        create_issue_parser = self.subparsers.add_parser("create-issue", aliases=['ci'], help="Create a new issue",)
        self.subparsers_dict['create_issue'] = create_issue_parser
        create_issue_parser.add_argument("title", help="Title of the issue")
        create_issue_parser.add_argument("--cvss-vector", help="CVSS vector", default=config.get('cvss_vector'))
        create_issue_parser.set_defaults(func=self.create_issue_caller)

        create_standard_issue_parser = self.subparsers.add_parser("create-standard-issue", aliases=['csi'], help="Search for a standard issue and create it (requires fzf)")
        self.subparsers_dict['create_standard_issue'] = create_standard_issue_parser
        create_standard_issue_parser.add_argument("-s", "--standard-issue", help="Create based on the given standard issue")
        create_standard_issue_parser.set_defaults(func=self.create_standard_issue_caller)

        for parser in [create_issue_parser, create_standard_issue_parser]:
            parser.add_argument("--output_file", help="Output file to store the issue")
            parser.add_argument("-n", "--no-evidence", action="store_true", help="Do not create evidence")

    def add_create_evidence_parser(self):
        create_evidence_parser = self.subparsers.add_parser("create-evidence", aliases=['ce'], help="Create a new evidence")
        self.subparsers_dict['create_evidence'] = create_evidence_parser
        create_evidence_parser.add_argument("location", help="Where you found the issue", nargs='?', default=config.get('default_location'))\
            .completer = LocationsCompleter
        create_evidence_parser.add_argument("-o", "--output_file", default=None)
        create_evidence_parser.set_defaults(func=self.create_evidence_caller)

    def add_clean_parser(self): 
        clean_parser = self.subparsers.add_parser("clean", help="Clean the given directory of build files")
        self.subparsers_dict['clean'] = clean_parser
        clean_parser.set_defaults(func=self.clean_caller)

    def add_finalize_parser(self):
        finalize_parser = self.subparsers.add_parser("finalize", help="Copy the output report to a final version with a default name")
        self.subparsers_dict['finalize'] = finalize_parser
        finalize_parser.set_defaults(func=self.finalize_caller)

    def add_locations_parser(self):
        locations_parser = self.subparsers.add_parser("locations", help="Get all locations used in the report")
        self.subparsers_dict['locations'] = locations_parser
        locations_parser.set_defaults(func=self.locations_caller)

    def add_images_parser(self):
        images_parser = self.subparsers.add_parser("images", help="Get all images available in the report")
        self.subparsers_dict['images'] = images_parser
        images_parser.set_defaults(func=self.images_caller)

    def add_standard_issues_parser(self):
        standard_issues_parser = self.subparsers.add_parser("standard-issues", help="List all standard issues")
        self.subparsers_dict['standard_issues'] = standard_issues_parser
        standard_issues_parser.set_defaults(func=self.standard_issues_caller)

    def add_find_root_parser(self):
        find_root_parser = self.subparsers.add_parser("find-root", help="Find the root of this report")
        self.subparsers_dict['find_root'] = find_root_parser
        find_root_parser.set_defaults(func=self.find_root_caller)

    def add_diff_standard_issues_parser(self):
        diff_standard_issues_parser = self.subparsers.add_parser("diff-standard-issues", help="List all issues that are not in the standard issues library.")
        self.subparsers_dict['diff_standard_issues'] = diff_standard_issues_parser
        diff_standard_issues_parser.add_argument("-d", "--show_diff", action="store_true", help="Show full git diff")
        diff_standard_issues_parser.set_defaults(func=self.diff_standard_issues_caller)

    def add_write_number_parser(self):
        write_number_parser = self.subparsers.add_parser("write-numbers", help="Write issue numbers back to the issue files")
        self.subparsers_dict['write_number'] = write_number_parser
        write_number_parser.set_defaults(func=self.write_number_caller)

    def add_common_args(self):
        for p in self.subparsers_dict.values():
            p.add_argument("--language", "-l", help="Language", default=config.get('language'))

    def add_subparsers(self):
        self.add_clean_parser()
        self.add_create_evidence_parser()
        self.add_create_issue_parser()
        self.add_finalize_parser()
        self.add_find_root_parser()
        self.add_generate_parser()
        self.add_init_parser()
        self.add_locations_parser()
        self.add_images_parser()
        self.add_standard_issues_parser()
        self.add_diff_standard_issues_parser()
        self.add_write_number_parser()

    def parse_args(self):
        args = self.parser.parse_args()
        if hasattr(args, 'language') and args.language != self.template.language:
            self.template.language = args.language
        if hasattr(args, 'func'):
            try:
                args.func(args)
            except Exception as e:
                if args.debug:
                    raise e
                else:
                    print(e)
                    return
        else:
            self.parser.print_usage()

    def __init__(self, template):
        self.template = template
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--debug", action="store_true", help="Debug mode")
        self.subparsers = self.parser.add_subparsers(help='Subcommands')
        self.add_subparsers()
        self.add_common_args()        
        argcomplete.autocomplete(self.parser)


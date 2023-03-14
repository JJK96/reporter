from os.path import realpath, dirname, join
import configparser
from .util import find_report_root, ReportRootNotFound, reporter_version

severities = [
    "critical",
    "high",
    "medium",
    "low",
    "none",
]

dir = realpath(dirname(__file__))

DEFAULT_TEMPLATE = "default"

DEFAULT_LANGUAGE = "en"

BASE_TEMPLATE = "default"

# Enforec that the report is compiled with the correct version
ENFORCE_VERSION = False

# Directory with templates
TEMPLATES_DIR = join(dir, "../templates")

# Directory with issue templates
ISSUE_TEMPLATES_DIR = join(dir, "../issue_templates")

# Directory with supporting files
NECESSARY_FILES_DIR = join(dir, "../necessary_files")

# Directory with files for initiating a new report
REPORT_INIT_DIR = join(dir, "../report_init")

# Directory containing standard issues
STANDARD_ISSUE_DIR = join(dir, "../standard-issue-library")

# Directory with bash scripts that can be executed
BIN_DIR = join(dir, "../bin")

# Report config file name
REPORT_CONFIG = "reporter.ini"

#########
# Directories within template
#########

# Directory with files necessary for compiling the full report
REPORT_TEMPLATE_DIR = "report"

# Directory with yaml files containing content for jinja templating
STATIC_CONTENT_DIR = "static_content"

STATIC_IMAGES_DIR = "static_images"

DYNAMIC_TEXT_LIB = "dynamic_text.py"

CONFIG_LIB = "config.py"

REPORTER_LIB = "reporter.py"

COMMANDLINE_LIB = "commandline.py"

REPORT_MANAGER_LIB = "report_manager.py"

PARENTS_FILE = "parents.txt"

########
# Overridable settings
# These settings can be overridden in a report-specific config file
########

DEFAULTS = {
    # Some default values
    "issue_title": "Title of the issue",
    "issue_filename": "issue.dradis",
    "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N",
    # Filename of main latex file for report
    "report_file": 'report.tex',
    "report_output_file": 'report.pdf',
    "language": DEFAULT_LANGUAGE,
    # Standard name of issue
    "issue_name": "issue.dradis",
    "cache_dir": '.cache',
    # Output dir is relative to cache dir
    "output_dir": 'output',
    "templates_output_dir": 'templates',
    "issue_dir": 'issues',
    "template": DEFAULT_TEMPLATE,
    "reporter_version": reporter_version,
    "show_locations": True,
    "default_location": "evidence",
}

parser = configparser.ConfigParser()
parser['DEFAULT'] = DEFAULTS

try:
    report_root = find_report_root()    
    parser.read(join(report_root, REPORT_CONFIG))
except ReportRootNotFound:
    # If not in a report dir, just do nothing
    pass

try:
    config = parser['report']
except KeyError:
    config = parser['DEFAULT']

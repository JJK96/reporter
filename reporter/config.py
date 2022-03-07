from os.path import realpath, dirname, join

severities = [
    "critical",
    "high",
    "medium",
    "low",
    "none",
]

OUTPUT_DIR = '.cache'
ISSUE_DIR = 'issues'
dir = realpath(dirname(__file__))

DEFAULT_TEMPLATE = "default"

BASE_TEMPLATE = "default"

# Directory with templates
TEMPLATES_DIR = join(dir, "../templates")

# Directory with issue templates
ISSUE_TEMPLATES_DIR = join(dir, "../issue_templates")

# Directory with supporting files
NECESSARY_FILES_DIR = join(dir, "../necessary_files")

# Directory with files for initiating a new report
REPORT_INIT_DIR = join(dir, "../report_init")

# Filename of main latex file for report
REPORT_FILE = 'report.tex'

# Directory containing standard issues
STANDARD_ISSUE_DIR = join(dir, "../standard-issue-library")

# Directory with bash scripts that can be executed
BIN_DIR = join(dir, "../bin")

# Standard name of issue
ISSUE_NAME = "issue.dradis"

# Some default values
DEFAULTS = {
    "issue": {
        "title": "Title of the issue",
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N",
        "cvss_score": "0.0",
    }
}

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

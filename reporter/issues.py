from textile_parser import parse_textile_file, check_issue
from .cvss_util import score_to_severity, vector_to_score
from .config import config
import yaml
import os
import shutil

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


class Issue:
    content: dict

    def __init__(self, content):
        if 'number' in content:
            content['number'] = int(content['number'])
        self.content = content

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
    def cvss_score(self):
        return vector_to_score(self.cvss_vector)

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

from reporter.dynamic_text import dynamic_text_generators


def run_with_content(content):
    generator = dynamic_text_generators.get("en")
    generator(content).generate()
    output = content['findings_summary']
    assert "  " not in output
    print(output)


def test_english_no_issues():
    content = {
        "num_issues": 0,
        "num_severity": {}
    }
    run_with_content(content)


def test_english_one_issue():
    content = {
        "num_issues": 1,
        "num_severity": {
            "critical": 1
        }
    }
    run_with_content(content)

    content = {
        "num_issues": 1,
        "num_severity": {
            "medium": 1
        }
    }
    run_with_content(content)


def test_english_multiple_issues():
    content = {
        "num_issues": 3,
        "num_severity": {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 0,
            "none": 0,
        }
    }
    run_with_content(content)

    content = {
        "num_issues": 3,
        "num_severity": {
            "critical": 0,
            "high": 0,
            "medium": 2,
            "low": 0,
            "none": 0,
        }
    }
    run_with_content(content)

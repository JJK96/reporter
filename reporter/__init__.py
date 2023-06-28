from .reporter import Template
from .config import config


def get_template():
    template = Template(config.get('template'))
    return template


def main():
    template = get_template()
    template.commandline.parse_args()

if __name__ == "__main__":
    main()

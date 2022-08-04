from .reporter import Template
from .config import config


def main():
    template = Template(config.get('template'))
    template.commandline.parse_args()

if __name__ == "__main__":
    main()

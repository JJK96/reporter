from .reporter import Template
from .config import config

def LocationsCompleter(**kwargs):
    template = Template(config.get('template'), language=config.get('lanaguage'))
    locations = template.reporter.get_locations()
    return list(locations)


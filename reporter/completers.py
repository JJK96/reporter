from .config import config

def LocationsCompleter(template, **kwargs):
    from .reporter import Template
    template = Template(config.get('template'), language=config.get('lanaguage'))
    locations = template.reporter.get_locations()
    return list(locations)


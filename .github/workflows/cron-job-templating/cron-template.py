#!/usr/bin/env python

import yaml
import sys
from jinja2 import Template
from jinja2.environment import Environment

def validate_epoch_input(cli_args):
    try:
        epoch_input = cli_args[1]
    except:
        raise ValueError('Missing required parameter. Epoch must be provided.')

    try:
        epoch = float(epoch_input)
    except:
        raise ValueError('Invalid epoch. Please enter an epoch in the following format: "yyyy.mm"')

    return epoch

def _yaml_parsing(cron_recipe):
    with open(cron_recipe) as fh:
        parsed_recipe = yaml.load(fh, Loader=yaml.FullLoader)

    return parsed_recipe

# TODO: separate filepath param into os & ubuntu filepaths
def write_recipe(jinja, output_filepath, parsed_recipe):
    with open(jinja) as fh:
        template = Template(fh.read())

    recipe_reqs = template.render(parsed_recipe)

    # TODO: create for-loop for both os
    with open(output_filepath, 'w') as fh:
        fh.write(recipe_reqs)

if __name__ == '__main__':

    class JinjaEnvironment(Environment):
        def __init__(self,**kwargs):
            super(JinjaEnvironment, self).__init__(**kwargs)
            self.globals['INPUT_EPOCH'] = validate_epoch_input(sys.argv[1])
            
    parsed_cron_recipe = _yaml_parsing('cron-recipe.yaml')
    write_recipe('jinja-template.j2', 'cron-output.yaml', parsed_cron_recipe)
#!/usr/bin/env python

import sys
from jinja2 import Template


def validate_inputs(cli_args):
    try:
        epoch = cli_args[1]
    except Exception:
        raise ValueError('Missing required parameter. '
                         'Epoch must be provided.')

    return epoch


if __name__ == '__main__':

    def write_recipe(jinja):
        epoch = validate_inputs(sys.argv)
        with open(jinja) as fh:
            template = Template(fh.read())
            for os in 'macos', 'ubuntu':
                filename = 'cron-' + epoch + '-core-' + os + '-latest.yaml'
                with open(filename, 'w') as outfile:
                    outfile.write(template.render(input_epoch=epoch,
                                                  input_os=os))

    write_recipe('cron-workflow-template.j2')

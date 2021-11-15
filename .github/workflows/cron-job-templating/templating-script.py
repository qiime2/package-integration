#!/usr/bin/env python

import sys
from jinja2 import Template


def validate_epoch_input(cli_args):
    try:
        epoch = cli_args[1]
    except Exception:
        raise ValueError('Missing required parameter. Epoch must be provided.')

    return epoch


def write_recipe(jinja):
    epoch = validate_epoch_input(sys.argv)
    with open(jinja) as fh:
        template = Template(fh.read())
        for os in 'macos', 'ubuntu':
            filename = 'cron-' + epoch + '-core-' + os + '-latest.yaml'
            outfile = open(filename, 'w')
            outfile.write(template.render(input_epoch=epoch, input_os=os))
            outfile.close()


if __name__ == '__main__':

    write_recipe('cron-template.j2')

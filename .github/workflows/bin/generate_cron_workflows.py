#!/usr/bin/env python

import sys
from jinja2 import Environment, FileSystemLoader


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
        for os in 'macos', 'ubuntu':
            filename = 'cron-' + epoch + '-core-' + os + '-latest.yaml'
            env = Environment(loader=FileSystemLoader('templates'),
                              variable_start_string='{{{',
                              variable_end_string='}}}')
            template = env.get_template(jinja)
            with open(filename, 'w') as outfile:
                if os == 'macos':
                    opsys = 'osx'
                else:
                    opsys = 'linux'
                outfile.write(template.render(input_epoch=epoch,
                                              input_os=os, op_sys=opsys))

    write_recipe('cron-workflow-template.j2')

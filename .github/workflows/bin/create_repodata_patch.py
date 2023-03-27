#!/usr/bin/env python
import yaml
import json
import os
import sys
import subprocess
import copy
from collections import defaultdict


LOCAL_CHANNEL = './patched_base/'
CONFIG_FP = f'{LOCAL_CHANNEL}/config.yaml'
SUBDIRS = ['linux-64', 'noarch', 'osx-64']
CMD_TEMPLATE = ('conda-mirror --upstream-channel %s --target-directory %s '
                '--platform %s --config %s')


def write_config(cbc_yaml):
    config_yaml = {'blacklist': [{'name': '*'}]}
    whitelist = []

    for pkg, version in cbc_yaml.items():
        version = version[0]
        if pkg.startswith('q2') or pkg == 'qiime2':
            pkg = pkg.replace('_', '-')
            whitelist.append({'name': pkg, 'version': f'{version}'})

    config_yaml['whitelist'] = whitelist
    with open(CONFIG_FP, 'w') as fh:
        yaml.safe_dump(config_yaml, fh)


def create_channel():
    for subdir in SUBDIRS:
        cmd = CMD_TEMPLATE % (REMOTE_CHANNEL, LOCAL_CHANNEL, subdir, CONFIG_FP)
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()


def _patch_repodata(repodata, changes):
    packages = repodata['packages']
    instructions = {
        'patch_instructions_version': 1,
        'packages': defaultdict(dict),
        'revoke': [],
        'remove': [],
    }
    # If we only want to patch the newest version of the downstream package
    # that's in repodata I can probably use timestamps
    for updated, downstream in changes.items():
        updated_pkg, new_version = updated
        for pkg, info in packages.items():
            if info['name'] in downstream:
                deps = info['depends']
                for idx, dep in enumerate(deps):
                    if updated_pkg == dep.split()[0]:
                        if instructions['packages'].get(pkg, None) is None:
                            instructions['packages'][pkg] = {}
                            instructions['packages'][pkg]['depends'] = \
                                copy.deepcopy(packages[pkg]['depends'])
                        instructions['packages'][pkg]['depends'][idx] = \
                            f'{updated_pkg} {new_version}'
                        break

    return instructions


def patch_channels(filtered_cbc_yaml, versioned_filtered_dict):
    patch_instructions = {}

    for subdir in SUBDIRS:
        # The channel name might not end up just being a filepath but we will
        # see, depends on what happens with the github workers and whatever
        with open(os.path.join(LOCAL_CHANNEL,
                               subdir, 'repodata.json'), 'r') as fh:
            repodata = json.load(fh)

        versioned_tuple_filtered_dict = {}
        for pkg, version in filtered_cbc_yaml.items():
            version = version[0]
            versioned_tuple_filtered_dict[(pkg, version)] = \
                versioned_filtered_dict[pkg + '-' + version]

        patch_instructions = _patch_repodata(repodata,
                                             versioned_tuple_filtered_dict)

        # Similar to the above this filepath
        # probably won't look quite like this in the end
        with open(os.path.join(LOCAL_CHANNEL,
                               subdir, 'patch_instructions.json'), 'w') as fh:
            json.dump(patch_instructions, fh, indent=2,
                      sort_keys=True, separators=(",", ": "))


if __name__ == '__main__':
    (conf_epoch,
     cbc_yaml_fp,
     filtered_cbc_yaml_fp,
     versioned_filtered_dict_fp) = sys.argv[1:]

    REMOTE_CHANNEL = f'https://packages.qiime2.org/qiime2/{conf_epoch}/tested'

    with open(cbc_yaml_fp, 'r') as fh:
        cbc_yaml = json.load(fh)

    with open(filtered_cbc_yaml_fp, 'r') as fh:
        filtered_cbc_yaml = json.load(fh)

    with open(versioned_filtered_dict_fp, 'r') as fh:
        versioned_filtered_dict = json.load(fh)

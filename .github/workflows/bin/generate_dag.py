#!/usr/bin/env python
import urllib.request
import json
import re
import sys

import yaml
import jinja2
import networkx as nx
from jinja2 import FileSystemLoader
from ghapi.all import GhApi, paged

# Helper methods ##


# Helper for parsing CBC and tested channel URLs
def _fetch_url(url):
    http_response = urllib.request.urlopen(url)
    obj = http_response.read().decode('utf-8')

    return obj


def get_library_packages():
    response = urllib.request.urlopen(
        'https://library.qiime2.org/api/v2/packages')
    return json.load(response)['packages']


# Parses the cmd line diff into a dict with pkgs added, changed, and removed
def find_diff(diff):
    dependency = r"\n?.*:\n"
    # `\n?.*\n` -> matches any line that ends with colon,
    #              will match dependency name line
    added_dependency = r"\n?\+.*:\n"
    # same as above but match when line begins with '+'
    removed_dependency = r"\n?-.*:\n"
    # same as above but match when line begins with '-'

    removed_version = r"\n?-\t? *- '?[(<=)(>=)]?[0-9]+\..*'?"
    # `\n?` -> optional newline
    # `- ` -> diff syntax for line in old file
    # `\t *` -> optional tab and any number of spaces (identation in yaml)
    # `'?` -> optional quote in version line
    # `[(<=)(>=)]?` -> optional '>=' or '<=' in version
    # `[0-9]+\.` -> a version number followed by a dot followed by anything
    #               else
    # `'?` -> optional close quote
    added_version = r"\n?\+\t? *- '?[(<=)(>=)]?[0-9]+\..*'?\n"
    # same as above but line begins with '+'

    version_change_pattern = rf"{dependency}{removed_version}{added_version}"
    added_dependency_pattern = rf"{added_dependency}{added_version}"
    removed_dependency_pattern = rf"{removed_dependency}{removed_version}"

    with open(diff, 'r') as file:
        contents = file.read()
        version_change_matches = re.findall(version_change_pattern, contents)
        added_dependency_matches = re.findall(added_dependency_pattern,
                                              contents)
        removed_dependency_matches = re.findall(removed_dependency_pattern,
                                                contents)

    changed_pkgs = [match.split('=')[0].strip()
                    for match in version_change_matches]
    added_pkgs = [match.split('=')[0].strip().strip('+')
                  for match in added_dependency_matches]
    removed_pkgs = [match.split('=')[0].strip().strip('-')
                    for match in removed_dependency_matches]

    pkgs = {
        'changed_pkgs': changed_pkgs,
        'added_pkgs': added_pkgs,
        'removed_pkgs': removed_pkgs,
    }

    return pkgs


def get_minimal_env(seed_env_path):
    with open(seed_env_path) as fh:
        env = yaml.safe_load(fh)

    return dict(entry.split('=') for entry in env['dependencies'])


# Get current distro dep structure from repodata.json under tested channel
def get_distro_deps(epoch, conda_subdir, relevant_pkgs):
    missing_pkgs = relevant_pkgs.copy()
    # TODO: update tested/ to staged/ once library does that also
    q2_pkg_channel_url = (f'https://packages.qiime2.org/qiime2/{epoch}/'
                          f'tested/{conda_subdir}/repodata.json')
    response = _fetch_url(q2_pkg_channel_url)
    repodata = json.loads(response)

    # this is what's pulled from our tested channel on packages.qiime2.org
    q2_dep_dict = {}

    for info in repodata['packages'].values():
        name = info['name']
        if (name not in missing_pkgs
                or missing_pkgs[name] != info['version']):
            continue
        del missing_pkgs[name]
        q2_dep_dict[name] = [dep.split(' ')[0] for dep in info['depends']]

    if missing_pkgs:
        raise Exception(f'Missing the following packages in the channel:'
                        f'{missing_pkgs}')

    return q2_dep_dict


def get_packages_to_rebuild(relevant_pkgs, library_pkgs):
    api = GhApi()
    repos = lookup_repos(relevant_pkgs, library_pkgs)
    return find_packages_to_build(api, repos, 'test-pr')


def lookup_repos(packages, repo_map):
    packages_to_check = {
        pkg: tuple(repo_map[pkg].split('/'))
        for pkg in repo_map.keys() & set(packages)
    }
    return packages_to_check


def is_branch_in_pager(pager, branch):
    for page in pager:
        for page_branch in page:
            if branch == page_branch['name']:
                return True
    return False


def find_packages_to_build(api, repos, branch):
    to_build = {}
    for name, repo in repos.items():
        pager = paged(api.repos.list_branches, *repo)
        if is_branch_in_pager(pager, branch):
            to_build[name] = repo
    return to_build


def get_source_revdeps(dag, distro_dep_dict, all_changes):
    src_revdeps = {}
    for pkg in all_changes:
        revdeps = [edge[1] for edge in dag.out_edges(pkg)]
        src_revdeps[pkg] = revdeps

    return src_revdeps


# Create new DiGraph object & add list of pkgs from a given pkg dict as nodes
def make_dag(pkg_dict):
    print(pkg_dict)
    dag = nx.DiGraph()
    # Add edges connecting each pkg to their list of deps
    for pkg, deps in pkg_dict.items():
        for dep in deps:
            dag.add_edge(dep, pkg)

    return dag


# Convert DAG subplot to mermaid diagram for use in job summary
def to_mermaid(G, highlight_from=None):
    lookup = {n: f'{i:x}' for i, n in enumerate(sorted(G.nodes, reverse=True))}

    if highlight_from is None:
        highlight_from = set()
    else:
        highlight_from = set(highlight_from)

    build = set()
    for parent in highlight_from:
        build.update([x[1] for x in G.out_edges(parent)])
        build.add(parent)

    build = [lookup[x] for x in build]

    G = nx.transitive_reduction(G)

    lines = ['flowchart LR']
    for key, value in lookup.items():
        lines.append(f'{value}["{key}"]')

    test = set()
    for parent in highlight_from:
        test.update(nx.descendants(G, parent))
        test.add(parent)

    test = [lookup[x] for x in test]

    edges = []
    for idx, (a, b) in enumerate(sorted(G.edges)):
        lines.append(f'{lookup[a]} --> {lookup[b]}')
        if lookup[a] in test:
            edges.append(str(idx))

    lines.append('linkStyle default opacity:0.25')
    if edges:
        lines.append(f'linkStyle {",".join(edges)} opacity:1')
    lines.append('classDef default fill:#e0f2fe,stroke:#7dd3fc')
    if test:
        lines.append('classDef test fill:#38bdf8,stroke:#0284c7')
        lines.append(f'class {",".join(test)} test')
    if build:
        lines.append('classDef build fill:#818cf8,stroke:#4f46e5')
        lines.append(f'class {",".join(build)} build')
    if highlight_from:
        lines.append('classDef origin fill:#f472b6,stroke:#ec4899')
        lines.append(
            f'class {",".join([lookup[parent] for parent in highlight_from])} '
            'origin')
    return '\n'.join(lines)


def main(epoch, distro, seed_env_path, diff_path, conda_subdir,
         gh_summary_path, rebuild_matrix_path, retest_matrix_path,
         packages_in_distro_path, full_distro_path, revdeps_of_sources_path):

    library_pkgs = get_library_packages()

    diff = find_diff(diff_path)

    new_pkgs = diff['added_pkgs']
    changed_pkgs = diff['changed_pkgs']
    removed_pkgs = diff['removed_pkgs']
    all_changes = [*new_pkgs, *changed_pkgs, *removed_pkgs]
    print(all_changes)
    # TODO: don't test a source which was removed, since it isn't there.
    # TODO: if the removed is a terminal node in the dag, we need to change the
    # test plan/skip doing anything interesting at all

    relevant_pkgs = get_minimal_env(seed_env_path)
    plugin_pkgs = {k, v for k, v in relevant_pkgs.items() if k in library_pkgs}
    distro_deps = get_distro_deps(epoch, conda_subdir, plugin_pkgs)

    core_dag = make_dag(pkg_dict=distro_deps)
    core_sub = nx.subgraph(core_dag, relevant_pkgs)

    pkgs_to_rebuild = get_packages_to_rebuild(relevant_pkgs, library_pkgs)
    all_changes.extend(list(pkgs_to_rebuild))

    rebuild_generations = list(nx.topological_generations(
        nx.induced_subgraph(core_sub, pkgs_to_rebuild)
    ))

    if len(rebuild_generations) > 6:
        raise Exception(f"Too many generations: {rebuild_generations}")

    src_revdeps = get_source_revdeps(core_dag, distro_deps, all_changes)

    pkgs_to_test = list(set.union(set(src_revdeps),
                                  *(nx.descendants(core_dag, pkg)
                                    for pkg in src_revdeps)))

    core_mermaid = to_mermaid(core_sub, highlight_from=src_revdeps)

    environment = jinja2.Environment(
        loader=FileSystemLoader(".github/workflows/bin/templates"))
    template = environment.get_template("job-summary-template.j2")

    with open(gh_summary_path, 'w') as fh:
        fh.write(template.render(epoch=epoch,
                                 distro=distro,
                                 core_mermaid=core_mermaid,
                                 source_dep_dict=src_revdeps,
                                 pkgs_to_test=pkgs_to_test))

    with open(rebuild_matrix_path, 'w') as fh:
        json.dump(rebuild_generations, fh)

    with open(retest_matrix_path, 'w') as fh:
        json.dump(pkgs_to_test, fh)

    with open(packages_in_distro_path, 'w') as fh:
        pkgs_in_distro = {
            k: v for k, v in relevant_pkgs.items()
            if k in library_pkgs
        }
        json.dump(pkgs_in_distro, fh)

    with open(full_distro_path, 'w') as fh:
        json.dump(relevant_pkgs, fh)

    with open(revdeps_of_sources_path, 'w') as fh:
        json.dump(src_revdeps, fh)


if __name__ == '__main__':
    epoch = sys.argv[1]
    distro = sys.argv[2]
    seed_env_path = sys.argv[3]
    diff_path = sys.argv[4]
    conda_subdir = sys.argv[5]
    gh_summary_path = sys.argv[6]
    rebuild_matrix_path = sys.argv[7]
    retest_matrix_path = sys.argv[8]
    packages_in_distro_path = sys.argv[9]
    full_distro_path = sys.argv[10]
    revdeps_of_sources_path = sys.argv[11]

    main(epoch, distro, seed_env_path, diff_path, conda_subdir,
         gh_summary_path, rebuild_matrix_path, retest_matrix_path,
         packages_in_distro_path, full_distro_path, revdeps_of_sources_path)

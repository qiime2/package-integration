import argparse
import os
import subprocess


def main(epochs):
    seen = None
    changed_files = get_changed()

    for file in changed_files:
        for epoch in epochs:
            if epoch in file:
                if seen is None:
                    seen = epoch
                elif seen == epoch:
                    pass
                else:
                    raise Exception('PR updates multiple epochs, please split')

    if seen is None:
        raise Exception('No matches')

    print(seen, end='')

def get_changed():
    base = os.environ['GITHUB_BASE_REF']
    head = os.environ['GITHUB_HEAD_REF']
    cmd = ['git', 'diff', '--name-only', '%s...%s' % (base, head)]
    captured = subprocess.run(cmd, capture_output=True, text=True)
    files = captured.stdout.split('\n')
    files = [f for f in files if f != '']
    if not files:
        raise Exception('No files changed?!')
    return files

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='determine epochs changed')
    parser.add_argument('epochs', type=str, help='space-separated list of epochs')

    args = parser.parse_args()
    epochs = args.epochs.split(' ')  # these should stay as strings

    main(epochs)

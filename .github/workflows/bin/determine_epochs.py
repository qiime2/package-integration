import argparse


def main(epochs, changed_files):
    seen = set()

    for file in changed_files:
        for epoch in epochs:
            if epoch in file:
                seen.add(epoch)

    if not seen:
        raise Exception('No matches')

    print(list(seen), end='')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='determine epochs changed')
    parser.add_argument('epochs', type=str, help='space-separated list of epochs')
    parser.add_argument('changed_files', type=str, help='space-separated list of changed files')

    args = parser.parse_args()
    epochs = args.epochs.split(' ')  # these should stay as strings
    changed_files = args.changed_files.split(' ')

    main(epochs, changed_files)

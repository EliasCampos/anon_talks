import argparse
from anon_talks import start, sync_db


def main():
    commands = {
        'run': start,
        'syncdb': sync_db,
    }

    arg_parser = argparse.ArgumentParser(description='Managament commands.')
    arg_parser.add_argument('command', choices=tuple(commands))

    args = arg_parser.parse_args()
    command = commands[args.command]
    command()


if __name__ == '__main__':
    main()

import argparse
from anon_talks import start, sync_db


def main():
    commands = ('run', 'syncdb')

    arg_parser = argparse.ArgumentParser(description='Managament commands.')
    arg_parser.add_argument('command', choices=commands)
    arg_parser.add_argument('--sock_name')

    args = arg_parser.parse_args()
    if args.command == 'syncdb':
        sync_db()
    else:
        start(socket_name=args.sock_name)


if __name__ == '__main__':
    main()

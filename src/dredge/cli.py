import argparse
import sys
from . import __version__

def main(argv=None):
    parser = argparse.ArgumentParser(prog="dredge", description="DREDGE CLI")
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    parser.print_help()
    return 0

if __name__ == "__main__":
    sys.exit(main())

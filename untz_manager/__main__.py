"""Main entry point for untz."""
import argparse


def args():
    """Parse and return arguments."""
    parser = argparse.ArgumentParser(description="Convert FLACs to OGGs and "
                                                 "sort into a sensible folder hierarchy.")
    parser.add_argument("--output", "-o",
                        help="Folder to store output files to.", required=True)
    parser.add_argument("--passthrough", "-p",
                        help="Additional CLI arguments to pass through to oggenc.",
                        default="")
    parser.add_argument("--quality", "-q",
                        type=float,
                        default=10,
                        help="Sets encoding quality to n, between -1 (low) and 10 (high). "
                             "Fractional quality levels such as 2.5 are permitted.")
    parser.add_argument(dest="input_files", help="List of folder/file inputs.", nargs="+")

    return parser.parse_args()


def main():
    """Main logic for untz."""
    arguments = args()
    print(arguments)

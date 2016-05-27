"""Main entry point for untz."""
import argparse


def args():
    """Parse and return arguments."""
    parser = argparse.ArgumentParser(description="Convert FLACs to OGGs and "
                                                 "sort into a sensible folder hierarchy.")
    parser.add_argument("--names", "-n",
                        default="%n - %t",
                        dest="pattern",
                        help="Produce filenames as this string, with %%g, %%a, %%l, %%n, %%t, %%d "
                             "replaced by genre, artist, album, track number, title, "
                             "and date, respectively. Also, %%%% gives a literal %%. "
                             "Defaults to %%n - %%t.")
    parser.add_argument("--output", "-o",
                        dest="output_files",
                        help="Folder to store output files to.", required=True)
    parser.add_argument("--passthrough", "-p",
                        dest="ogg_cli_parameters",
                        help="Additional CLI arguments to pass through to oggenc.",
                        default="")
    parser.add_argument("--quality", "-q",
                        dest="quality",
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

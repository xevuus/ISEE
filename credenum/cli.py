import argparse
import sys

from rich.console import Console

from credenum.report import build_report, render_json, render_rich

# Two separate raw strings instead of one BANNER: rich lets us give the
# block-letter "ISEE" title and the portrait underneath different colors,
# which reads better than one flat color across two very different kinds
# of ASCII/Unicode art. Raw strings (r"""...""") so the literal
# backslashes in the block letters print as-is instead of Python trying
# to interpret them as escape sequences like \_ or \n.
BANNER_TITLE = r""" .___  _______________________________
|   |/   _____/\_   _____/\_   _____/
|   |\_____  \  |    __)_  |    __)_
|   |/        \ |        \ |        \
|___/_______  //_______  //_______  /
            \/         \/         \/"""

BANNER_IMAGE = r"""⡿⢿⠛⣻⠿⢿⡿⢿⠿⠿⠻⠿⠿⢿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⡿⠿⠟⠟⠿⣿⣿⢿⣿⠿⣛⠟⡻⢿
⣿⣶⣲⣾⣯⣥⣈⡀⡀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠛⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠉⠁⠀⠀⠀⠀⠀⠀⠀⢀⢀⣁⣬⣽⣗⣶⣶⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣤⣀⡀⠀⠀⠀⠀⠀⠀⠀⠉⠻⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣶⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣦⣄⢀⠀⠀⠀⠀⠀⠉⠛⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠛⠉⠀⠀⠀⠀⠀⡀⣠⣤⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⡿⠿⠿⠟⠛⠛⠛⠛⠛⠛⠛⠋⠁⠉⠓⠲⠄⢀⠀⠀⠀⠈⠈⠹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠏⠁⠀⠀⠀⠀⠀⠠⠖⠚⠉⠈⠙⠋⠋⠛⠛⠛⠛⠛⠻⠿⠿⢿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⠟⠋⠀⠀⢀⠠⠆⠷⠄⠛⠹⠊⠓⠰⠆⡄⣀⣠⡀⠀⠀⠀⢰⣶⣴⣦⣦⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣽⣤⣴⡦⣦⠄⠀⠀⠀⠀⣄⣀⢠⠰⠖⠚⠱⠏⠚⠠⠿⠰⠄⡀⠀⠈⠙⠻⣿⣿⣿⣿
⡿⣿⣿⢷⣦⡝⠛⠽⠚⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠳⣤⡀⠀⠀⠈⠁⠈⠝⠻⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠋⠀⠈⠁⠀⠀⢀⣦⠞⠈⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠐⠓⠯⠛⢣⣔⡾⣿⣿⢿
⣧⡙⢿⡏⠚⠌⠀⠀⣠⣴⣿⣿⡁⠀⠀⠀⠄⠀⠀⢀⠀⠀⣠⡈⢻⣴⡀⠀⠀⠀⠀⠀⠈⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠁⠀⠀⠀⠀⠀⢀⣦⡟⢁⣄⠀⠀⡀⠀⠀⠠⠀⠀⠀⢈⣿⣿⣶⣄⠀⠀⠩⠓⢼⠯⢋⣸
⣿⣷⣮⣁⣠⣤⣤⡄⣿⣿⣿⣿⣇⠀⠀⠀⠀⠀⠀⠈⠀⠀⣿⣷⣬⠙⢷⣤⡀⠀⠀⠀⠀⠈⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠁⠀⠀⠀⠀⢀⣤⡞⢋⣡⣾⣿⠀⠀⠁⠀⠀⠀⠀⠀⠀⣸⣿⣿⣿⣿⣀⣤⣤⣀⣨⣤⣾⣿
⣿⣿⣿⣯⢿⢿⠛⣿⣿⣿⣿⣿⣿⣆⠀⠀⠀⠀⠀⠀⢀⣼⣿⣿⣿⣷⡀⠙⣿⣷⣾⣶⣄⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⣠⣶⣷⣷⣿⠏⢀⣾⣿⣿⣿⣧⡀⠀⠀⠀⠀⠀⠀⣠⣿⣿⣿⣿⣿⣿⠻⡻⣿⣽⣿⣿⣿
⣿⣿⣿⣿⣯⡓⠀⠘⠛⡿⣿⣿⣿⣿⣿⣶⣤⣤⣴⣶⣿⣿⣿⣿⣿⣯⣥⣬⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⣬⣬⣼⣿⣿⣿⣿⣿⣶⣦⣤⣤⣶⣾⣿⣿⣿⣿⢿⠛⠈⠆⢺⣽⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣧⣧⡗⡜⣰⠀⡨⠙⠙⠙⠙⠿⠻⡿⠻⢙⣹⣿⣏⣷⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣾⣹⣿⡯⡏⡟⠻⠟⠿⠋⠋⠋⠉⢄⢈⣶⢣⢻⠸⣼⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣯⣷⣷⡆⢠⡇⡼⣆⣰⢰⢰⡅⣷⣰⣳⣿⡿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣳⡿⣿⣿⣜⣯⣾⢀⡆⣤⣖⣸⣧⢸⡄⣤⣾⣾⣽⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣿⢥⣿⣾⣼⣟⣿⣽⣿⣷⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⣿⣿⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="credenum",
        description="Hunt for passwords, SSH keys, and tokens on a Linux system.",
    )
    parser.add_argument(
        "--root",
        default="/home",
        help="Directory to start searching from (default: /home)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--skip-process",
        action="store_true",
        help="Skip scanning running processes (/proc) -- useful for tests/CI, "
             "where matching against whatever happens to be running isn't deterministic",
    )
    return parser


def main() -> None:
    console = Console()
    # bold magenta for the block-letter title, dim cyan for the portrait --
    # rich picks up "[style]...[/style]" markup the same way it would in
    # render_rich, so this reuses the exact same syntax we'll see there.
    console.print(f"[bold magenta]{BANNER_TITLE}[/bold magenta]")
    console.print(f"[dim cyan]{BANNER_IMAGE}[/dim cyan]")

    parser = build_parser()
    args = parser.parse_args()

    findings = build_report(args.root, include_process=not args.skip_process)

    if args.format == "json":
        print(render_json(findings))
    else:
        render_rich(findings, console=console)

    # Exit code conventions matter for scripting: 0 means "ran fine, all
    # clear" so `credenum && deploy.sh` only proceeds when nothing was
    # found. 1 means "ran fine, but found something" -- distinct from
    # argparse's own exit(2) on a bad flag, which means "didn't even run".
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()

import argparse
import colorsys
import sys

from rich.console import Console
from rich.text import Text

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

# (row, column) bounding boxes for the two eyes within BANNER_IMAGE,
# found by rendering the raw braille text to a PNG with a monospace font
# and reading off pixel coordinates -- there's no way to know where a
# face's eyes are from the raw unicode characters alone. Each box also
# contains a small dense cluster of characters (the pupil) surrounded by
# mostly blank/sparse ones (the eye socket) -- confirmed against the
# actual string, not just the rendered image, since eyeballing pixels
# alone is easy to get slightly wrong.
_LEFT_EYE = (range(5, 10), range(5, 26))
_RIGHT_EYE = (range(5, 10), range(53, 73))


def _in_eye(row: int, col: int) -> bool:
    return any(row in rows and col in cols for rows, cols in (_LEFT_EYE, _RIGHT_EYE))


def _rainbow_hex(fraction: float) -> str:
    # fraction is 0.0 (top of banner) to 1.0 (bottom). Sweeping hue over
    # ~0-295 degrees (0.0-0.82 of the full 0-1 hue wheel) instead of the
    # full 360 avoids the gradient wrapping back around to red at the
    # bottom, which would visually clash with the red eyes.
    r, g, b = colorsys.hsv_to_rgb(fraction * 0.82, 0.85, 1.0)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def build_banner() -> Text:
    """Assembles the banner as a rich Text object, built character by
    character: a rainbow gradient sweeps top-to-bottom across the title
    and the portrait, while every character inside the eye bounding
    boxes is forced to bold red regardless of where it falls in the
    gradient. A plain string can only have one style; getting different
    colors on different characters within the same block of text requires
    building it up piece by piece like this.
    """
    title_lines = BANNER_TITLE.splitlines()
    image_lines = BANNER_IMAGE.splitlines()
    total_rows = len(title_lines) + len(image_lines)

    banner = Text()
    row_index = 0

    for line in title_lines:
        banner.append(line + "\n", style=f"bold {_rainbow_hex(row_index / total_rows)}")
        row_index += 1

    for image_row, line in enumerate(image_lines):
        color = _rainbow_hex(row_index / total_rows)
        for col, ch in enumerate(line):
            style = "bold red" if _in_eye(image_row, col) else color
            banner.append(ch, style=style)
        banner.append("\n")
        row_index += 1

    return banner


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
    console.print(build_banner())

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

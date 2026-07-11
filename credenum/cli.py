import argparse
import sys

from credenum.report import build_report, render_json, render_text


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
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    findings = build_report(args.root)

    if args.format == "json":
        print(render_json(findings))
    else:
        print(render_text(findings))

    # Exit code conventions matter for scripting: 0 means "ran fine, all
    # clear" so `credenum && deploy.sh` only proceeds when nothing was
    # found. 1 means "ran fine, but found something" -- distinct from
    # argparse's own exit(2) on a bad flag, which means "didn't even run".
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()

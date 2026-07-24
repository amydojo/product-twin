from __future__ import annotations

import argparse
import json
from pathlib import Path

from .service import render_fixture


def main() -> None:
    parser = argparse.ArgumentParser(prog="product-twin")
    subcommands = parser.add_subparsers(dest="command", required=True)
    render = subcommands.add_parser("render-fixture")
    render.add_argument("--spec", type=Path, required=True)
    render.add_argument("--output", type=Path, required=True)
    render.add_argument("--label", type=Path)
    render.add_argument("--no-fallback", action="store_true")
    args = parser.parse_args()

    if args.command == "render-fixture":
        manifest = render_fixture(
            args.spec,
            args.output,
            label=args.label,
            allow_fallback=not args.no_fallback,
        )
        print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

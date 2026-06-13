"""archviz-3d CLI."""

import argparse
import json
import sys
from pathlib import Path
from .engine import render, list_types


def main():
    parser = argparse.ArgumentParser(prog="archviz3d", description="3D visualization engine")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List 3D types")

    p_render = sub.add_parser("render", help="Render a 3D visualization")
    p_render.add_argument("--type", "-t", required=True)
    p_render.add_argument("--data", "-d", help="JSON data file")
    p_render.add_argument("--output", "-o", help="Output file")

    args = parser.parse_args()

    if args.command == "list":
        for t in list_types():
            print(f"  {t['type']:20s} {t['description']}")
    elif args.command == "render":
        data = json.loads(Path(args.data).read_text()) if args.data else list_types()[0].get("example", {})
        html = render(args.type, data)
        if args.output:
            Path(args.output).write_text(html)
            print(f"Written to {args.output} ({len(html)} chars)")
        else:
            print(html)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

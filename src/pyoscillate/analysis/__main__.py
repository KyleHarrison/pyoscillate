"""Probe a patch from the CLI and print its measured features as JSON.

    uv run python -m pyoscillate.analysis pyoscillate.patches.drums.clap.clap \\
        --set decay=0.3 --set tone=2000 --seconds 1.2 --ceiling 0.18
"""

import argparse
import json
from dataclasses import asdict

from pyoscillate.analysis.features import features
from pyoscillate.analysis.render import render


def _value(text: str) -> float | str:
    """Numbers for sliders, strings for profile names such as `style=round`."""
    try:
        return float(text)
    except ValueError:
        return text


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m pyoscillate.analysis")
    parser.add_argument("module", help="patch module exposing build(...)")
    parser.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    parser.add_argument("--seconds", type=float, default=1.0)
    parser.add_argument("--bpm", type=float, default=120)
    parser.add_argument("--ceiling", type=float, default=1.0)
    args = parser.parse_args()
    params = {
        name: _value(value) for name, value in (item.split("=", 1) for item in args.set)
    }
    result = features(
        render(args.module, params, seconds=args.seconds, bpm=args.bpm),
        ceiling=args.ceiling,
    )
    print(json.dumps(asdict(result), indent=2))


main()

#!/usr/bin/env python3
"""Generate a deterministic Flutter scene (compatibility entry for `generate.py --target flutter`)."""
from __future__ import annotations

from pathlib import Path

import generate as _generate
from emit_flutter import Call, DList, Lambda, Raw, dart_string, render  # noqa: F401  (stable imports)
from scene_model import argb_hex, font_weight, num, parse_color  # noqa: F401


def generate(evidence: list[Path], plan_path: Path | None, font_map_path: Path | None,
             class_name: str, output: Path, report_path: Path | None = None,
             app_root: Path | None = None, asset_dir: str | None = None,
             scene_test: Path | None = None, render_test: Path | None = None,
             output_env: str | None = None) -> dict:
    return _generate.generate(evidence, plan_path, font_map_path, class_name, output, report_path,
                              app_root, asset_dir, scene_test, render_test, output_env, 'flutter')


def main() -> int:
    return _generate.main('flutter')


if __name__ == '__main__':
    raise SystemExit(main())

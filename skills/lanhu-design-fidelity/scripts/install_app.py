#!/usr/bin/env python3
"""One-time setup for app developers: install only what page work needs.

  skill --target DIR      copy the Skill into an agent's skills directory
                          (no maintainer tests or experiment material)
  init  --app APP         add the lanhu_fidelity package and a fidelity/ workspace
  page  --app APP --name  create fidelity/<name>/page.json and declare its assets
  fonts --app APP         extract the design font (PingFang SC) from this Mac for
                          fidelity renders only and add it to fidelity/font-map.json

Nothing here touches page code, thresholds or contracts.
"""
from __future__ import annotations

import argparse
import filecmp
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
PACKAGE = SKILL / 'assets' / 'flutter' / 'lanhu_fidelity'
SKILL_PARTS = ('SKILL.md', 'agents', 'references', 'scripts', 'assets')
IGNORE = shutil.ignore_patterns('__pycache__', '*.pyc', '.dart_tool', 'build', '.DS_Store')
DEPENDENCY = '  lanhu_fidelity:\n    path: packages/lanhu_fidelity\n'

WRAPPER = '''#!/bin/bash
# Usage: fidelity/page <page-name> <start|prepare|generate|spec|accept|validate|report|status|finish|stop|...> [args]
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
if [[ -f "$here/.local.env" ]]; then source "$here/.local.env"; fi
: "${LANHU_FIDELITY_SKILL:?Run install_app.py init on this machine (writes fidelity/.local.env)}"
: "${LANHU_FIDELITY_PYTHON:=python3}"
name="${1:?page name}"; shift
exec "$LANHU_FIDELITY_PYTHON" "$LANHU_FIDELITY_SKILL/scripts/page_session.py" --config "$here/$name/page.json" "$@"
'''

GITIGNORE = '''# Per-machine paths and per-run renders; evidence, specs and contracts are committed.
.local.env
*/run/
'''


def skill_version() -> str:
    match = re.search(r'version:\s*"([^"]+)"', (SKILL / 'SKILL.md').read_text())
    return match.group(1) if match else 'unknown'


def install_skill(target: Path, force: bool) -> dict:
    destination = target / 'lanhu-design-fidelity'
    if destination.exists():
        marker = destination / '.installed-version'
        current = marker.read_text().strip() if marker.exists() else None
        if current == skill_version() and not force:
            return {'status': 'UP_TO_DATE', 'path': str(destination), 'version': current}
        backup = destination.with_name(f'lanhu-design-fidelity.backup-{current or "unknown"}')
        if backup.exists():
            shutil.rmtree(backup)
        destination.rename(backup)
    destination.mkdir(parents=True)
    for part in SKILL_PARTS:
        source = SKILL / part
        if source.is_dir():
            shutil.copytree(source, destination / part, ignore=IGNORE)
        else:
            shutil.copy2(source, destination / part)
    (destination / '.installed-version').write_text(skill_version() + '\n')
    return {'status': 'INSTALLED', 'path': str(destination), 'version': skill_version()}


def _yaml_block(lines: list[str], key: str, indent: int, start: int = 0, end: int | None = None):
    """Index of `key:` at exactly `indent` spaces between start and end, and its block end."""
    end = len(lines) if end is None else end
    pattern = re.compile(rf'^ {{{indent}}}{re.escape(key)}:\s*(#.*)?$')
    for index in range(start, end):
        if pattern.match(lines[index]):
            stop = index + 1
            while stop < end:
                line = lines[stop]
                if line.strip() and not line.startswith(' ' * (indent + 1)) and not line.lstrip().startswith('#'):
                    break
                stop += 1
            return index, stop
    return None, None


def add_dependency(pubspec: Path) -> str:
    text = pubspec.read_text()
    if re.search(r'^\s+lanhu_fidelity:', text, re.M):
        return 'present'
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith('\n'):
        lines[-1] += '\n'
    index, stop = _yaml_block(lines, 'dependencies', 0)
    if index is None:
        lines.append('\ndependencies:\n' + DEPENDENCY)
    else:
        while stop > index + 1 and not lines[stop - 1].strip():
            stop -= 1
        lines.insert(stop, DEPENDENCY)
    pubspec.write_text(''.join(lines))
    return 'added'


def add_asset_dir(pubspec: Path, asset_dir: str) -> str:
    entry = asset_dir.rstrip('/') + '/'
    text = pubspec.read_text()
    if re.search(rf'^\s+-\s+{re.escape(entry)}\s*$', text, re.M):
        return 'present'
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith('\n'):
        lines[-1] += '\n'
    flutter, flutter_end = _yaml_block(lines, 'flutter', 0)
    if flutter is None:
        lines.append(f'\nflutter:\n  assets:\n    - {entry}\n')
    else:
        assets, assets_end = _yaml_block(lines, 'assets', 2, flutter + 1, flutter_end)
        if assets is None:
            lines.insert(flutter + 1, f'  assets:\n    - {entry}\n')
        else:
            last = assets_end
            while last > assets + 1 and not lines[last - 1].strip():
                last -= 1
            lines.insert(last, f'    - {entry}\n')
    pubspec.write_text(''.join(lines))
    return 'added'


def flutter_version() -> str:
    try:
        result = subprocess.run(['flutter', '--version', '--machine'], capture_output=True,
                                text=True, timeout=60)
        return json.loads(result.stdout).get('frameworkVersion', '')
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return ''


def init_app(app: Path, python: str, force: bool) -> dict:
    pubspec = app / 'pubspec.yaml'
    if not pubspec.is_file():
        raise ValueError(f'{app} is not a Flutter app (pubspec.yaml missing)')
    target = app / 'packages' / 'lanhu_fidelity'
    package = 'unchanged'
    if target.exists():
        differs = _tree_differs(PACKAGE, target)
        if differs and not force:
            raise ValueError(f'{target} differs from this Skill version; re-run with --force to replace it')
        if differs:
            shutil.rmtree(target)
    if not target.exists():
        shutil.copytree(PACKAGE, target, ignore=IGNORE)
        package = 'installed'
    dependency = add_dependency(pubspec)
    workspace = app / 'fidelity'
    workspace.mkdir(exist_ok=True)
    font_map = workspace / 'font-map.json'
    if not font_map.exists():
        font_map.write_text(json.dumps({'fonts': {}}, indent=2) + '\n')
    wrapper = workspace / 'page'
    wrapper.write_text(WRAPPER)
    wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    (workspace / '.gitignore').write_text(GITIGNORE)
    (workspace / '.local.env').write_text(
        f'LANHU_FIDELITY_SKILL="{SKILL}"\nLANHU_FIDELITY_PYTHON="{python}"\n')
    return {'status': 'READY', 'package': package, 'dependency': dependency,
            'workspace': str(workspace),
            'next': ['flutter pub get',
                     '(cd packages/lanhu_fidelity && flutter test)  # once per Flutter upgrade',
                     'python3 <skill>/scripts/install_app.py page --app . --name <page>']}


def _tree_differs(source: Path, target: Path) -> bool:
    """True when any packaged file is missing or changed in the app copy."""
    for path in source.rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts or '.dart_tool' in path.parts \
                or 'build' in path.relative_to(source).parts:
            continue
        other = target / path.relative_to(source)
        if not other.is_file() or not filecmp.cmp(path, other, shallow=False):
            return True
    return False


FONT_HOME = '~/.lanhu-fidelity/fonts'
PINGFANG_FACES = {'Ultralight': 100, 'Thin': 200, 'Light': 300, 'Regular': 400,
                  'Medium': 500, 'Semibold': 600}


def discover_pingfang() -> Path | None:
    candidates = [Path('/System/Library/Fonts/PingFang.ttc')]
    for base in (Path('/System/Library/AssetsV2'), Path('/System/Library/Assets')):
        if base.exists():
            candidates.extend(sorted(base.glob('com_apple_MobileAsset_Font*/*/AssetData/PingFang.ttc')))
    return next((p for p in candidates if p.is_file()), None)


def install_fonts(app: Path, source: Path | None, android: str | None) -> dict:
    """Extract PingFang SC faces to ~/.lanhu-fidelity/fonts (outside every repo).

    The files are only loaded by fidelity tests on this machine. Production
    fonts are chosen per platform in the font map: iOS uses the system font
    (PingFang itself); Android uses the system font unless --android names a
    licensed family declared in pubspec.yaml.
    """
    from fontTools.ttLib import TTCollection, TTFont
    font_map_path = app / 'fidelity' / 'font-map.json'
    if not font_map_path.is_file():
        raise ValueError('run install_app.py init --app first')
    source = source or discover_pingfang()
    if source is None or not source.is_file():
        raise ValueError('PingFang.ttc not found; install 苹方 in Font Book or pass --pingfang')
    collection = TTCollection(str(source), lazy=True)
    faces = {font['name'].getDebugName(6): index for index, font in enumerate(collection.fonts)}
    collection.close()
    target_dir = Path(FONT_HOME).expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)
    font_map = json.loads(font_map_path.read_text())
    fonts = font_map.setdefault('fonts', {})
    added, extracted = [], []
    for face, weight in PINGFANG_FACES.items():
        name = f'PingFangSC-{face}'
        if name not in faces:
            continue
        target = target_dir / f'{name}.otf'
        if not target.exists():
            with TTFont(str(source), fontNumber=faces[name], recalcTimestamp=False) as font:
                font.save(str(target))
            extracted.append(target.name)
        key = f'{name}@{weight}'
        if key not in fonts:
            fonts[key] = {'path': f'{FONT_HOME}/{name}.otf', 'runtime_family': 'DesignPingFang',
                          'ios': None, 'android': android}
            added.append(key)
    font_map_path.write_text(json.dumps(font_map, ensure_ascii=False, indent=2) + '\n')
    return {'status': 'READY', 'font_dir': str(target_dir), 'extracted': extracted,
            'added_to_font_map': added,
            'production': {'ios': 'system font (PingFang)',
                           'android': android or 'system font'},
            'note': 'Fonts stay outside the app and are never bundled. Map any other design '
                    'fonts that prepare reports as font_mapping_missing by hand.'}


def camel(name: str) -> str:
    parts = re.split(r'[^0-9A-Za-z]+', name)
    result = ''.join(p[:1].upper() + p[1:] for p in parts if p)
    if not result or not result[0].isalpha():
        raise ValueError('page name must start with a letter; pass --class-name')
    return result


def create_page(app: Path, name: str, class_name: str | None, title: str | None) -> dict:
    if not re.fullmatch(r'[a-z][a-z0-9_]*', name):
        raise ValueError('page name must be snake_case, e.g. withdraw or order_detail')
    workspace = app / 'fidelity'
    if not (workspace / 'page').exists():
        raise ValueError('run install_app.py init --app first')
    folder = workspace / name
    config = folder / 'page.json'
    if config.exists():
        return {'status': 'EXISTS', 'config': str(config)}
    folder.mkdir()
    (folder / 'evidence').mkdir()
    asset_dir = f'assets/lanhu/{name}'
    page = {
        'name': title or name,
        'run_dir': 'run',
        'scope': 'page',
        'evidence': ['evidence/source.json'],
        'reference': 'evidence/reference.png',
        'manifest': 'evidence/manifest.json',
        'font_map': '../font-map.json',
        'spec': 'reviewed-spec.json',
        'contract': 'visual-contract.json',
        'app': '../..',
        'generated': f'../../lib/fidelity/{name}.g.dart',
        'class_name': class_name or camel(name),
        'asset_dir': asset_dir,
        'test': f'test/fidelity/{name}_test.dart',
        'output_env': 'LANHU_RENDER_OUTPUT',
        'page_inputs': [],
        'renderer_version': flutter_version(),
        'platform': f'{sys.platform}',
    }
    config.write_text(json.dumps(page, ensure_ascii=False, indent=2) + '\n')
    assets = add_asset_dir(app / 'pubspec.yaml', asset_dir)
    return {'status': 'CREATED', 'config': str(config), 'class_name': page['class_name'],
            'pubspec_assets': assets,
            'next': f'fidelity/page {name} start, then let the agent fetch evidence into '
                    f'fidelity/{name}/evidence/ and continue with prepare'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    s = sub.add_parser('skill')
    s.add_argument('--target', type=Path, required=True,
                   help='Agent skills directory, e.g. ~/.codex/skills or <repo>/.claude/skills')
    s.add_argument('--force', action='store_true')
    i = sub.add_parser('init')
    i.add_argument('--app', type=Path, required=True)
    i.add_argument('--python', default=sys.executable,
                   help='Python with scripts/requirements.txt installed (default: this one)')
    i.add_argument('--force', action='store_true', help='Replace a different lanhu_fidelity copy')
    p = sub.add_parser('page')
    p.add_argument('--app', type=Path, required=True)
    p.add_argument('--name', required=True, help='snake_case page id, e.g. withdraw')
    p.add_argument('--class-name', help='UpperCamelCase prefix for generated classes')
    p.add_argument('--title', help='Human-readable page name for reports')
    f = sub.add_parser('fonts')
    f.add_argument('--app', type=Path, required=True)
    f.add_argument('--pingfang', type=Path, help='PingFang.ttc (default: this Mac\'s system copy)')
    f.add_argument('--android', help='Licensed family declared in pubspec.yaml for Android '
                                     '(default: Android system font)')
    args = parser.parse_args()
    try:
        if args.command == 'skill':
            result = install_skill(args.target.expanduser().resolve(), args.force)
        elif args.command == 'init':
            result = init_app(args.app.resolve(), args.python, args.force)
        elif args.command == 'fonts':
            result = install_fonts(args.app.resolve(), args.pingfang, args.android)
        else:
            result = create_page(args.app.resolve(), args.name, args.class_name, args.title)
    except (ValueError, OSError) as exc:
        print(json.dumps({'status': 'ERROR', 'error': str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

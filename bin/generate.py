#!/usr/bin/env python3
"""Regenerate bucket/*.json from the latest freemkv releases.

Arch-aware: for every manifest, each Scoop architecture (64bit, arm64) is
included only when the latest release actually carries its assets, so a new
architecture shows up here on the next run without editing anything. Hashes
come from the release's .sha256 sidecars. No GitHub API calls: the latest tag
comes from the /releases/latest redirect and the asset list from the release's
expanded_assets page.

The manifests keep `checkver` + `autoupdate` for the architectures they carry,
so Scoop's own excavator (`.github/workflows/excavator.yml`) can also bump
versions between runs of this script.

    python3 bin/generate.py           # rewrite bucket/*.json
    python3 bin/generate.py --check   # exit 1 if anything would change
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

BUCKET = Path(__file__).resolve().parent.parent / 'bucket'
# Scoop architecture -> asset architecture token.
ARCHES = {'64bit': 'x86_64', 'arm64': 'aarch64'}

APP = {
    'repo': 'freemkv/freemkv',
    'homepage': 'https://freemkv.org',
    'license': 'MIT',
}
FIRMWARE = {
    'repo': 'freemkv/freemkv-firmware',
    'homepage': 'https://freemkv.org/firmware',
    'license': 'MIT',
}

# Each manifest lists candidate layouts, best first. A layout is used for an
# architecture when every one of its assets exists on the latest release.
MANIFESTS = {
    'freemkv': {
        **APP,
        'description': 'Rip DVD, Blu-ray and UHD discs to MKV without re-encoding (desktop app + command line)',
        'layouts': [{
            'assets': ['freemkv-{a}-windows.zip'],
            'bin': ['freemkv.com'],
            'shortcuts': [['freemkv.exe', 'freemkv']],
        }],
        'notes': 'Run `freemkv` for the command line; the desktop app is in the Start menu (Scoop Apps).',
    },
    'freemkv-cli': {
        **APP,
        'description': 'Rip DVD, Blu-ray and UHD discs to MKV without re-encoding (command line only)',
        'layouts': [{
            'assets': ['freemkv-cli-{a}-windows.exe#/freemkv.exe'],
            'bin': ['freemkv.exe'],
        }],
        'notes': 'Provides the same `freemkv` command as the freemkv app package; install one or the other.',
    },
    'freemkv-flash': {
        **FIRMWARE,
        'description': 'Flash optical-drive firmware for freemkv (desktop app + command line)',
        'layouts': [
            # Per-tool bundle (GUI + CLI) once releases ship it.
            {
                'assets': ['freemkv-flash-{a}-windows.zip'],
                'bin': ['freemkv-flash.exe', 'freemkv-flash-gui.exe'],
                'shortcuts': [['freemkv-flash-gui.exe', 'freemkv flash']],
            },
            # Separate CLI and GUI archives (v0.10.1 and earlier).
            {
                'assets': ['freemkv-flash-windows-{a}.zip', 'freemkv-flash-gui-windows-{a}.zip'],
                'bin': ['freemkv-flash.exe', 'freemkv-flash-gui.exe'],
                'shortcuts': [['freemkv-flash-gui.exe', 'freemkv flash']],
            },
        ],
    },
    'freemkv-fw': {
        **FIRMWARE,
        'description': 'Read, back up and identify optical-drive firmware for freemkv (desktop app + command line)',
        'layouts': [
            {
                'assets': ['freemkv-fw-{a}-windows.zip'],
                'bin': ['freemkv-fw.exe', 'freemkv-fw-gui.exe'],
                'shortcuts': [['freemkv-fw-gui.exe', 'freemkv fw']],
            },
            {
                'assets': ['freemkv-fw-windows-{a}.zip', 'freemkv-fw-gui-windows-{a}.zip'],
                'bin': ['freemkv-fw.exe', 'freemkv-fw-gui.exe'],
                'shortcuts': [['freemkv-fw-gui.exe', 'freemkv fw']],
            },
        ],
    },
}


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'freemkv-scoop-bucket'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.geturl(), r.read().decode()


def latest(repo):
    """(tag, {asset names}) of the repo's latest release, without the API."""
    final, _ = fetch(f'https://github.com/{repo}/releases/latest')
    m = re.search(r'/releases/tag/([^/?#]+)$', final)
    if not m:
        sys.exit(f'{repo}: no latest release ({final})')
    tag = m.group(1)
    _, page = fetch(f'https://github.com/{repo}/releases/expanded_assets/{tag}')
    names = set(re.findall(rf'href="/{re.escape(repo)}/releases/download/{re.escape(tag)}/([^"]+)"', page))
    if not names:
        sys.exit(f'{repo} {tag}: no assets found')
    return tag, names


def sha256(repo, tag, name):
    _, text = fetch(f'https://github.com/{repo}/releases/download/{tag}/{name}.sha256')
    m = re.match(r'\s*([0-9a-fA-F]{64})\b', text)
    if not m:
        sys.exit(f'{name}.sha256: no SHA-256 in {text!r}')
    return m.group(1).lower()


def one(values):
    return values[0] if len(values) == 1 else values


def build(name, spec, releases):
    repo = spec['repo']
    tag, names = releases[repo]
    version = tag[1:] if tag[:1] in 'vV' else tag
    base = f'https://github.com/{repo}/releases/download/'
    arch, auto, chosen = {}, {}, None
    for scoop_arch, token in ARCHES.items():
        for layout in spec['layouts']:
            files = [a.format(a=token) for a in layout['assets']]
            if all(f.split('#')[0] in names for f in files):
                break
        else:
            continue
        if chosen is None:
            chosen = layout
        elif layout is not chosen:
            sys.exit(f'{name}: architectures resolved to different layouts; split the manifest')
        arch[scoop_arch] = {
            'url': one([base + f'{tag}/{f}' for f in files]),
            'hash': one([sha256(repo, tag, f.split('#')[0]) for f in files]),
        }
        auto[scoop_arch] = {'url': one([base + f'v$version/{f}' for f in files])}
    if not arch:
        sys.exit(f'{name}: no Windows assets on {repo} {tag}')
    manifest = {
        'version': version,
        'description': spec['description'],
        'homepage': spec['homepage'],
        'license': spec['license'],
    }
    if spec.get('notes'):
        manifest['notes'] = spec['notes']
    manifest['architecture'] = arch
    manifest['bin'] = one(chosen['bin'])
    if chosen.get('shortcuts'):
        manifest['shortcuts'] = chosen['shortcuts']
    manifest['checkver'] = {'github': f'https://github.com/{repo}'}
    manifest['autoupdate'] = {
        'architecture': auto,
        'hash': {'url': '$url.sha256'},
    }
    return json.dumps(manifest, indent=4, ensure_ascii=False) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    releases = {r: latest(r) for r in {s['repo'] for s in MANIFESTS.values()}}
    changed = []
    for name, spec in MANIFESTS.items():
        text = build(name, spec, releases)
        path = BUCKET / f'{name}.json'
        if not path.exists() or path.read_text().replace('\r\n', '\n') != text:
            changed.append(path.name)
            if not args.check:
                path.parent.mkdir(exist_ok=True)
                path.write_text(text)
    print('changed: ' + (', '.join(changed) if changed else 'nothing'))
    if args.check and changed:
        sys.exit(1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Fetch pinned SVG prop bases and upstream license; no credentials or dependencies."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.request
import xml.etree.ElementTree as ET

SOURCES = {
    'tabler': ('tabler/tabler-icons', '55f87a73f45cf1d9eaf16d7da705065483a9e4f9', 'icons/outline', 'LICENSE'),
    'lucide': ('lucide-icons/lucide', 'a79b2d131dab2bf20cb224bd0937b439a9c4fa99', 'icons', 'LICENSE'),
}

def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000:
        raise ValueError('response exceeds 2 MB')
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', choices=SOURCES, required=True)
    parser.add_argument('--name', required=True, help='Exact upstream icon name, e.g. package')
    parser.add_argument('--output-dir', type=Path, required=True, help='New directory; existing directories are never overwritten')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', args.name):
        parser.error('invalid icon name')
    if args.output_dir.exists():
        parser.error('output directory already exists')
    repo, commit, folder, license_path = SOURCES[args.source]
    base = f'https://raw.githubusercontent.com/{repo}/{commit}/'
    url = base + folder + '/' + args.name + '.svg'
    svg = fetch(url)
    root = ET.fromstring(svg)
    if root.tag.split('}')[-1] != 'svg':
        raise ValueError('response is not SVG')
    for element in root.iter():
        if element.tag.split('}')[-1] in {'script', 'foreignObject', 'style'}:
            raise ValueError('unsupported active SVG content')
        for key, value in element.attrib.items():
            if key.lower().startswith('on') or 'href' in key.lower() or 'url(' in value.lower():
                raise ValueError('unsupported SVG reference')
    license_data = fetch(base + license_path)
    if not license_data.strip() or b'<html' in license_data.lower():
        raise ValueError('invalid license response')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / 'original.svg').write_bytes(svg)
    (args.output_dir / 'LICENSE').write_bytes(license_data)
    record = dict(source=args.source, name=args.name, role='prop_base', repository=repo,
                  commit=commit, source_url=url, license_url=base+license_path,
                  sha256=hashlib.sha256(svg).hexdigest(),
                  license_sha256=hashlib.sha256(license_data).hexdigest(),
                  visual_review='not_performed', brand_match='not_verified')
    (args.output_dir / 'ASSET.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps({'ok': True, 'directory': str(args.output_dir), 'sha256': record['sha256']}))

if __name__ == '__main__':
    main()

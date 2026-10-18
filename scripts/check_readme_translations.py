#!/usr/bin/env python3
"""Check README navigation, local targets and unchanged executable commands."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['README.md', 'README_zh.md', 'README_ja.md', 'README_ko.md']


def commands(text):
    blocks = re.findall(r'```bash\n(.*?)```', text, re.S)
    return [line.strip() for block in blocks for line in block.splitlines()
            if line.strip() and not line.lstrip().startswith('#')]


def main():
    baseline = (ROOT / NAMES[0]).read_text()
    base_commands = commands(baseline)
    baseline_links = set(re.findall(r'\]\(([^)]+)\)', baseline)) - set(NAMES)
    for name in NAMES:
        text = (ROOT / name).read_text()
        assert commands(text) == base_commands, name + ': executable commands differ'
        assert text.count('```') % 2 == 0, name + ': unclosed fence'
        assert len(re.findall(r'^## ', text, re.M)) == len(re.findall(r'^## ', baseline, re.M)), name + ': missing sections'
        links = set(re.findall(r'\]\(([^)]+)\)', text))
        assert links - set(NAMES) == baseline_links, name + ': reference links differ'
        for other in NAMES:
            if other != name:
                assert other in links, name + ': missing language navigation'
        for link in links:
            if '://' not in link and not link.startswith('#'):
                assert (ROOT / link.split('#')[0]).is_file(), name + ': missing local target ' + link
    print('README CHECK: PASS (4 languages, matching commands/references, navigation and local targets)')


if __name__ == '__main__':
    main()

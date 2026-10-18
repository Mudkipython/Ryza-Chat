#!/usr/bin/env python3
"""Export the maintained source snapshot, never the local runtime or Git history."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'output/github-release'
NAME = 'ryza-chat-mac-local'
DOCS = {'PROJECT.md', 'SETUP.md', 'MAC_DEMO.md', 'UPSTREAM_README.md',
        'AGENTATELIER_ADAPTATIONS.md', 'GITHUB_RELEASE.md', 'RELEASE_VALIDATION.md'}
TOP = {'README.md', 'README_zh.md', 'README_ja.md', 'README_ko.md', 'LICENSE', 'ACKNOWLEDGMENTS.md', 'CONTRIBUTING.md', 'SECURITY.md', '.gitignore'}
CONFIG = {'layers.json', 'version.json', 'providers.example.json', 'local-asr.json',
          'ryza-voice-reference.json', 'cosyvoice-trial-requirements.txt', 'sovits-trial-requirements.txt',
          'llm-recovery-8b.json'}
BINARY_MEDIA = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.m4a', '.mp3', '.wav', '.ogg',
                '.aac', '.skel', '.ttf', '.otf'}
DESKTOP = {'main.js', 'preload.js', 'web-storage.js', 'proxy-target.js', 'local-runtime.js',
           'model-manifest.json', 'package.json', 'package-lock.json', 'README.md',
           'build/icon.png', 'build/mac-icon.png'}
EXPERIMENTS = {'compare_fish_s2.py', 'compare_index_tts.py'}


def candidates():
    # Enumerate maintained roots, not "everything not ignored"; new private roots
    # and unexpected config files cannot silently become public.
    paths = [ROOT / name for name in TOP]
    paths += [ROOT / 'config' / name for name in CONFIG]
    paths += [ROOT / 'docs' / name for name in DOCS]
    for directory in ['web', 'scripts', 'android', 'desktop', '.github']:
        for base, dirs, files in os.walk(ROOT / directory, followlinks=False):
            dirs[:] = [d for d in dirs if d not in {'node_modules', '__pycache__', '.gradle', '.idea', 'dist', 'keystore'}
                       and not (directory == 'android' and d == 'build')]
            for name in files:
                p = Path(base) / name
                rel = p.relative_to(ROOT)
                if directory == 'desktop' and p.relative_to(ROOT/'desktop').as_posix() not in DESKTOP:
                    continue
                if name.startswith('.') or p.suffix.lower() in {'.pem', '.key', '.p12', '.jks', '.keystore'}:
                    continue
                if directory == 'scripts' and p.suffix not in {'.py', '.js', '.command', '.sh', '.ps1'}:
                    continue
                if p.is_symlink() or name == '.DS_Store' or p.suffix in {'.log', '.pyc', '.apk', '.zip'}:
                    continue
                if directory == 'web' and p.suffix.lower() in BINARY_MEDIA:
                    continue
                if directory == 'scripts' and name in EXPERIMENTS:
                    continue
                if directory == 'android' and (name == 'local.properties' or p.suffix in {'.jks', '.keystore'}):
                    continue
                paths.append(p)
    return sorted(set(paths))


def inspect_file(path):
    if not path.is_file() or path.is_symlink():
        raise ValueError('Missing or unsafe source: ' + str(path.relative_to(ROOT)))
    data = path.read_bytes()
    if len(data) > 20 * 1024 * 1024:
        raise ValueError('Unexpected large source: ' + str(path.relative_to(ROOT)))
    if b'\x00' not in data:
        text = data.decode('utf-8', 'replace')
        patterns = [r'/Users/[A-Za-z0-9._-]+/', r'C:\\Users\\[^\\\s]+\\',
                    r'sk-[A-Za-z0-9]{16,}', r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----']
        if any(re.search(pattern, text) for pattern in patterns):
            raise ValueError('Private marker in: ' + str(path.relative_to(ROOT)))
    return data


def main():
    files = [(p, inspect_file(p)) for p in candidates()]
    DEST.mkdir(parents=True, exist_ok=True)
    staging = DEST / NAME
    # Only replace this script's dedicated export, never the working tree.
    if staging.is_symlink():
        raise ValueError('Refusing symlink export directory')
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    manifest = []
    for source, data in files:
        rel = source.relative_to(ROOT)
        target = staging / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        mode = 0o755 if source.suffix in {'.command', '.sh'} else 0o644
        target.chmod(mode)
        manifest.append({'path': rel.as_posix(), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    (staging / 'SOURCE_MANIFEST.json').write_text(json.dumps({
        'release': 'mac-local-preview.1', 'upstreamCommit': '45e75ad6f6f0eb7952676b1bf24a674256082941',
        'files': manifest}, ensure_ascii=False, indent=2) + '\n')
    subprocess.run(['python3', str(staging/'scripts/privacy_check.py'), str(staging/'web')], check=True)
    archive = DEST / 'ryza-chat-mac-local-preview-source.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as out:
        for path in sorted(staging.rglob('*')):
            if path.is_file():
                info = zipfile.ZipInfo(path.relative_to(DEST).as_posix(), (2026, 10, 18, 0, 0, 0))
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | (path.stat().st_mode & 0o777)) << 16
                out.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (DEST/'SHA256SUMS.txt').write_text(digest + '  ' + archive.name + '\n')
    print(f'EXPORTED: {len(manifest)} files; {archive.stat().st_size:,} bytes; {archive}')
    print('SHA256: ' + digest)


if __name__ == '__main__':
    main()

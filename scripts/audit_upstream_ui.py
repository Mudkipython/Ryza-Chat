"""Verify upstream UI assets in source and optionally the built Mac app."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = '45e75ad6f6f0eb7952676b1bf24a674256082941'
parser = argparse.ArgumentParser()
parser.add_argument('--packaged', action='store_true')
parser.add_argument('--apk', type=Path)
args = parser.parse_args()
paths = subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'web/css','web/assets/icons','web/index.html'], cwd=ROOT).decode().splitlines()
pack = ROOT/'output/desktop/mac-arm64/RyzaChat.app/Contents/Resources'
errors = []
for rel in paths:
    expected = subprocess.check_output(['git','show',BASE+':'+rel],cwd=ROOT)
    for base in [ROOT] + ([pack] if args.packaged else []):
        p=base/rel
        if not p.is_file() or p.read_bytes()!=expected:
            errors.append(str(p.relative_to(ROOT)))
media=0
if args.apk:
    from restore_media import dest_for_apk_member
    with zipfile.ZipFile(args.apk) as z:
        for entry in z.infolist():
            rel=dest_for_apk_member(entry.filename)
            if not rel: continue
            expected=hashlib.sha256(z.read(entry)).digest()
            for base in [ROOT] + ([pack] if args.packaged else []):
                p=base/rel
                if not p.is_file() or hashlib.sha256(p.read_bytes()).digest()!=expected:
                    errors.append(str(p.relative_to(ROOT)))
            media+=1
if errors:
    raise SystemExit('UI AUDIT FAILED:\n'+'\n'.join(errors))
print(f'UI AUDIT PASS: {len(paths)} upstream HTML/CSS/icon files; {media} release media files; packaged={args.packaged}; base={BASE[:7]}')

#!/usr/bin/env python3
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
text = (root / 'index.html').read_text(encoding='utf-8')
lines = text.splitlines()

out = []

# Extract the exact starter document assignment.
for i, line in enumerate(lines):
    if 'const starterText =' in line:
        out.append('--- STARTER TEXT ---')
        out.append(f'{i+1:05d}: {line}')
        break
else:
    out.append('STARTER TEXT NOT FOUND')

# Extract only the help drawer aside block, whichever id/class it currently uses.
aside_pattern = re.compile(r'<aside\b[^>]*>.*?</aside>', re.S | re.I)
help_block = None
for match in aside_pattern.finditer(text):
    block = match.group(0)
    low = block.lower()
    if 'help and about' in low or 'help &amp; about' in low or 'helpdrawer' in low or 'help-drawer' in low:
        help_block = block
        break

out.append('\n--- HELP DRAWER ---')
if help_block is None:
    out.append('HELP DRAWER NOT FOUND')
else:
    start_line = text[:text.index(help_block)].count('\n') + 1
    for offset, line in enumerate(help_block.splitlines()):
        out.append(f'{start_line + offset:05d}: {line}')

(root / 'tools' / 'onboarding_context.txt').write_text('\n'.join(out) + '\n', encoding='utf-8')

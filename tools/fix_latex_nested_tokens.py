#!/usr/bin/env python3
"""Resolve nested placeholder tokens in the LaTeX inline converter."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = r'''      text = escapeLatexText(decodeHtmlText(text));
      return text.replace(/\uE000(\d+)\uE001/g, (_, index) => tokens[Number(index)] || '');
'''
NEW = r'''      let resolved = escapeLatexText(decodeHtmlText(text));
      for (let pass = 0; pass <= tokens.length && /\uE000\d+\uE001/.test(resolved); pass += 1) {
        resolved = resolved.replace(/\uE000(\d+)\uE001/g, (_, index) => tokens[Number(index)] || '');
      }
      return resolved;
'''

for relative in ('index.html', 'tools/latex_export_inline.js'):
    path = ROOT / relative
    text = path.read_text(encoding='utf-8')
    count = text.count(OLD)
    if count != 1:
        raise SystemExit(f'Expected one nested-token marker in {relative}, found {count}')
    path.write_text(text.replace(OLD, NEW, 1), encoding='utf-8')
    print(f'Updated {relative}')

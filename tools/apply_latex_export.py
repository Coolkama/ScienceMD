#!/usr/bin/env python3
"""Apply the branch-only ScienceMD LaTeX export patch."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'index.html'
SMOKE = ROOT / 'tools' / 'smoke_test.py'
PARTS = ROOT / 'tools'

html = INDEX.read_text(encoding='utf-8')
if 'function buildLatexDocument()' in html:
    print('LaTeX export already present.')
    raise SystemExit(0)

def replace_once(source, old, new, label):
    count = source.count(old)
    if count != 1:
        raise SystemExit(f'Expected one {label}, found {count}')
    return source.replace(old, new, 1)

for old, new, label in [
    ('Download/export edited Markdown, rendered HTML, or print/save as PDF',
     'Download/export edited Markdown, rendered HTML, LaTeX, or print/save as PDF', 'feature summary'),
    ('Use <strong>Save</strong> or <strong>Save As</strong> to download your Markdown.',
     'Use <strong>Save</strong> or <strong>Save As</strong> to download Markdown, rendered HTML, or LaTeX.', 'workflow help'),
    ('Save with a new filename or export rendered HTML',
     'Save with a new filename or export rendered HTML or LaTeX', 'toolbar help'),
]:
    html = replace_once(html, old, new, label)

normalisers = r'''    function normaliseLatexFileName(fileName) {
      const raw = String(fileName || '').trim() || 'science-draft.tex';
      const stem = raw.replace(/\.(?:md|markdown|html?|tex)$/i, '') || 'science-draft';
      return `${stem}.tex`;
    }

    function normaliseExportFileName(fileName, format) {
      if (format === 'html') return normaliseHtmlFileName(fileName);
      if (format === 'latex') return normaliseLatexFileName(fileName);
      return normaliseMarkdownFileName(fileName);
    }

'''
marker = '    function getSaveAsOptions() {'
html = replace_once(html, marker, normalisers + marker, 'Save As marker')

save_dialog = (PARTS / 'latex_export_save_dialog.js').read_text(encoding='utf-8')
pattern = re.compile(r'    function getSaveAsOptions\(\) \{\n.*?\n    \}\n\n    async function ensurePreviewRenderedForExport\(\)', re.DOTALL)
html, count = pattern.subn(save_dialog, html, count=1)
if count != 1:
    raise SystemExit(f'Expected one Save As block, replaced {count}')

converter = ''.join((PARTS / name).read_text(encoding='utf-8') for name in [
    'latex_export_inline.js', 'latex_export_tables.js',
    'latex_export_body_a.js', 'latex_export_body_b.js',
    'latex_export_document.js',
])
marker = '    async function saveMarkdownAs() {'
html = replace_once(html, marker, converter + marker, 'converter insertion marker')

dispatch = r'''    async function saveMarkdownAs() {
      if (isVisualModeActive()) {
        const committedMath = commitActiveWysiwygMathEdit({ quiet: true });
        if (!committedMath) syncMarkdownFromWysiwyg();
      }
      const options = await getSaveAsOptions();
      if (!options) return;
      if (options.format === 'html') {
        await downloadRenderedHtml(options.fileName);
        return;
      }
      if (options.format === 'latex') {
        downloadLatex(options.fileName);
        return;
      }
      downloadMarkdown(options.fileName);
    }


    function clearDraft()'''
pattern = re.compile(r'    async function saveMarkdownAs\(\) \{\n.*?\n    \}\n\n\n    function clearDraft\(\)', re.DOTALL)
html, count = pattern.subn(dispatch, html, count=1)
if count != 1:
    raise SystemExit(f'Expected one Save As dispatch, replaced {count}')

for required in ['value="latex"', 'function buildLatexDocument()',
                 'function markdownToLatexBody(markdown)',
                 'application/x-tex;charset=utf-8',
                 r'\documentclass[11pt,a4paper]{article}']:
    if required not in html:
        raise SystemExit(f'Missing LaTeX marker: {required}')
INDEX.write_text(html, encoding='utf-8')

smoke = SMOKE.read_text(encoding='utf-8')
anchor = '    "printing": "print" in lower,\n'
smoke = replace_once(smoke, anchor, anchor + '    "LaTeX export": "buildlatexdocument" in lower and \'value="latex"\' in lower,\n', 'smoke capability')
anchor = 'require("documentLoadInProgress = true" in html, "New Document load lock is missing")\n'
extra = anchor + 'require(r"\\documentclass[11pt,a4paper]{article}" in html, "LaTeX document preamble is missing")\n' + 'require("application/x-tex;charset=utf-8" in html, "LaTeX download MIME type is missing")\n'
smoke = replace_once(smoke, anchor, extra, 'smoke assertions')
SMOKE.write_text(smoke, encoding='utf-8')
print('LaTeX export added.')

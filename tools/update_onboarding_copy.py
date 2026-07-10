#!/usr/bin/env python3
from pathlib import Path
import json
import re

root = Path(__file__).resolve().parents[1]
index_path = root / 'index.html'
text = index_path.read_text(encoding='utf-8')

starter = r'''# Welcome to Sciwrix

**Sciwrix** is an offline-first Markdown and LaTeX editor for scientific and technical writing. Your document remains a normal `.md` file, and all editing stays on your device.

> This starter document introduces the current Sciwrix interface. Delete it when you are ready to begin your own document.

---

## The ribbon

Sciwrix organises its controls into focused tabs:

- **File** — create, open, save, save as, and print documents.
- **Edit** — undo, redo, and find or replace text.
- **Markdown** — paragraphs, headings, bold, italic, quotations, and lists.
- **Insert** — images and horizontal rules.
- **Maths** — inline maths, display maths, and the maths palette.
- **Table** — insert and edit Markdown tables.
- **View** — switch between Visual and Markdown views, navigate sections, choose the document style, and enter fullscreen.
- **Help** — open the full guide and application information.

The toolbar changes when you select a different tab. Under **View**, you can also choose Icons, Labels, or Adaptive toolbar buttons.

---

## Visual and Markdown views

Use **Visual** for normal writing and formatting. Use **Markdown** when you want direct control of the source text.

Both views edit the same document. There is no separate preview mode: the Visual editor is the rendered editing view.

Editing is always continuous. On larger displays the document uses a comfortable page-like width with a subtle shadow. On mobile it expands to the screen width to maximise the writing area.

---

## Saving and printing

- **Save** downloads the current Markdown file.
- **Save As** lets you choose a filename and save as Markdown, rendered HTML, or LaTeX.
- **Print** prints the document as it currently appears, or lets your browser save it as PDF.

The selected **Document Style** is used both on screen and when printing. It changes appearance only; it does not alter your Markdown source.

Autosave is stored in this browser as a safety net. It is not a replacement for saving a real file.

---

## Headings and formatting

Use headings to organise longer documents:

```markdown
# Document title
## Main section
### Subsection
```

You can apply paragraph and heading styles from the **Markdown** tab, alongside bold, italic, block quotations, bulleted lists, and numbered lists.

> Quotations and code blocks use neutral shading so the document remains clear without adding decorative colour.

---

## Maths

Inline maths stays within a sentence:

\(E = mc^2\)

Display maths is shown on its own line:

\[
F = G\frac{m_1m_2}{r^2}
\]

Use the **Maths** tab to insert maths or open the maths palette. In Visual view, select a rendered formula to edit its LaTeX source, then choose **Done** to render it again.

---

## Tables

Use **Table → Insert table**, choose the number of columns and rows, then type directly into the cells.

| Quantity | Meaning | Relationship |
|---|---|---|
| \(v\) | wave speed | \(v = f\lambda\) |
| \(f\) | frequency | measured in hertz |
| \(\lambda\) | wavelength | measured in metres |

When the cursor is inside a table, the Table tab provides controls for adding or removing rows and columns, or deleting the table.

---

## Code

Triple backticks create a code block:

```csharp
public static double KineticEnergy(double mass, double velocity)
{
    return 0.5 * mass * velocity * velocity;
}
```

Sciwrix works as a standalone HTML file, through GitHub Pages, and as an Android app.
'''

starter_literal = json.dumps(starter, ensure_ascii=False)
text, starter_count = re.subn(
    r'^\s*const starterText = .*?;\s*$',
    f'    const starterText = {starter_literal};',
    text,
    count=1,
    flags=re.M,
)
if starter_count != 1:
    raise SystemExit(f'Expected one starterText assignment, replaced {starter_count}')

text = text.replace('<strong>Help / About</strong>', '<strong>Help &amp; About</strong>', 1)

help_intro = '''    <div class="help-panel">
      <section class="about-card">
        <div class="about-icon" aria-hidden="true">Σ</div>
        <div>
          <h2>Sciwrix</h2>
          <p><strong>Version 1.5.1</strong></p>
          <p>An offline-first Markdown and LaTeX editor for scientific and technical writing.</p>
          <p>The standalone browser edition and Android app keep document editing on your device. No account or server is required.</p>
          <p class="creator">Designed and created by Trevor Neil Kelleher.</p>
          <p><a href="https://github.com/Coolkama/Sciwrix" target="_blank" rel="noopener noreferrer">Project source and releases on GitHub</a></p>
        </div>
      </section>

      <section>
        <h3>Getting started</h3>
        <ol>
          <li>Use <strong>File → New</strong> to start from the built-in Sciwrix guide.</li>
          <li>Use <strong>File → Open</strong> to load an existing <code>.md</code> file.</li>
          <li>Write in <strong>Visual</strong> view, or use <strong>View → Markdown</strong> for direct source editing.</li>
          <li>Choose a <strong>Document Style</strong> under View. The same style is used on screen and when printing.</li>
          <li>Use <strong>Save</strong> for Markdown, or <strong>Save As</strong> to choose Markdown, rendered HTML, or LaTeX.</li>
          <li>Use <strong>Print</strong> to print the current document or save it as PDF.</li>
        </ol>
      </section>

      <section>
        <h3>Ribbon tabs</h3>
        <table>
          <tr><th>Tab</th><th>What it contains</th></tr>
          <tr><td>File</td><td>New, Open, Save, Save As, and Print</td></tr>
          <tr><td>Edit</td><td>Undo, Redo, and Find &amp; Replace</td></tr>
          <tr><td>Markdown</td><td>Paragraphs, headings, bold, italic, quotations, and lists</td></tr>
          <tr><td>Insert</td><td>Images and horizontal rules</td></tr>
          <tr><td>Maths</td><td>Inline maths, display maths, and the maths palette</td></tr>
          <tr><td>Table</td><td>Insert a table and edit its rows and columns</td></tr>
          <tr><td>View</td><td>Visual or Markdown view, section navigation, Document Style, fullscreen, and toolbar appearance</td></tr>
          <tr><td>Help</td><td>Open this Help &amp; About panel</td></tr>
        </table>
        <p>The toolbar changes with the selected tab. Under View, choose <strong>Icons</strong>, <strong>Labels</strong>, or <strong>Adaptive</strong> toolbar buttons.</p>
      </section>

      <section>
        <h3>Editing views and layout</h3>
        <p><strong>Visual</strong> is the rendered editing view. <strong>Markdown</strong> exposes the source of the same document. There is no separate preview mode.</p>
        <p>Editing is always continuous. On larger displays, the editor uses a comfortable page-like width and a subtle shadow. On mobile, it expands to the screen width to maximise the writing area.</p>
        <p>The word and character count remain visible in the footer.</p>
      </section>

      <section>
        <h3>Document style, printing, and export</h3>
        <p>The selected <strong>Document Style</strong> controls both the on-screen document and its printed or PDF appearance. It does not change the Markdown source.</p>
        <p><strong>Save</strong> downloads Markdown. <strong>Save As</strong> provides the filename and format choices for Markdown, standalone HTML, and LaTeX. <strong>Print</strong> opens the browser print dialog.</p>
      </section>

      <section>
        <h3>Tables</h3>
        <p>Use <strong>Table → Insert table</strong>, choose the number of columns and data rows, then type directly into the cells.</p>
        <p>Place the cursor inside a table to add or remove rows and columns, or delete the entire table. Press <strong>Tab</strong> to move through cells; pressing Tab in the final cell adds another row.</p>
      </section>

      <section>
        <h3>Maths</h3>
        <p>Inline maths:</p>
        <pre><code>\(E = mc^2\)</code></pre>
        <p>Display maths:</p>
        <pre><code>\[
F = G\frac{m_1m_2}{r^2}
\]</code></pre>
        <p>Use the Maths tab to insert maths or open the maths palette. In Visual view, select a rendered formula to edit its LaTeX source, then choose <strong>Done</strong> to render it again.</p>
      </section>

      <section>
        <h3>Autosave and embedded images</h3>
        <p>Autosave is browser storage. It is a useful safety net, but it is not the same as saving a file. Use <strong>Save</strong> or <strong>Save As</strong> to create a real document file.</p>
        <p>Embedded images retain their original format and dimensions. Sciwrix may display them at a smaller size in the editor, while the saved Markdown keeps the full embedded image.</p>
      </section>

'''

help_pattern = re.compile(
    r'    <div class="help-panel">.*?(?=      <!-- SCIENCEMD-LICENCES-START -->)',
    re.S,
)
text, help_count = help_pattern.subn(help_intro, text, count=1)
if help_count != 1:
    raise SystemExit(f'Expected one pre-licence help section, replaced {help_count}')

# Guardrails against stale interface language.
for stale in ('Use **Write**', 'Output group', '<h3>Top toolbar</h3>', '<h3>Edit toolbar</h3>'):
    if stale in text:
        raise SystemExit(f'Stale interface wording remains: {stale}')

if text.count('SCIENCEMD-LICENCES-START') != 1 or text.count('SCIENCEMD-LICENCES-END') != 1:
    raise SystemExit('Licence acknowledgement markers were altered')
if not re.search(r'</body>\s*</html>\s*$', text, re.S | re.I):
    raise SystemExit('Document tail is invalid')

index_path.write_text(text, encoding='utf-8')

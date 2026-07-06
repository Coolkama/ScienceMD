#!/usr/bin/env python3
"""Maintain New Document reset behaviour and embedded licence notices."""

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
SMOKE = ROOT / "tools/smoke_test.py"

html = INDEX.read_text(encoding="utf-8")

old = """    function clearDraft() {
      const confirmed = confirm('Start a new document from the built-in ScienceMD starter? This will replace the current editor text, but it will not delete any files from your device.');
      if (!confirmed) return;

      embeddedImages = {};
      nextImageNumber = 1;
      saveImageMap();

      // New document must be treated like opening a completely different file.
      // Updating the hidden Markdown textarea is not enough: if the visual editor
      // currently has focus, the normal render path deliberately avoids rebuilding
      // it, which left the previous document visible in WYSIWYG mode.
      activeMathEditInput = null;
      savedWysiwygRange = null;
      hideTableTools();
      setEditorMarkdown(starterText, { collapseImages: false, resetScroll: true });
      setFileName('science-draft.md');

      if (sourceMode) setSourceMode(false);
      switchView('edit');

      // Force the visual editor after switchView as well, because wide desktop
      // mode calls renderNow() during the switch and renderNow() is intentionally
      // conservative about rebuilding a focused WYSIWYG pane.
      forceWysiwygFromMarkdown({ resetScroll: true, focusStart: true });
      renderNow();
      saveDraft(false);
      resetHistory(editor.value || '');

      requestAnimationFrame(() => {
        forceWysiwygFromMarkdown({ resetScroll: true, focusStart: true });
      });

      showToast('New document created');
    }
"""

new = """    function clearDraft() {
      const confirmed = confirm('Start a new document from the built-in ScienceMD starter? This will replace the current editor text, but it will not delete any files from your device.');
      if (!confirmed) return;

      // Treat New exactly like loading another file. On mobile browsers and
      // Android WebView, a delayed contenteditable/keyboard event can otherwise
      // write the previous visual document back over the starter text.
      documentLoadInProgress = true;
      clearTimeout(renderTimer);
      clearTimeout(historyTimer);

      try {
        try { wysiwygEditor.blur(); } catch (_error) {}
        try { editor.blur(); } catch (_error) {}

        embeddedImages = {};
        nextImageNumber = 1;
        saveImageMap();

        activeMathEditInput = null;
        savedWysiwygRange = null;
        hideTableTools();
        setEditorMarkdown(starterText, { collapseImages: false, resetScroll: true });
        setFileName('science-draft.md');

        sourceMode = false;
        editor.classList.add('hidden');
        wysiwygEditor.classList.remove('hidden');
        editModeLabel.textContent = 'Visual editor';
        switchView('edit');

        forceWysiwygFromMarkdown({ resetScroll: true, focusStart: false });
        renderNow();
        saveDraft(false);
        resetHistory(editor.value || '');

        // Keep the document-load lock through two animation frames so any late
        // IME or contenteditable input event is ignored before focus is restored.
        requestAnimationFrame(() => requestAnimationFrame(() => {
          forceWysiwygFromMarkdown({ resetScroll: true, focusStart: true });
          renderNow();
          documentLoadInProgress = false;
        }));

        showToast('New document created');
      } catch (error) {
        documentLoadInProgress = false;
        console.error('Could not create a new document:', error);
        editor.value = starterText;
        safeSetStorage(STORAGE_KEY, starterText, true);
        forceWysiwygFromMarkdown({ resetScroll: true, focusStart: true });
        renderNow();
        showToast('New document created with a visual-editor warning.');
      }
    }
"""

if old in html:
    html = html.replace(old, new, 1)
elif new not in html:
    raise SystemExit("Expected clearDraft implementation was not found")

html = html.replace(
    "Released under the Apache license 2.0 and Mozilla Public License 2.0",
    "Released under the Apache License 2.0 OR Mozilla Public License 2.0",
)
html = html.replace(
    "Released under the Apache License 2.0 and Mozilla Public License 2.0",
    "Released under the Apache License 2.0 OR Mozilla Public License 2.0",
)

project_notice = "<!-- ScienceMD | Copyright 2026 Trevor Neil Kelleher | Apache License 2.0 | Full notices in Help and About. -->"
if project_notice not in html:
    html = html.replace("<html", project_notice + "\n<html", 1)

mathjax_notice = "<!-- MathJax 3.2.1 | Apache License 2.0 | Includes Speech Rule Engine 4.0.6 and Wicked Good XPath 1.3.0. -->"
if mathjax_notice not in html:
    marker = "  <script>\n    window.MathJax = {"
    if marker not in html:
        raise SystemExit("MathJax configuration marker was not found")
    html = html.replace(marker, "  " + mathjax_notice + "\n" + marker, 1)

apache_text = escape((ROOT / "LICENSE").read_text(encoding="utf-8"))
mit_text = escape((ROOT / "WICKED_GOOD_XPATH_LICENSE.txt").read_text(encoding="utf-8"))
sre_notice = escape(
    "Speech Rule Engine\n"
    "Copyright 2014-2018 Volker Sorge\n\n"
    "This product includes software developed by Volker Sorge and originally "
    "implemented in the context of ChromeVox at Google Inc.\n\n"
    "The browser version depends on Wicked Good XPath."
)

licence_section = f"""<!-- SCIENCEMD-LICENCES-START -->
      <section id="licenceAcknowledgements">
        <h3>Licence and acknowledgements</h3>
        <p><strong>ScienceMD</strong> is Copyright 2026 Trevor Neil Kelleher and is licensed under the <strong>Apache License 2.0</strong>.</p>
        <p>This application includes MathJax 3.2.1, DOMPurify 3.4.8, Speech Rule Engine 4.0.6, and Wicked Good XPath 1.3.0. Each component remains governed by its respective licence.</p>
        <details class="licence-details"><summary>Apache License 2.0</summary><pre>{apache_text}</pre></details>
        <details class="licence-details"><summary>Speech Rule Engine notice</summary><pre>{sre_notice}</pre></details>
        <details class="licence-details"><summary>Wicked Good XPath — MIT License</summary><pre>{mit_text}</pre></details>
      </section>
      <!-- SCIENCEMD-LICENCES-END -->"""

start_marker = "<!-- SCIENCEMD-LICENCES-START -->"
end_marker = "<!-- SCIENCEMD-LICENCES-END -->"
if start_marker in html:
    start = html.index(start_marker)
    end = html.index(end_marker, start) + len(end_marker)
    html = html[:start] + licence_section + html[end:]
else:
    help_end_marker = "      <section>\n        <h3>Autosave warning</h3>"
    help_start = html.index(help_end_marker)
    help_end = html.index("      </section>", help_start) + len("      </section>")
    html = html[:help_end] + "\n\n      " + licence_section + html[help_end:]

licence_css = """
    .licence-details {
      margin: 9px 0;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: var(--panel-2);
    }

    .licence-details summary {
      cursor: pointer;
      padding: 10px 12px;
      font-weight: 750;
    }

    .licence-details pre {
      max-height: 46vh;
      margin: 0 10px 10px;
      white-space: pre-wrap;
      overflow: auto;
      font-size: 0.72rem;
    }

"""
if ".licence-details {" not in html:
    css_marker = "    .about-card {"
    if css_marker not in html:
        raise SystemExit("About-panel CSS marker was not found")
    html = html.replace(css_marker, licence_css + css_marker, 1)

INDEX.write_text(html, encoding="utf-8")
print("Updated New Document handling and embedded licence notices.")

smoke = SMOKE.read_text(encoding="utf-8")
marker = 'require("HTMLAnchorElement.prototype.click" in activity, "web download interception is missing")\n'
new_document_check = 'require("documentLoadInProgress = true" in html, "New Document load lock is missing")\n'
if new_document_check not in smoke:
    if marker not in smoke:
        raise SystemExit("Smoke-test insertion point was not found")
    smoke = smoke.replace(marker, marker + new_document_check, 1)

legal_checks = """
require((ROOT / "LICENSE").is_file(), "Apache 2.0 LICENSE file is missing")
require((ROOT / "NOTICE").is_file(), "NOTICE file is missing")
require((ROOT / "THIRD_PARTY_NOTICES.md").is_file(), "third-party notices are missing")
require((ROOT / "WICKED_GOOD_XPATH_LICENSE.txt").is_file(), "Wicked Good XPath licence is missing")
require("Licence and acknowledgements" in html, "in-app licence acknowledgements are missing")
require("Apache License 2.0 OR Mozilla Public License 2.0" in html, "DOMPurify licence choice is recorded incorrectly")
require("MathJax 3.2.1 | Apache License 2.0" in html, "MathJax licence banner is missing")
"""
if "in-app licence acknowledgements are missing" not in smoke:
    completion = 'print("ScienceMD smoke checks passed.")'
    if completion not in smoke:
        raise SystemExit("Smoke-test completion marker was not found")
    smoke = smoke.replace(completion, legal_checks + "\n" + completion, 1)

SMOKE.write_text(smoke, encoding="utf-8")
print("Updated licensing regression checks.")

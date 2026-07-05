from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str, label: str) -> None:
    global text
    if new in text:
        print(f"{label}: already applied")
        return
    if old not in text:
        raise RuntimeError(f"{label}: expected source block was not found")
    text = text.replace(old, new, 1)
    print(f"{label}: applied")


replace_once(
    """    .top-toolbar .primary {
      background: var(--accent);
      border-color: var(--accent);
      color: white;
    }
""",
    """    .top-toolbar .primary {
      background: var(--accent);
      border-color: var(--accent);
      color: white;
    }

    .top-toolbar button:disabled {
      opacity: 0.36;
      cursor: default;
      box-shadow: none;
    }
""",
    "disabled history button style",
)

replace_once(
    """          <button id="navBtn" type="button" title="Section navigation" aria-label="Section navigation">""",
    """          <button id="undoBtn" type="button" title="Undo (Ctrl+Z)" aria-label="Undo" disabled><svg class="bi bi-arrow-counterclockwise" aria-hidden="true" focusable="false" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8 3a5 5 0 1 1-4.546 2.914.5.5 0 0 0-.908-.417A6 6 0 1 0 8 2z"/><path d="M8 4.466V.534a.25.25 0 0 0-.41-.192L5.23 2.308a.25.25 0 0 0 0 .384l2.36 1.966A.25.25 0 0 0 8 4.466"/></svg></button>
          <button id="redoBtn" type="button" title="Redo (Ctrl+Y)" aria-label="Redo" disabled><svg class="bi bi-arrow-clockwise" aria-hidden="true" focusable="false" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2z"/><path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966a.25.25 0 0 1 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466"/></svg></button>
          <button id="navBtn" type="button" title="Section navigation" aria-label="Section navigation">""",
    "undo and redo toolbar buttons",
)

replace_once(
    """          <tr><td>Save As</td><td>Save with a new filename or export rendered HTML</td></tr>
          <tr><td>Navigation</td><td>Open the section navigator built from headings</td></tr>
""",
    """          <tr><td>Save As</td><td>Save with a new filename or export rendered HTML</td></tr>
          <tr><td>Undo</td><td>Undo the most recent editing change</td></tr>
          <tr><td>Redo</td><td>Restore the most recently undone change</td></tr>
          <tr><td>Navigation</td><td>Open the section navigator built from headings</td></tr>
""",
    "help entries",
)

replace_once(
    """    const clearBtn = document.getElementById('clearBtn');
    const darkBtn = document.getElementById('darkBtn');
""",
    """    const clearBtn = document.getElementById('clearBtn');
    const undoBtn = document.getElementById('undoBtn');
    const redoBtn = document.getElementById('redoBtn');
    const darkBtn = document.getElementById('darkBtn');
""",
    "history button references",
)

replace_once(
    """    let wysiwygSyncLock = false;
    let documentLoadInProgress = false;
    let lastScrollProgress = 0;
""",
    """    let wysiwygSyncLock = false;
    let documentLoadInProgress = false;
    const HISTORY_LIMIT = 50;
    let undoStack = [];
    let redoStack = [];
    let historyCurrentMarkdown = null;
    let historyTimer = null;
    let historyApplying = false;
    let lastScrollProgress = 0;
""",
    "history state",
)

replace_once(
    """    function saveDraft(updateVisual = true) {
      try {
        safeSetStorage(STORAGE_KEY, editor.value || '');
""",
    """    function saveDraft(updateVisual = true) {
      try {
        queueHistoryCapture();
        safeSetStorage(STORAGE_KEY, editor.value || '');
""",
    "history capture from edits",
)

history_functions = """    function updateHistoryButtons() {
      const pendingChange = historyCurrentMarkdown !== null && (editor.value || '') !== historyCurrentMarkdown;
      if (undoBtn) undoBtn.disabled = undoStack.length === 0 && !pendingChange;
      if (redoBtn) redoBtn.disabled = redoStack.length === 0 || pendingChange;
    }

    function resetHistory(markdown = editor.value || '') {
      clearTimeout(historyTimer);
      historyTimer = null;
      undoStack = [];
      redoStack = [];
      historyCurrentMarkdown = markdown;
      updateHistoryButtons();
    }

    function flushHistoryCapture() {
      clearTimeout(historyTimer);
      historyTimer = null;
      if (historyApplying || documentLoadInProgress) return;

      const currentMarkdown = editor.value || '';
      if (historyCurrentMarkdown === null) {
        historyCurrentMarkdown = currentMarkdown;
        updateHistoryButtons();
        return;
      }
      if (currentMarkdown === historyCurrentMarkdown) return;

      undoStack.push(historyCurrentMarkdown);
      if (undoStack.length > HISTORY_LIMIT) undoStack.shift();
      historyCurrentMarkdown = currentMarkdown;
      redoStack = [];
      updateHistoryButtons();
    }

    function queueHistoryCapture(delay = 450) {
      if (historyApplying || documentLoadInProgress) return;
      clearTimeout(historyTimer);
      updateHistoryButtons();
      historyTimer = setTimeout(flushHistoryCapture, delay);
    }

    function applyHistoryMarkdown(markdown) {
      historyApplying = true;
      clearTimeout(historyTimer);
      historyTimer = null;
      activeMathEditInput = null;
      savedWysiwygRange = null;
      hideTableTools();

      try {
        editor.value = markdown;
        safeSetStorage(STORAGE_KEY, editor.value || '');
        saveImageMap();
        updateNavigation(false);
        forceWysiwygFromMarkdown({ resetScroll: false, focusStart: false });
        renderNow();
      } finally {
        historyApplying = false;
        updateHistoryButtons();
      }
    }

    function undoDocument() {
      if (isVisualModeActive()) commitActiveWysiwygMathEdit({ quiet: true });
      flushHistoryCapture();
      if (!undoStack.length) return;

      const currentMarkdown = editor.value || '';
      const previousMarkdown = undoStack.pop();
      redoStack.push(currentMarkdown);
      if (redoStack.length > HISTORY_LIMIT) redoStack.shift();
      historyCurrentMarkdown = previousMarkdown;
      applyHistoryMarkdown(previousMarkdown);
    }

    function redoDocument() {
      if (isVisualModeActive()) commitActiveWysiwygMathEdit({ quiet: true });
      flushHistoryCapture();
      if (!redoStack.length) return;

      const currentMarkdown = editor.value || '';
      const nextMarkdown = redoStack.pop();
      undoStack.push(currentMarkdown);
      if (undoStack.length > HISTORY_LIMIT) undoStack.shift();
      historyCurrentMarkdown = nextMarkdown;
      applyHistoryMarkdown(nextMarkdown);
    }

    function editorHistoryShortcutTarget(target) {
      return target === editor || target === wysiwygEditor || (wysiwygEditor && wysiwygEditor.contains(target));
    }

"""
replace_once(
    """    function clamp(value, min, max) {
""",
    history_functions + """    function clamp(value, min, max) {
""",
    "history implementation",
)

replace_once(
    """      saveDraft(false);

      requestAnimationFrame(() => {
""",
    """      saveDraft(false);
      resetHistory(editor.value || '');

      requestAnimationFrame(() => {
""",
    "new document history reset",
)

replace_once(
    """        forceWysiwygFromMarkdown({ resetScroll: true, focusStart: false });
        renderNow();
        showToast(`Opened ${file.name}`);
""",
    """        forceWysiwygFromMarkdown({ resetScroll: true, focusStart: false });
        renderNow();
        resetHistory(editor.value || '');
        showToast(`Opened ${file.name}`);
""",
    "opened document history reset",
)

replace_once(
    """    clearBtn.addEventListener('click', clearDraft);
    darkBtn.addEventListener('click', () => {
""",
    """    clearBtn.addEventListener('click', clearDraft);
    undoBtn.addEventListener('pointerdown', event => event.preventDefault());
    redoBtn.addEventListener('pointerdown', event => event.preventDefault());
    undoBtn.addEventListener('click', undoDocument);
    redoBtn.addEventListener('click', redoDocument);
    darkBtn.addEventListener('click', () => {
""",
    "history button handlers",
)

replace_once(
    """    editor.addEventListener('keydown', event => {
      if (event.key === 'Tab') {
""",
    """    document.addEventListener('keydown', event => {
      if (!(event.ctrlKey || event.metaKey) || event.altKey || !editorHistoryShortcutTarget(event.target)) return;
      const key = event.key.toLowerCase();
      if (key === 'z') {
        event.preventDefault();
        if (event.shiftKey) redoDocument();
        else undoDocument();
      } else if (key === 'y') {
        event.preventDefault();
        redoDocument();
      }
    });

    editor.addEventListener('keydown', event => {
      if (event.key === 'Tab') {
""",
    "keyboard shortcuts",
)

replace_once(
    """      setSourceMode(false);
      updateNavigation();
    } catch (error) {
""",
    """      setSourceMode(false);
      updateNavigation();
      resetHistory(editor.value || '');
    } catch (error) {
""",
    "startup history reset",
)

path.write_text(text, encoding="utf-8")

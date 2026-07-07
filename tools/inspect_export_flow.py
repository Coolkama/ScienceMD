#!/usr/bin/env python3
from pathlib import Path
import re

source = Path(__file__).resolve().parents[1] / "index.html"
text = source.read_text(encoding="utf-8")
patterns = [
    r"save as",
    r"saveas",
    r"export",
    r"html",
    r"download",
    r"showSaveFilePicker",
    r"createObjectURL",
    r"Blob\(",
]

lines = text.splitlines()
out = []
for pattern in patterns:
    out.append(f"\n===== PATTERN: {pattern} =====\n")
    regex = re.compile(pattern, re.IGNORECASE)
    matches = []
    for lineno, line in enumerate(lines, start=1):
        if regex.search(line):
            matches.append(lineno)
    out.append(f"matches: {matches}\n")
    for lineno in matches[:40]:
        start = max(1, lineno - 6)
        end = min(len(lines), lineno + 12)
        out.append(f"\n--- lines {start}-{end} (match {lineno}) ---\n")
        for n in range(start, end + 1):
            snippet = lines[n - 1]
            if len(snippet) > 500:
                snippet = snippet[:500] + " …[truncated]"
            out.append(f"{n}: {snippet}\n")

report = Path(__file__).with_name("export_flow_report.txt")
report.write_text("".join(out), encoding="utf-8")
print(report)

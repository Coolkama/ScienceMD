    function splitMarkdownTableRow(line) {
      const source = String(line || '').trim().replace(/^\|/, '').replace(/\|$/, '');
      const cells = [];
      let current = '';
      let escaped = false;
      for (const character of source) {
        if (escaped) {
          current += character;
          escaped = false;
        } else if (character === '\\') {
          escaped = true;
          current += character;
        } else if (character === '|') {
          cells.push(current.trim());
          current = '';
        } else {
          current += character;
        }
      }
      cells.push(current.trim());
      return cells;
    }

    function isMarkdownTableSeparator(line) {
      const cells = splitMarkdownTableRow(line);
      return cells.length > 0 && cells.every(cell => /^:?-{3,}:?$/.test(cell));
    }

    function buildLatexTable(headerLine, separatorLine, rowLines) {
      const headers = splitMarkdownTableRow(headerLine);
      const separators = splitMarkdownTableRow(separatorLine);
      const rows = rowLines.map(splitMarkdownTableRow);
      const columnSpec = separators.map(cell => {
        if (/^:-+:$/.test(cell)) return String.raw`>{\centering\arraybackslash}X`;
        if (/^-+:$/.test(cell)) return String.raw`>{\raggedleft\arraybackslash}X`;
        return String.raw`>{\raggedright\arraybackslash}X`;
      }).join(' ');
      const formatRow = cells => headers.map((_, index) => convertInlineMarkdownToLatex(cells[index] || '')).join(' & ') + String.raw` \\`;
      return [
        String.raw`\begin{table}[htbp]`,
        String.raw`\centering`,
        String.raw`\begin{tabularx}{\linewidth}{${columnSpec}}`,
        String.raw`\toprule`,
        formatRow(headers),
        String.raw`\midrule`,
        ...rows.map(formatRow),
        String.raw`\bottomrule`,
        String.raw`\end{tabularx}`,
        String.raw`\end{table}`
      ].join('\n');
    }


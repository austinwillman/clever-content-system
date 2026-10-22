export function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = "";
  let quoted = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];
    if (char === '"' && quoted && next === '"') {
      cell += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      row.push(cell);
      cell = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") index += 1;
      row.push(cell);
      rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += char;
    }
  }

  if (cell.length || row.length) {
    row.push(cell);
    rows.push(row);
  }

  const [headers, ...records] = rows.filter((candidate) => candidate.some(Boolean));
  if (!headers) return [];

  return records.map((record, index) => {
    if (record.length !== headers.length) {
      throw new Error(`CSV row ${index + 2} has ${record.length} cells, expected ${headers.length}`);
    }
    return Object.fromEntries(headers.map((header, cellIndex) => [header, record[cellIndex]]));
  });
}

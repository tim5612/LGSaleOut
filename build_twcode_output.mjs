import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = path.resolve("期初與實銷資料/TWCode.xlsx");
const outputDir = path.resolve("outputs/twcode_grouping");
const outputPath = path.join(outputDir, "TWCode_整理完成.xlsx");

await fs.mkdir(outputDir, { recursive: true });
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(inputPath));
const sheet = workbook.worksheets.getItemAt(0);

const before = await workbook.render({ sheetName: sheet.name, range: "A1:H20", scale: 1, format: "png" });
await fs.writeFile(path.join(outputDir, "before.png"), new Uint8Array(await before.arrayBuffer()));

const used = sheet.getUsedRange(true);
const rows = used.values;
const lastRow = rows.length;
const groups = new Map();

for (let i = 1; i < rows.length; i += 1) {
  const twCode = rows[i]?.[0];
  const dealer = rows[i]?.[1];
  if (twCode == null || dealer == null || String(dealer).trim() === "") continue;
  const key = String(dealer);
  if (!groups.has(key)) groups.set(key, { firstRow: i + 1, codes: [] });
  groups.get(key).codes.push(twCode);
}

const maxCodes = Math.max(...[...groups.values()].map((group) => group.codes.length));
sheet.getRangeByIndexes(1, 2, Math.max(lastRow - 1, 1), maxCodes).clear({ applyTo: "contents" });

for (const group of groups.values()) {
  sheet.getRangeByIndexes(group.firstRow - 1, 2, 1, group.codes.length).values = [group.codes];
}

workbook.recalculate();
const inspection = await workbook.inspect({
  kind: "table",
  range: `${sheet.name}!A1:H20`,
  include: "values,formulas",
  tableMaxRows: 20,
  tableMaxCols: 8,
  maxChars: 8000,
});
console.log(inspection.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
  maxChars: 3000,
});
console.log(errors.ndjson);

const after = await workbook.render({ sheetName: sheet.name, range: "A1:H20", scale: 1.5, format: "png" });
await fs.writeFile(path.join(outputDir, "after.png"), new Uint8Array(await after.arrayBuffer()));

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(JSON.stringify({ outputPath, sheet: sheet.name, records: lastRow - 1, dealers: groups.size, maxCodes }));

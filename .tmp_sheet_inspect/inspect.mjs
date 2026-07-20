import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const files = process.argv.slice(2);
for (const path of files) {
  const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(path));
  const summary = await wb.inspect({
    kind: "workbook,sheet,table,region",
    maxChars: 14000,
    tableMaxRows: 15,
    tableMaxCols: 20,
    tableMaxCellChars: 100,
  });
  process.stdout.write(`\n=== ${path} ===\n${summary.ndjson}\n`);
}

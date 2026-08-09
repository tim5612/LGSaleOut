const fs = require('fs');

const output = 'Codex筆記/LGSale_ERD.drawio';
const rowH = 26;
const titleH = 38;
const tableW = 390;

const tables = [
  {name:'Employee', zh:'員工', module:'人員與組織', x:60,y:120, fields:[
    ['EmployeeId','bigint','PK','員工識別碼'],['EmployeeNo','nvarchar','UK','員工編號'],['EmployeeName','nvarchar','','員工姓名'],['HireDate','date','','到職日期'],['TerminationDate','date','NULL','離職日期'],['EmploymentStatus','varchar','','在職狀態'],['IsLoginEnabled','bit','','是否允許登入']]},
  {name:'EmployeePositionHistory', zh:'員工職級歷史', module:'人員與組織', x:500,y:80, fields:[
    ['EmployeePositionHistoryId','bigint','PK','職級歷史識別碼'],['EmployeeId','bigint','FK','員工識別碼'],['PositionLevel','varchar','','職級'],['StartDateTime','datetime2','','生效開始時間'],['EndDateTime','datetime2','NULL','生效結束時間'],['ChangeReason','nvarchar','','異動原因'],['CreatedAt','datetime2','','建立時間'],['CreatedByEmployeeId','bigint','FK','建立者員工識別碼']]},
  {name:'OrganizationUnit', zh:'組織單位', module:'人員與組織', x:60,y:460, fields:[
    ['OrgUnitId','bigint','PK','組織單位識別碼'],['OrgUnitCode','varchar','UK','組織單位代碼'],['OrgUnitName','nvarchar','','組織單位名稱'],['IsActive','bit','','是否啟用']]},
  {name:'EmployeeOrgAssignmentHistory', zh:'員工組織歸屬歷史', module:'人員與組織', x:500,y:410, fields:[
    ['EmployeeOrgAssignmentId','bigint','PK','組織歸屬識別碼'],['EmployeeId','bigint','FK','員工識別碼'],['OrgUnitId','bigint','FK','組織單位識別碼'],['StartDateTime','datetime2','','生效開始時間'],['EndDateTime','datetime2','NULL','生效結束時間'],['ChangeReason','nvarchar','','異動原因'],['CreatedAt','datetime2','','建立時間'],['CreatedByEmployeeId','bigint','FK','建立者員工識別碼']]},
  {name:'Dealer', zh:'經銷商', module:'經銷商與銷售', x:950,y:100, fields:[
    ['DealerId','bigint','PK','經銷商識別碼'],['DealerCode','varchar','UK','經銷商代碼'],['DealerName','nvarchar','','經銷商名稱'],['DealerStatus','varchar','','經銷商狀態'],['CreatedAt','datetime2','','建立時間']]},
  {name:'DealerAssignmentHistory', zh:'經銷商負責人歷史', module:'經銷商與銷售', x:950,y:380, fields:[
    ['DealerAssignmentId','bigint','PK','經銷商指派識別碼'],['DealerId','bigint','FK','經銷商識別碼'],['EmployeeId','bigint','FK','負責員工識別碼'],['StartDateTime','datetime2','','生效開始時間'],['EndDateTime','datetime2','NULL','生效結束時間'],['ChangeReason','nvarchar','','異動原因'],['CreatedAt','datetime2','','建立時間'],['CreatedByEmployeeId','bigint','FK','建立者員工識別碼']]},
  {name:'Sales', zh:'銷售紀錄', module:'經銷商與銷售', x:1390,y:100, fields:[
    ['SaleId','bigint','PK','銷售識別碼'],['DealerId','bigint','FK','經銷商識別碼'],['SaleDateTime','datetime2','','銷售日期時間'],['Amount','decimal(18,2)','','銷售金額'],['DealerAssignmentId','bigint','FK','經銷商指派識別碼'],['ResponsibleEmployeeId','bigint','FK','負責員工識別碼'],['CreatedAt','datetime2','','建立時間'],['CreatedByEmployeeId','bigint','FK','建立者員工識別碼'],['UpdatedAt','datetime2','NULL','更新時間'],['UpdatedByEmployeeId','bigint','FK NULL','更新者員工識別碼']]},
  {name:'ImportBatch', zh:'資料匯入批次', module:'匯入與庫存', x:60,y:850, fields:[
    ['ImportBatchId','bigint','PK','匯入批次識別碼'],['ImportType','varchar','','匯入類型'],['DataMonth','char(6)','NULL','資料月份 YYYYMM'],['DataDate','date','NULL','資料日期'],['OriginalFileName','nvarchar','','原始檔名'],['StoredFileName','nvarchar','','儲存檔名'],['StoredFilePath','nvarchar','','儲存檔案路徑'],['FileHash','varchar','','檔案雜湊值'],['FileSize','bigint','','檔案大小'],['ImportStatus','varchar','','匯入狀態'],['ReplacedBatchId','bigint','FK NULL','被取代批次識別碼'],['TotalRowCount','int','','總資料列數'],['SuccessRowCount','int','','成功資料列數'],['ErrorRowCount','int','','錯誤資料列數'],['ErrorSummary','nvarchar','NULL','錯誤摘要'],['ErrorReportPath','nvarchar','NULL','錯誤報告路徑'],['ImportedAt','datetime2','','匯入時間'],['ImportedByEmployeeId','bigint','FK','匯入者員工識別碼']]},
  {name:'MonthlyOpeningInventoryDetail', zh:'每月期初庫存明細', module:'匯入與庫存', x:500,y:850, fields:[
    ['OpeningInventoryDetailId','bigint','PK','期初庫存明細識別碼'],['ImportBatchId','bigint','FK UQ1','匯入批次識別碼'],['SourceRowNumber','int','','來源資料列號碼'],['DealerId','bigint','FK UQ1','經銷商識別碼'],['ProductId','bigint','FK UQ1','產品識別碼'],['OpeningQuantity','int','','期初庫存數量']]},
  {name:'SellInTransaction', zh:'進貨交易', module:'匯入與庫存', x:940,y:850, fields:[
    ['SellInTransactionId','bigint','PK','進貨交易識別碼'],['ImportBatchId','bigint','FK','匯入批次識別碼'],['SourceRowNumber','int','','來源資料列號碼'],['DealerId','bigint','FK','經銷商識別碼'],['ProductId','bigint','FK','產品識別碼'],['SalesDocumentNo','varchar','UQ?','銷售文件號碼'],['SalesDocumentItemNo','varchar','UQ?','銷售文件項次'],['InvoiceNo','varchar','NULL','發票號碼'],['OrderDate','date','','訂單日期'],['BillingDate','date','','開立帳單日期'],['InvoiceDate','date','NULL','發票日期'],['InventoryEffectiveDate','date','','庫存生效日期'],['Quantity','decimal(18,3)','','交易數量'],['TransactionType','varchar','','交易類型'],['TransactionStatus','varchar','','交易狀態'],['ReviewStatus','varchar','','審核狀態'],['CreatedAt','datetime2','','建立時間'],['UpdatedAt','datetime2','NULL','更新時間']]},
  {name:'Product', zh:'產品', module:'匯入與庫存', x:1380,y:850, fields:[
    ['ProductId','bigint','PK','產品識別碼'],['ProductCode','varchar','UK','產品代碼'],['ProductName','nvarchar','','產品名稱'],['CategoryLevel1','nvarchar','NULL','第一層產品分類'],['CategoryLevel2','nvarchar','NULL','第二層產品分類'],['IsActive','bit','','是否啟用'],['CreatedAt','datetime2','','建立時間']]},
  {name:'StoreVisit', zh:'巡店紀錄', module:'巡店', x:1830,y:100, fields:[
    ['StoreVisitId','bigint','PK','巡店識別碼'],['DealerId','bigint','FK','經銷商識別碼'],['DealerAssignmentId','bigint','FK','經銷商指派識別碼'],['ResponsibleEmployeeId','bigint','FK','負責員工識別碼'],['PreviousStoreVisitId','bigint','FK NULL','前次巡店識別碼'],['VisitDateTime','datetime2','','巡店日期時間'],['PeriodStartDateTime','datetime2','','統計期間開始時間'],['PeriodEndDateTime','datetime2','','統計期間結束時間'],['VisitStatus','varchar','','巡店狀態'],['CreatedAt','datetime2','','建立時間'],['CreatedByEmployeeId','bigint','FK','建立者員工識別碼'],['UpdatedAt','datetime2','NULL','更新時間'],['UpdatedByEmployeeId','bigint','FK NULL','更新者員工識別碼']]},
  {name:'StoreVisitProductDetail', zh:'巡店產品明細', module:'巡店', x:1830,y:570, fields:[
    ['StoreVisitProductDetailId','bigint','PK','巡店產品明細識別碼'],['StoreVisitId','bigint','FK UQ1','巡店識別碼'],['ProductId','bigint','FK UQ1','產品識別碼'],['SellOutQuantity','decimal(18,3)','','銷售出庫數量'],['DisplayQuantity','int','','陳列數量'],['IsSellOutChecked','bit','','是否確認銷售出庫'],['IsDisplayChecked','bit','','是否確認陳列數量'],['CreatedAt','datetime2','','建立時間'],['UpdatedAt','datetime2','NULL','更新時間']]}
];

const relations = [
  ['Employee','EmployeeId','EmployeePositionHistory','EmployeeId','任職員工'],
  ['Employee','EmployeeId','EmployeePositionHistory','CreatedByEmployeeId','建立者'],
  ['Employee','EmployeeId','EmployeeOrgAssignmentHistory','EmployeeId','歸屬員工'],
  ['OrganizationUnit','OrgUnitId','EmployeeOrgAssignmentHistory','OrgUnitId','所屬組織'],
  ['Employee','EmployeeId','EmployeeOrgAssignmentHistory','CreatedByEmployeeId','建立者'],
  ['Dealer','DealerId','DealerAssignmentHistory','DealerId','被指派經銷商'],
  ['Employee','EmployeeId','DealerAssignmentHistory','EmployeeId','負責員工'],
  ['Employee','EmployeeId','DealerAssignmentHistory','CreatedByEmployeeId','建立者'],
  ['Dealer','DealerId','Sales','DealerId','銷售經銷商'],
  ['DealerAssignmentHistory','DealerAssignmentId','Sales','DealerAssignmentId','銷售時指派'],
  ['Employee','EmployeeId','Sales','ResponsibleEmployeeId','負責員工'],
  ['Employee','EmployeeId','Sales','CreatedByEmployeeId','建立者'],
  ['Employee','EmployeeId','Sales','UpdatedByEmployeeId','更新者'],
  ['Employee','EmployeeId','ImportBatch','ImportedByEmployeeId','匯入者'],
  ['ImportBatch','ImportBatchId','ImportBatch','ReplacedBatchId','取代批次','optional'],
  ['ImportBatch','ImportBatchId','MonthlyOpeningInventoryDetail','ImportBatchId','來源批次'],
  ['Dealer','DealerId','MonthlyOpeningInventoryDetail','DealerId','庫存經銷商'],
  ['Product','ProductId','MonthlyOpeningInventoryDetail','ProductId','庫存產品'],
  ['ImportBatch','ImportBatchId','SellInTransaction','ImportBatchId','來源批次'],
  ['Dealer','DealerId','SellInTransaction','DealerId','進貨經銷商'],
  ['Product','ProductId','SellInTransaction','ProductId','進貨產品'],
  ['Dealer','DealerId','StoreVisit','DealerId','巡店經銷商'],
  ['DealerAssignmentHistory','DealerAssignmentId','StoreVisit','DealerAssignmentId','巡店時指派'],
  ['Employee','EmployeeId','StoreVisit','ResponsibleEmployeeId','負責員工'],
  ['Employee','EmployeeId','StoreVisit','CreatedByEmployeeId','建立者'],
  ['Employee','EmployeeId','StoreVisit','UpdatedByEmployeeId','更新者'],
  ['StoreVisit','StoreVisitId','StoreVisit','PreviousStoreVisitId','前次巡店','optional'],
  ['StoreVisit','StoreVisitId','StoreVisitProductDetail','StoreVisitId','巡店明細'],
  ['Product','ProductId','StoreVisitProductDetail','ProductId','巡店產品']
];

const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const id = s => s.replace(/[^A-Za-z0-9_]/g,'_');
const moduleStyles = {
  '人員與組織':['#dae8fc','#6c8ebf'],
  '經銷商與銷售':['#fff2cc','#d6b656'],
  '匯入與庫存':['#d5e8d4','#82b366'],
  '巡店':['#e1d5e7','#9673a6']
};

let cells = [];
cells.push('<mxCell id="0"/>','<mxCell id="1" parent="0"/>');

const section = (name,x,y,w,color) => {
  cells.push(`<mxCell id="section_${id(name)}" value="${esc(name)}" style="text;html=1;strokeColor=none;fillColor=none;fontSize=18;fontStyle=1;fontColor=${color};align=left;verticalAlign=middle;" vertex="1" parent="1"><mxGeometry x="${x}" y="${y}" width="${w}" height="30" as="geometry"/></mxCell>`);
};
section('人員與組織',40,25,850,'#2f5597');
section('經銷商與銷售',930,25,830,'#9c6500');
section('巡店',1810,25,430,'#7030a0');
section('匯入與庫存',40,795,1720,'#38761d');

const rowIds = {};
for (const t of tables) {
  const [fill,stroke] = moduleStyles[t.module];
  const h = titleH + t.fields.length * rowH;
  const tid = `table_${t.name}`;
  cells.push(`<UserObject id="${tid}" label="${esc(t.name)}｜${esc(t.zh)}" dbTable="${esc(t.name)}" dbDescription="${esc(t.zh)}"><mxCell style="swimlane;html=1;startSize=${titleH};horizontal=1;rounded=1;collapsible=1;fontStyle=1;fontSize=15;fillColor=${fill};strokeColor=${stroke};swimlaneFillColor=#ffffff;" vertex="1" parent="1"><mxGeometry x="${t.x}" y="${t.y}" width="${tableW}" height="${h}" as="geometry"/></mxCell></UserObject>`);
  t.fields.forEach((f,i) => {
    const [name,type,key,zh] = f;
    const rid = `row_${t.name}_${name}`;
    rowIds[`${t.name}.${name}`] = rid;
    const keyText = key || '';
    const keyColor = key.includes('PK') ? '#d79b00' : key.includes('FK') ? '#b85450' : key.includes('UK') || key.includes('UQ') ? '#6c8ebf' : '#999999';
    const html = `<div style='display:flex;white-space:nowrap'><span style='display:inline-block;width:58px;color:${keyColor};font-weight:bold'>${keyText}</span><span style='display:inline-block;width:155px;font-family:monospace'>${name}</span><span style='display:inline-block;width:92px;color:#666666'>${type}</span><span>${zh}</span></div>`;
    cells.push(`<UserObject id="${rid}" label="${esc(html)}" dbColumn="${esc(name)}" dbType="${esc(type)}" dbKey="${esc(key)}" dbDescription="${esc(zh)}"><mxCell style="text;html=1;align=left;verticalAlign=middle;spacingLeft=8;spacingRight=4;overflow=hidden;whiteSpace=wrap;strokeColor=${stroke};strokeWidth=0.5;fillColor=#ffffff;connectable=1;portConstraint=eastwest;" vertex="1" parent="${tid}"><mxGeometry x="0" y="${titleH + i*rowH}" width="${tableW}" height="${rowH}" as="geometry"/></mxCell></UserObject>`);
  });
}

relations.forEach((r,i) => {
  const [pt,pf,ct,cf,label,optional] = r;
  const source = rowIds[`${pt}.${pf}`];
  const target = rowIds[`${ct}.${cf}`];
  if (!source || !target) throw new Error(`Missing relation endpoint ${pt}.${pf} -> ${ct}.${cf}`);
  const startArrow = optional ? 'ERzeroToOne' : 'ERone';
  const style = `edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=18;html=1;endArrow=ERmany;endFill=0;startArrow=${startArrow};startFill=0;strokeWidth=1.4;strokeColor=#5b6573;fontSize=10;labelBackgroundColor=#ffffff;`;
  cells.push(`<UserObject id="rel_${i+1}" label="${esc(label)}" parentTable="${pt}" parentColumn="${pf}" childTable="${ct}" childColumn="${cf}"><mxCell style="${style}" edge="1" parent="1" source="${source}" target="${target}"><mxGeometry relative="1" as="geometry"/></mxCell></UserObject>`);
});

const note = (idv,x,y,w,h,title,body,fill,stroke) => {
  const value = `<b>${title}</b><br>${body.replace(/\n/g,'<br>')}`;
  cells.push(`<mxCell id="${idv}" value="${esc(value)}" style="shape=note;whiteSpace=wrap;html=1;backgroundOutline=1;size=14;fillColor=${fill};strokeColor=${stroke};fontSize=11;align=left;verticalAlign=top;spacing=8;" vertex="1" parent="1"><mxGeometry x="${x}" y="${y}" width="${w}" height="${h}" as="geometry"/></mxCell>`);
};
note('legend',1810,1050,430,170,'圖例與命名','PK 主鍵　FK 外鍵　UK 唯一鍵　NULL 可空值\nUQ1 同組複合唯一鍵　UQ? 唯一鍵待確認\n連線端點直接附著於實際 PK／FK 欄位\nTable 與欄位英文名稱為未來 T-SQL 識別名稱','#f5f5f5','#666666');
note('pending',1810,1240,430,190,'優先討論項目','1. Sell-in 防重鍵與退貨／取消規則\n2. 歷史有效期間不得重疊\n3. 經銷商同時間可有幾位負責人\n4. 每月正式期初庫存批次唯一性\n5. FK 的 NULL 與刪除／更新策略\n6. Sales 是否與 SellInTransaction 意義重複','#fff2cc','#d6b656');

const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<mxfile host="app.diagrams.net" modified="${new Date().toISOString()}" agent="Codex" version="26.0.16" type="device" compressed="false">\n  <diagram id="LGSaleERD" name="LGSale ERD">\n    <mxGraphModel dx="2400" dy="1500" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="2400" pageHeight="1500" math="0" shadow="0">\n      <root>\n        ${cells.join('\n        ')}\n      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>\n`;

fs.writeFileSync(output, xml, 'utf8');
console.log(`Created ${output}: ${tables.length} tables, ${relations.length} relations, ${xml.length} chars`);

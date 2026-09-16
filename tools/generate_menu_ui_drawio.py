"""Generate the editable role-by-role Menu/UI discussion diagram."""

from pathlib import Path
from xml.etree import ElementTree as ET


OUT = Path(__file__).resolve().parents[1] / "Codex筆記" / "Menu與UI.drawio"
W, H = 1680, 1110
NAVY = "#19334D"
BLUE = "#14639A"
PALE = "#EAF3F9"
BG = "#F4F7FA"
LINE = "#D5E0E9"
INK = "#203448"
MUTED = "#64778A"
GREEN = "#E6F5ED"
AMBER = "#FFF3DE"


class Page:
    def __init__(self, page_id, name, title, subtitle):
        self.diagram = ET.Element("diagram", id=page_id, name=name)
        self.model = ET.SubElement(
            self.diagram, "mxGraphModel", grid="1", page="1", gridSize="10",
            guides="1", tooltips="1", connect="1", arrows="1", fold="1",
            pageScale="1", pageWidth=str(W), pageHeight=str(H), math="0", shadow="0",
        )
        root = ET.SubElement(self.model, "root")
        ET.SubElement(root, "mxCell", id="0")
        ET.SubElement(root, "mxCell", id="1", parent="0")
        self.root = root
        self.n = 0
        self.box(0, 0, W, H, "", BG, BG, radius=False)
        self.box(36, 25, 1608, 66, "", NAVY, NAVY)
        self.label(59, 37, 550, 28, title, 22, "#FFFFFF", bold=True)
        self.label(660, 43, 935, 22, subtitle, 13, "#D7E6F0", align="right")

    def box(self, x, y, w, h, value="", fill="#FFFFFF", stroke=LINE,
            font=13, color=INK, bold=False, align="left", radius=True):
        self.n += 1
        style = (
            f"rounded={1 if radius else 0};arcSize=10;whiteSpace=wrap;html=1;"
            f"fillColor={fill};strokeColor={stroke};fontColor={color};fontSize={font};"
            f"fontStyle={1 if bold else 0};align={align};verticalAlign=middle;"
            "spacingLeft=11;spacingRight=9;"
        )
        cell = ET.SubElement(self.root, "mxCell", id=f"c{self.n}", value=value,
                             style=style, vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=str(x), y=str(y), width=str(w),
                      height=str(h), as_="geometry")
        cell[-1].set("as", "geometry")
        cell[-1].attrib.pop("as_", None)
        return cell

    def label(self, x, y, w, h, value, font=13, color=INK, bold=False, align="left"):
        return self.box(x, y, w, h, value, "none", "none", font, color, bold, align, False)

    def pill(self, x, y, w, text, fill=PALE, color=BLUE):
        self.box(x, y, w, 29, text, fill, fill, 12, color, True, "center")

    def finish(self):
        return self.diagram


def shell(p, role, scope, menu, desktop_title, phone_title, phone_allowed=True):
    # Desktop browser and navigation.
    p.box(36, 110, 1055, 780, "", "#FFFFFF")
    p.box(36, 110, 1055, 39, "", "#E3EBF2", "#E3EBF2")
    p.label(52, 116, 500, 24, "●  ●  ●     LGSale 管理後台", 13, MUTED, True)
    p.box(36, 149, 245, 741, "", NAVY, NAVY, radius=False)
    p.label(54, 170, 196, 32, "LGSale", 21, "#FFFFFF", True)
    p.label(54, 203, 195, 22, role + "｜桌機 Menu", 12, "#B9D1E1")
    y = 246
    for group, items in menu:
        if group:
            p.label(53, y, 202, 22, group, 12, "#83AFCB", True)
            y += 29
        for item in items:
            p.box(50, y, 216, 37, "▸  " + item, "#2B5473" if y < 310 else NAVY,
                  "#2B5473" if y < 310 else NAVY, 13, "#FFFFFF", False)
            y += 42
        y += 9
    p.label(54, 836, 200, 30, "●  " + role + "｜Passkey 已登入", 11, "#D6E4EE")
    p.label(304, 174, 750, 35, desktop_title, 23, INK, True)
    p.pill(305, 220, min(710, max(265, len("資料範圍：" + scope) * 15 + 20)),
           "資料範圍：" + scope)

    # Phone / mobile data surface.
    p.box(1122, 110, 522, 780, "", "#FFFFFF")
    p.label(1145, 124, 450, 30, phone_title, 20, INK, True)
    p.box(1220, 168, 328, 640, "", "#1B354C", "#1B354C")
    p.box(1232, 180, 304, 614, "", "#FFFFFF", "#FFFFFF")
    p.box(1232, 180, 304, 51, "LGSale　　" + role, NAVY, NAVY,
          15, "#FFFFFF", True)
    if phone_allowed:
        p.box(1232, 748, 304, 46, "工作台     經銷商     任務     我的", "#EDF4F8", "#EDF4F8",
              11, BLUE, True, "center")
    else:
        p.box(1232, 748, 304, 46, "Passkey 授權桌機登入", "#EDF4F8", "#EDF4F8",
              12, BLUE, True, "center")


def desktop_tabs(p, labels, y=267):
    x = 305
    for i, text in enumerate(labels):
        width = max(105, len(text) * 19 + 32)
        p.box(x, y, width, 37, text, BLUE if i == 0 else "#FFFFFF",
              BLUE if i == 0 else LINE, 13, "#FFFFFF" if i == 0 else INK,
              i == 0, "center")
        x += width + 8


def table(p, x, y, widths, headers, rows, row_h=48):
    total = sum(widths)
    p.box(x, y, total, 40, "", "#EAF0F5", LINE, radius=False)
    cursor = x
    for width, header in zip(widths, headers):
        p.label(cursor + 3, y + 5, width - 6, 30, header, 12, MUTED, True)
        cursor += width
    for ri, row in enumerate(rows):
        yy = y + 40 + ri * row_h
        p.box(x, yy, total, row_h, "", "#FFFFFF" if ri % 2 == 0 else "#F8FAFC", LINE, radius=False)
        cursor = x
        for width, val in zip(widths, row):
            p.label(cursor + 3, yy + 4, width - 6, row_h - 8, val, 12, INK)
            cursor += width


def foot(p, lines, pending=None):
    p.box(36, 916, 1608, 166, "", "#FFFFFF")
    p.label(57, 929, 1500, 28, "權限與 Menu 說明", 17, INK, True)
    y = 961
    for line in lines:
        p.label(62, y, 1518, 23, "• " + line, 12, INK)
        y += 25
    if pending:
        p.label(62, y + 2, 1518, 24, "待討論：" + pending, 12, "#9A5F0A", True)


def phone_card(p, y, title, detail, fill="#F2F7FA"):
    p.box(1250, y, 270, 92, "", fill, LINE)
    p.label(1260, y + 9, 245, 26, title, 14, INK, True)
    p.label(1260, y + 38, 245, 45, detail, 11, MUTED)


pages = []

# 1. Sales representative
p = Page("sales", "01 業務", "業務｜個人負責範圍", "桌機：任務、照片、PSI　　手機：任務、實銷與陳列")
shell(p, "業務", "自己負責的經銷商", [("工作資料", ["巡店任務", "PSI 月報"])],
      "我的巡店任務", "手機｜我的經銷商與任務")
desktop_tabs(p, ["巡店任務", "PSI 月報"])
p.box(305, 325, 750, 52, "搜尋任務、經銷商　　期間：全部　　狀態：全部", "#FFFFFF")
table(p, 305, 391, [270, 198, 140, 142], ["任務", "經銷商", "進度", "操作"],
      [["新品陳列檢查", "民生家電", "已完成", "查看照片"],
       ["秋季促銷巡店", "光華電器", "待執行", "查看任務"],
       ["門市展示維護", "永安電器", "已完成", "查看照片"]])
p.box(305, 635, 750, 174, "", PALE)
p.label(323, 650, 700, 25, "PSI 頁面示意", 16, INK, True)
p.label(323, 685, 700, 95, "月份　2026-09　｜　經銷商：自己負責的門市\n期初庫存　＋　SaleIn　－　實銷　＝　期末庫存\n可切換任務與 PSI；其他維護入口不顯示。", 13, INK)
phone_card(p, 254, "我的經銷商", "只列自己現行負責的經銷商。")
phone_card(p, 362, "巡店任務", "查看與執行自己負責門市的任務；上傳照片。")
phone_card(p, 470, "實銷與陳列", "查看自己負責門市的回報；輸入權限沿用現有流程。")
foot(p, ["Menu 只顯示巡店任務與 PSI；隱藏人員、經銷商、匯入、Passkey 與權限設定。",
         "資料範圍必須由後端判定，不能依靠畫面篩選或隱藏按鈕。"],
     "任務建立／修改與手機回報的細項操作權限，可由 Designer 再分別設定。")
pages.append(p.finish())

# 2. Director
p = Page("director", "02 處長", "處長｜所屬處所範圍", "桌機：該處所任務、照片、PSI　　手機：該處所任務、實銷與陳列")
shell(p, "處長", "該處所業務負責的經銷商", [("工作資料", ["巡店任務", "PSI 月報"])],
      "所屬處所巡店任務", "手機｜所屬處所工作台")
desktop_tabs(p, ["巡店任務", "PSI 月報"])
p.box(305, 325, 750, 52, "處所：台北一處　　業務：全部　　搜尋任務／經銷商", "#FFFFFF")
table(p, 305, 391, [260, 180, 170, 140], ["任務", "負責業務", "門市進度", "操作"],
      [["新品陳列檢查", "王正文", "12 / 15 家", "查看照片"],
       ["秋季促銷巡店", "陳小明", "8 / 10 家", "查看照片"],
       ["門市展示維護", "林怡君", "9 / 9 家", "查看照片"]])
p.box(305, 635, 750, 174, "", PALE)
p.label(323, 650, 700, 25, "PSI 頁面示意", 16, INK, True)
p.label(323, 685, 700, 95, "月份　2026-09　｜　處所：台北一處（固定）\n可依該處所的業務或經銷商縮小範圍。\n不能切換至其他處所。", 13, INK)
phone_card(p, 254, "處所經銷商", "列出本處所業務現行負責的門市。")
phone_card(p, 362, "巡店任務", "查看本處所業務負責門市的任務與照片。")
phone_card(p, 470, "實銷與陳列", "查看本處所業務負責門市的回報。")
foot(p, ["Menu 與業務相同，差別在伺服器限定的資料範圍。",
         "所屬處所依員工目前有效的處所歷程取得。"],
     "處長是否能替所屬業務執行手機任務與修改回報，需另定操作權限。")
pages.append(p.finish())

# 3. Manager
p = Page("manager", "03 經理", "經理｜全公司任務與 PSI", "桌機僅有任務與 PSI；手機不提供資料畫面")
shell(p, "經理", "所有業務負責的經銷商", [("工作資料", ["巡店任務", "PSI 月報"])],
      "全公司巡店任務", "手機｜不提供資料", phone_allowed=False)
desktop_tabs(p, ["巡店任務", "PSI 月報"])
p.box(305, 325, 750, 52, "處所：全部　　業務：全部　　搜尋任務／經銷商", "#FFFFFF")
table(p, 305, 391, [270, 198, 140, 142], ["任務", "負責處所／業務", "進度", "操作"],
      [["新品陳列檢查", "台北一處／王正文", "28 / 32 家", "查看照片"],
       ["秋季促銷巡店", "新竹處／陳小明", "21 / 30 家", "查看照片"],
       ["門市展示維護", "中區／林怡君", "完成", "查看照片"]])
p.box(305, 635, 750, 174, "", AMBER)
p.label(323, 651, 700, 27, "個別經理可由 Designer 開放任務操作", 16, INK, True)
p.label(323, 690, 700, 90, "預設：查看任務、照片、PSI。\n例外：指定經理可開啟「建立任務」；未被開放的經理仍只可瀏覽。\n其他管理功能即使知道網址也不得存取。", 13, INK)
phone_card(p, 277, "不顯示手機資料", "任務、經銷商、實銷與陳列均不可查看。", AMBER)
phone_card(p, 396, "可用 Passkey 授權桌機", "手機僅作為桌機登入的驗證裝置。", PALE)
foot(p, ["經理預設 Menu 只有巡店任務及 PSI；人員、匯入、Passkey 等全部不顯示。",
         "Designer 對單一經理開啟任務建立等操作時，只改該人的操作權限，不改其他經理。"],
     "可開放的任務動作需拆成建立、修改、暫停、樣本照片等獨立項目。")
pages.append(p.finish())

# 4. Management
p = Page("management", "04 管理", "管理｜業務資料與後台維護", "桌機：完整管理工作台　　手機：全公司業務負責範圍")
shell(p, "管理", "所有業務負責的經銷商", [
    ("工作資料", ["巡店任務", "實銷與陳列", "PSI 月報"]),
    ("主檔與異動", ["員工與處所", "經銷商", "人員與經銷商異動"]),
    ("匯入與帳號", ["期初庫存匯入", "SaleIn 匯入", "Passkey 帳號"]),
], "管理工作台", "手機｜全公司業務範圍")
p.box(305, 266, 750, 77, "", PALE)
p.label(323, 278, 710, 25, "任務維護", 16, INK, True)
p.label(323, 308, 710, 22, "新增／發布任務　•　任務修改　•　查看照片與設定樣本", 12, INK)
p.box(305, 359, 359, 105, "", "#FFFFFF")
p.label(320, 370, 320, 25, "人員與經銷商", 16, INK, True)
p.label(320, 403, 320, 45, "員工、處所、經銷商主檔\n負責人移轉與處所異動", 12, MUTED)
p.box(680, 359, 375, 105, "", "#FFFFFF")
p.label(695, 370, 340, 25, "實銷、陳列與 PSI", 16, INK, True)
p.label(695, 403, 340, 45, "查看全部業務負責門市\n依處所、業務、月份查詢", 12, MUTED)
p.box(305, 480, 359, 105, "", "#FFFFFF")
p.label(320, 491, 320, 25, "資料匯入", 16, INK, True)
p.label(320, 524, 320, 45, "期初庫存匯入\nSaleIn 匯入與問題清單", 12, MUTED)
p.box(680, 480, 375, 105, "", "#FFFFFF")
p.label(695, 491, 340, 25, "Passkey 帳號", 16, INK, True)
p.label(695, 524, 340, 45, "登入開關、邀請 QR Code\n裝置查看與撤銷", 12, MUTED)
p.box(305, 613, 750, 100, "Designer 權限設定：不可見、不可存取、不可自行授權。", AMBER,
      AMBER, 15, "#805315", True)
phone_card(p, 254, "全公司業務負責門市", "可查看有業務負責的所有經銷商。")
phone_card(p, 362, "巡店任務", "可查看所有業務負責門市的任務與照片。")
phone_card(p, 470, "實銷與陳列", "可查看所有業務負責門市的正式回報。")
foot(p, ["管理負責任務、人員、經銷商、異動、匯入及 Passkey 等後台操作。",
         "管理即使有完整後台維護權，仍不能開啟或修改 Designer 的權限設定。"],
     "手機端目前定義為可看；是否可代業務輸入或完成任務，需另定操作權限。")
pages.append(p.finish())

# 5. Dealer
p = Page("dealer", "05 經銷商", "經銷商｜自己的門市", "桌機：自己的 PSI　　手機：自己的實銷與陳列")
shell(p, "經銷商", "自己的經銷商", [("我的資料", ["PSI 月報"])],
      "我的 PSI 月報", "手機｜我的實銷與陳列")
desktop_tabs(p, ["PSI 月報"])
p.box(305, 325, 750, 54, "月份：2026-09　　門市：民生家電（固定）　　匯出 Excel", "#FFFFFF")
table(p, 305, 398, [275, 118, 118, 118, 121],
      ["商品", "期初", "進貨", "實銷", "期末"],
      [["冰箱 A 型號", "12", "5", "4", "13"],
       ["冰箱 B 型號", "8", "2", "3", "7"],
       ["洗衣機 C 型號", "4", "1", "2", "3"]], 56)
p.box(305, 661, 750, 112, "", PALE)
p.label(324, 677, 700, 75, "處所與業務篩選不顯示。\n資料固定為登入的經銷商；不能以網址或 API 參數切換至其他經銷商。", 13, INK)
phone_card(p, 254, "我的經銷商", "只顯示自己門市的資訊。")
phone_card(p, 362, "實銷與陳列", "查看自己門市的回報與商品資料。")
phone_card(p, 470, "回報明細", "依現有流程輸入／修改自己的回報。")
foot(p, ["桌機 Menu 僅有 PSI；任務、員工、匯入、Passkey 等均不顯示。",
         "經銷商 PSI 是新開放項目；後端仍需將結果限定為該經銷商。"],
     "PSI 匯出是否開放給經銷商，可由 Designer 獨立設定。")
pages.append(p.finish())

# 6. Designer
p = Page("designer", "06 Designer", "Designer｜權限與 Menu 設計", "只有指定 Designer 帳號可調整職級預設及個人例外")
shell(p, "Designer", "權限設定；業務資料另依授權", [
    ("權限設計", ["職級預設權限", "個人例外權限", "Menu 預覽", "異動紀錄"]),
], "權限設定中心", "手機｜Passkey 驗證", phone_allowed=False)
desktop_tabs(p, ["職級預設", "個人例外", "Menu 預覽"])
p.box(305, 321, 750, 50, "職級：經理 ▼　　功能分類：巡店任務 ▼　　搜尋權限", "#FFFFFF")
table(p, 305, 386, [305, 140, 150, 155],
      ["權限項目", "職級預設", "經理甲", "經理乙"],
      [["查看巡店任務", "✓ 允許", "沿用預設", "沿用預設"],
       ["查看任務照片", "✓ 允許", "沿用預設", "沿用預設"],
       ["建立任務", "— 禁止", "✓ 個別允許", "沿用預設"],
       ["修改任務", "— 禁止", "沿用預設", "沿用預設"],
       ["暫停／恢復任務", "— 禁止", "沿用預設", "沿用預設"],
       ["設定樣本照片", "— 禁止", "沿用預設", "沿用預設"]], 49)
p.box(305, 746, 750, 58, "先預覽受影響 Menu 與操作，再儲存權限變更。", PALE,
      PALE, 14, BLUE, True)
phone_card(p, 271, "掃碼登入／授權", "手機可提供 Passkey 驗證桌機。")
phone_card(p, 382, "權限編輯放在桌機", "避免在小螢幕上誤改大量設定。", AMBER)
phone_card(p, 493, "業務資料另行授權", "Designer 身分本身不預設取得全部業務資料。")
foot(p, ["Designer 可編輯職級預設、指定人的允許／禁止例外，並預覽對應 Menu。",
         "Menu 由實際可用權限產生；後端 API 同時檢查資料範圍與操作權限。",
         "管理無權授予 Designer，也無權修改本頁；變更應留下修改者、時間及前後內容。"],
     "Designer 帳號如何指定及是否兼任管理工作，可在實作前確認。")
pages.append(p.finish())

mxfile = ET.Element("mxfile", host="Electron", agent="Codex", compressed="false",
                    pages=str(len(pages)), version="24.7.17")
mxfile.extend(pages)
ET.indent(mxfile, space="  ")
ET.ElementTree(mxfile).write(OUT, encoding="utf-8", xml_declaration=True)
print(OUT)

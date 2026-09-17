# 三台電腦：清空測試資料與重新註冊 Passkey

本流程由使用者在各機器自行執行，不會自動備份。只清除指定 DB 的測試資料，保留資料表、欄位、索引、限制及 SQL Server 連線帳密。

## 檔案順序

| 順序 | 檔案 | 用途 |
| --- | --- | --- |
| 1 | `EraseDummy.sql` | 清空目前 LGSale 業務表、登入帳戶、Passkey 與邀請，包含庫存更正歷程 |
| 2 | `建立初始測試帳戶.sql` | 建立測試處所、一位初始員工、任職／處所歷史及可登入的 UserAccount |
| 3 | `產生初始Passkey註冊連結.sql` | 產生一次性、15 分鐘有效的註冊網址，不需先登入系統 |

這三份檔案都使用 `USE [LGSaleOut]`。每次執行前，在 SSMS 確認目前連線是要重置的那台 SQL Server；若資料庫名稱不同，先修改 USE。三台應先同步最新程式並套用 `TSQL資料/Migrations/20260916_權限與Menu.sql` 等尚未套用的 migration，不要重跑 CreateDB.sql 來清資料。

## 各機器操作

1. 停止該機器的 LGSale 應用程式，暫停測試操作。SQL Server 保持執行。
2. 在 SSMS 開啟並執行 `EraseDummy.sql`。結果會顯示每張表剩餘筆數，應全部為 0。
3. 開啟 `建立初始測試帳戶.sql`，可修改員工編號、姓名、到職日、處所及職級；預設為 `E0001／初始管理員／測試處所`。執行一次即可，不需要手動指定 ID。
4. 啟動該機器的 LGSale 與既有 Cloudflare Tunnel，確認手機能開啟本台的 HTTPS 登入頁。
5. 開啟 `產生初始Passkey註冊連結.sql`，員工編號須與上一步相同，`@Origin` 填入**這台電腦** `.env.local` 的 `LGSALEOUT_ORIGIN`。例如目前 LGDevA 使用 `https://lgdeva.superb-supplies.com.tw`；其他兩台請讀自己的設定，不套用此網址。
6. 執行 SQL，從 SSMS 結果格複製 `RegistrationUrl`，在 iPhone 的 Safari 開啟。連結包含註冊權限，只交給自己的測試手機，不貼入共用文件或 Git。
7. 輸入裝置名稱，例如「我的 iPhone」，按「建立 Passkey」，以 Face ID 完成 Apple 的儲存流程。私密金鑰由手機建立，SQL 不會直接建立 `PasskeyCredential`。
8. 按「前往登入」，以新 Passkey 登入員工入口。桌機登入可使用頁面上的手機掃碼授權。

清空後第一個**成功使用員工 Passkey 登入**的帳號會自動成為 Designer。這個身分與職級分開保存，不會因姓名改變而轉移。請先用預定的 Designer 帳號（目前為王正文）完成首次登入，再讓其他員工登入。Designer 包含「管理」的全部生效權限與全體經銷商資料範圍，且可進入「權限與 Menu」設定職級預設及個別帳號例外；一般「管理」不能進入此頁。重置腳本會清除先前的 Designer 綁定、權限例外與異動紀錄。日後更換 Designer 可使用 `TSQL資料/轉移Designer.sql`，每台資料庫各自執行。

若邀請已超過 15 分鐘、已使用或被撤銷，只重跑第 3 份 SQL，使用新的網址。不要再次清資料或重建員工。

## 三機設定原則

| 機器 | SQL 連線 | 註冊網址來源 |
| --- | --- | --- |
| LGDevA | 該機 .env.local 的 DB_HOST／DB_PORT／DB_NAME | 該機 LGSALEOUT_ORIGIN |
| LGDevB | 該機 .env.local 的 DB_HOST／DB_PORT／DB_NAME | 該機 LGSALEOUT_ORIGIN |
| LGSalesOut | 該機 .env.local 的 DB_HOST／DB_PORT／DB_NAME | 該機 LGSALEOUT_ORIGIN |

RP_ID、ORIGIN 與 Cloudflare 網址必須是該環境已設定的對應值。可使用同一支 iPhone 在三個網站各註冊；不要共用另一台 DB 產生的邀請連結，也不要複製另一台 .env.local。

## 清除範圍與登入狀態

- 清空包含 Employee、OrganizationUnit、Dealer、Product、配對／異動歷程、任務／照片記錄、巡店、Sell in、期初庫存、排除規則、批次、更正歷程、UserAccount、PasskeyCredential 及邀請。
- 不刪除資料表，也不新增四個已取消的來源／陳列欄位。
- 不重設 IDENTITY 序號，避免重建帳戶沿用舊 UserAccountId，導致尚未到期的舊登入 cookie 對應新帳戶。序號沒有從 1 開始是正常現象；程式使用實際產生的 ID。
- 停止並重新啟動 LGSale 可清掉記憶體中的桌機授權申請；請在手機與桌機重新登入，不沿用舊頁面。
- SQL 不會刪除 iPhone「密碼」App 裡的 Passkey；手機上的舊項目由使用者自行刪除。也不刪除 Excel、上傳照片或 uploads 中的實體檔案。
- 初始員工的職級由 `建立初始測試帳戶.sql` 的 `@PositionLevel` 決定；Designer 是首次成功登入後附加的權限設定身分。

## 執行後核對

初始化完成且尚未註冊時，應有一位員工、一個帳戶、一筆員工職級歷史及一筆處所歷史；產生邀請後有一筆有效邀請。手機成功註冊後，PasskeyCredential 會新增一筆，邀請 UsedAt 會有值。

若 SQL 中途失敗，該檔案交易會回滾；先閱讀 SSMS 錯誤，不要直接停用外鍵重跑。

# LGSaleOut 資料庫摘要

> 更新日期：2026-08-09  
> 設計來源：`Codex筆記/LGSale_ERD_標準.drawio`  
> 用途：記錄目前開發環境的建庫、假資料及清除資料方式。

## 1. 檔案清單

| 檔案 | 用途 |
|---|---|
| `CreateDB.sql` | 刪除並重建 `LGSaleOut`，建立資料表、索引、限制條件及開發帳號。 |
| `DummyFile.sql` | 建立可供桌機 UI、巡店、庫存與任務流程測試的連貫假資料。 |
| `EraseDummy.sql` | 刪除全部業務資料並重設 Identity，保留資料庫結構與登入帳號。 |

## 2. CreateDB.sql 重點

- 資料庫名稱：`LGSaleOut`。
- 如果 `LGSaleOut` 已存在，會先：
  1. 設定為 `SINGLE_USER WITH ROLLBACK IMMEDIATE`。
  2. 刪除既有資料庫。
  3. 建立新的 `LGSaleOut`。
- 建立 SQL Server Login 與 Database User：`Tim`。
- 開發環境密碼：`561202`。
- `CHECK_POLICY` 與 `CHECK_EXPIRATION` 目前關閉。
- `Tim` 目前直接加入 `db_owner`。
- 正式上線前應更換密碼、重新評估密碼政策及最小權限設定。

### 2.1 資料表

目前依最新版 ERD 建立 21 張資料表：

#### 人員與組織

1. `Employee`
2. `EmployeePositionHistory`
3. `OrganizationUnit`
4. `EmployeeOrgAssignmentHistory`

#### 經銷商與負責關係

5. `Dealer`
6. `DealerLevelHistory`
7. `DealerAssignmentHistory`
8. `DealerTransferReview`

#### 統一登入與 Passkey

9. `UserAccount`
10. `PasskeyCredential`
11. `PasskeyRegistrationInvitation`

#### 商品、匯入與庫存

12. `Product`
13. `ImportBatch`
14. `MonthlyOpeningInventoryDetail`
15. `OpeningInventoryProductExclusion`
16. `SellInTransaction`

#### 巡店回報

17. `StoreVisit`
18. `StoreVisitProductDetail`

#### 公司任務與照片

19. `VisitTask`
20. `VisitTaskExecution`
21. `VisitTaskPhoto`

### 2.2 重要資料規則

- 員工職級、員工處所及經銷商負責關係均保留歷史期間。
- 同一時間只能有一筆有效的員工職級、員工處所及經銷商負責關係。
- 人員換處所不自動換線，改由 `DealerTransferReview` 建立逐家待確認事項；離職則先結束目前負責關係，再建立待移轉事項。
- 經銷商等級允許 `A`、`B`、`C`、`D`、`E`、`Z`。
- `UserAccount` 分為 `EMPLOYEE` 與 `DEALER`，只能對應其中一種身分。
- 期初庫存排除範圍分為：
  - `ALL`：適用全部經銷商，`DealerId` 必須為 `NULL`。
  - `DEALER`：只適用指定經銷商，`DealerId` 必填。
- `StoreVisit.RecordStatus` 使用 `ACTIVE` 或 `VOIDED`。
- `SellOutQuantity` 只能是 `NULL` 或 `1～10`。
- `DisplayQuantity` 只能是 `NULL` 或 `1～10`。
- `SellOutQuantity` 與 `SellOutDate` 必須同時有值或同時為 `NULL`。
- 任務截止日 `DueDate` 不得早於開始日 `ValidFrom`。
- 同一任務、同一家經銷商只能有一筆 `VisitTaskExecution`。
- `VisitTask.SampleTaskExecutionId` 必須指向同一任務下的執行紀錄。
- 一般任務照片可利用 `SampleTaskPhotoId` 對應核准樣本照片。

## 3. DummyFile.sql 重點

- 使用 `SET XACT_ABORT ON` 與 Transaction；發生錯誤時會整批回復。
- 為全部 21 張資料表建立測試資料。
- 如果主要資料表已有資料，會停止執行並提示先執行 `EraseDummy.sql`。
- 測試資料包含：
  - 台北、新竹及台中處所。
  - 管理員、業務、處長與離職人員。
  - 不同等級及停止經銷的經銷商。
  - 現行與歷史經銷商負責關係。
  - 員工及經銷商登入帳號、Passkey 與註冊邀請。
  - 商品、期初庫存、期初庫存排除規則及 Sell in。
  - 業務填寫、經銷商自行回報及作廢巡店紀錄。
  - 未開始、執行中及作廢任務。
  - 尚未回報、正常完成及不拍照附原因完成的任務執行。
  - 已核准樣本照片及一般照片對應樣本的情境。

## 4. EraseDummy.sql 重點

> **警告：目前版本不是只刪除具有特定假資料標記的資料，而是刪除全部業務資料。**

- 保留 `LGSaleOut` 資料庫、資料表、Constraint、Index、Login 與 User。
- 刪除前先解除以下參照：
  - `VisitTask.SampleTaskExecutionId`
  - `VisitTaskPhoto.SampleTaskPhotoId`
  - `ImportBatch.ReplacedBatchId`
- 再依外鍵順序，由子表到父表刪除所有資料。
- 不使用 `TRUNCATE TABLE`。
- 完成後使用 `DBCC CHECKIDENT`，將全部 Identity 種子重設為 0，下一筆資料會從 1 開始。
- 正式上線前，必須改為只刪除明確識別的測試資料，或完全移除這支清除腳本的正式環境執行權限。

## 5. 建議執行順序

第一次建立開發資料庫：

```text
1. CreateDB.sql
2. DummyFile.sql
```

清除後重新建立假資料：

```text
1. EraseDummy.sql
2. DummyFile.sql
```

完全重建資料庫：

```text
1. CreateDB.sql
2. DummyFile.sql
```

## 6. 執行注意事項

- `CreateDB.sql` 及 `EraseDummy.sql` 都屬於破壞性腳本，執行前必須確認目前連線的 SQL Server Instance。
- `CreateDB.sql` 需要具備建立、刪除資料庫及建立 Login 的系統管理權限。
- 建議使用 SSMS 依序開啟並執行，不要一次選取多支腳本混合執行。
- 目前三支 SQL 已完成檔案結構與 ERD 表名靜態核對，但尚未在本機 SQL Server 實際建立資料庫及寫入資料。

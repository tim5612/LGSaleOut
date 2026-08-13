# LGSale Passkey 啟用與正式機設定

## 測試機 iPhone 測試

測試機使用 `https://lgdeva.superb-supplies.com.tw`。先以系統管理員 PowerShell 停止占用 8097 的舊服務，再執行：

```powershell
powershell -ExecutionPolicy Bypass -File ".\正式機紀錄\啟動測試機Passkey.ps1" -EmployeeNo S0128
```

腳本只為目前程序設定測試 RP ID／Origin，不寫入正式機設定；它會輸出 15 分鐘有效的 iPhone 註冊網址並啟動測試 Waitress。

## 本機測試

1. 安裝套件：`.venv\Scripts\python.exe -m pip install -r requirements.txt`
2. 啟動：`.venv\Scripts\python.exe LGSale.py`（預設使用 8098，避免與既有 8097 正式服務衝突）
3. 為員工建立 15 分鐘有效的一次性邀請：
   `.venv\Scripts\python.exe LGSale.py invite employee <EmployeeNo>`
4. 為經銷商建立邀請：
   `.venv\Scripts\python.exe LGSale.py invite dealer <DealerCode>`
5. 用同一台電腦的瀏覽器開啟命令輸出的 `http://localhost:8098/register?...`。

業務登入入口為 `/login/employee`，經銷商登入入口為 `/login/dealer`。兩個入口會在後端核對 `UserAccount.AccountType`，不可交叉登入。

## 正式環境必要設定

```text
LGSALEOUT_RP_ID=lgdeva.superb-supplies.com.tw
LGSALEOUT_ORIGIN=https://lgdeva.superb-supplies.com.tw
LGSALEOUT_RP_NAME=LGSale
LGSALEOUT_SESSION_SECRET=<至少 32 bytes 的密碼學安全亂數>
```

`LGSALEOUT_RP_ID` 只填網域，不含協定或路徑；`LGSALEOUT_ORIGIN` 必須與使用者實際開啟的 HTTPS Origin 完全相同。正式環境不可使用 IP、`file://` 或 HTTP。

Passkey 的 Face ID、指紋、PIN 與裝置密碼只在裝置端使用；伺服器只保存 Credential ID、公鑰、計數器與裝置顯示名稱。

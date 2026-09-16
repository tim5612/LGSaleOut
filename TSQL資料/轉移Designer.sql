/* 在 SSMS 連到目標機器的 LGSaleOut 後執行。每台資料庫分別轉移。
   先備份資料庫，並把下方員工編號改成新 Designer 的員工編號。
   新帳號必須啟用且已有可用的 Passkey。此腳本不會修改職級。
   轉移完成後，舊 Designer 的權限立即失效，新 Designer 立即生效。
*/
USE [LGSaleOut];
GO

DECLARE @TargetEmployeeNo nvarchar(30) = N'請填入員工編號';
DECLARE @TargetAccountId bigint;

SET XACT_ABORT ON;
BEGIN TRY
    BEGIN TRANSACTION;

    -- 與首次登入自動認領使用相同的表鎖，避免同時產生兩位 Designer。
    DECLARE @ExistingCount int;
    SELECT @ExistingCount = COUNT(*)
      FROM dbo.PermissionDesigner WITH (TABLOCKX, HOLDLOCK);

    SELECT @TargetAccountId = ua.UserAccountId
      FROM dbo.Employee e
      JOIN dbo.UserAccount ua ON ua.EmployeeId = e.EmployeeId
     WHERE e.EmployeeNo = @TargetEmployeeNo
       AND e.TerminationDate IS NULL
       AND ua.AccountType = 'EMPLOYEE'
       AND ua.AccountStatus = 'ACTIVE'
       AND ua.IsLoginEnabled = 1
       AND EXISTS (
           SELECT 1 FROM dbo.PasskeyCredential pc
            WHERE pc.UserAccountId = ua.UserAccountId
              AND pc.RevokedAt IS NULL
       );

    IF @TargetAccountId IS NULL
        THROW 50001, N'找不到啟用中且已有可用 Passkey 的員工帳號；未轉移 Designer。', 1;

    DELETE FROM dbo.PermissionDesigner;
    INSERT INTO dbo.PermissionDesigner (UserAccountId) VALUES (@TargetAccountId);

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;

SELECT e.EmployeeNo, e.EmployeeName, ua.UserAccountId, pd.CreatedAt
  FROM dbo.PermissionDesigner pd
  JOIN dbo.UserAccount ua ON ua.UserAccountId = pd.UserAccountId
  JOIN dbo.Employee e ON e.EmployeeId = ua.EmployeeId;

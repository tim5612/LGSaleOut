/* SSMS 手動執行。不需先登入 LGSale。
   此檔可重跑：撤銷此帳戶尚未使用的舊邀請，重新產生 15 分鐘有效的新連結。
   不刪除既有 Passkey；清空測試資料後，Passkey 表應為空。
*/
USE [LGSaleOut];
GO
SET NOCOUNT ON;
SET XACT_ABORT ON;

DECLARE @EmployeeNo nvarchar(30) = N'E0001'; -- 與初始帳戶 SQL 相同
DECLARE @Origin varchar(500) = 'https://CHANGE_ME'; -- 本機 .env.local 的 LGSALEOUT_ORIGIN

IF CHARINDEX('CHANGE_ME',@Origin)>0 OR @Origin NOT LIKE 'https://%' OR CHARINDEX(' ',@Origin)>0
    THROW 51000, N'請把 @Origin 改成本台電腦 .env.local 的 LGSALEOUT_ORIGIN（完整 HTTPS 網址）。', 1;
WHILE RIGHT(@Origin,1)='/' SET @Origin=LEFT(@Origin,LEN(@Origin)-1);
IF LEN(@Origin)<=8 OR CHARINDEX('/',SUBSTRING(@Origin,9,500))>0 OR CHARINDEX('?',@Origin)>0 OR CHARINDEX('#',@Origin)>0
    THROW 51000, N'@Origin 只填 HTTPS 網站來源，不要加 /register、路徑或查詢參數。', 1;

BEGIN TRY
    BEGIN TRANSACTION;
    DECLARE @EmployeeId bigint,@UserAccountId bigint;
    SELECT @EmployeeId=e.EmployeeId,@UserAccountId=a.UserAccountId
    FROM dbo.Employee e JOIN dbo.UserAccount a ON a.EmployeeId=e.EmployeeId AND a.AccountType='EMPLOYEE'
    WHERE e.EmployeeNo=@EmployeeNo AND e.TerminationDate IS NULL AND a.IsLoginEnabled=1 AND a.AccountStatus='ACTIVE';
    IF @UserAccountId IS NULL
        THROW 51000, N'找不到可登入的初始員工帳戶。請先建立帳戶，並確認員工編號。', 1;

    -- 十六進位 ASCII token；varchar 的 SHA2_256 與 Python token.encode() 一致。
    -- 不可改成 nvarchar token，否則 HASHBYTES 使用 UTF-16，網站無法驗證。
    DECLARE @Token varchar(64)=CONVERT(varchar(64),CRYPT_GEN_RANDOM(32),2);
    DECLARE @Now datetime2(0)=SYSDATETIME();
    DECLARE @ExpiresAt datetime2(0)=DATEADD(minute,15,@Now);
    UPDATE dbo.PasskeyRegistrationInvitation SET RevokedAt=@Now
    WHERE UserAccountId=@UserAccountId AND UsedAt IS NULL AND RevokedAt IS NULL;
    INSERT dbo.PasskeyRegistrationInvitation(UserAccountId,TokenHash,ExpiresAt,CreatedAt,CreatedByEmployeeId)
    VALUES(@UserAccountId,HASHBYTES('SHA2_256',@Token),@ExpiresAt,@Now,@EmployeeId);
    COMMIT TRANSACTION;

    SELECT DB_NAME() AS DatabaseName,@EmployeeNo AS EmployeeNo,@ExpiresAt AS ExpiresAt_ServerLocalTime,
           @Origin+'/register?token='+@Token AS RegistrationUrl,
           N'用 iPhone Safari 在 15 分鐘內開啟 RegistrationUrl，按「建立 Passkey」。' AS NextStep;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO

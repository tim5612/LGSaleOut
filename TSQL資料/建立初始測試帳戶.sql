/* SSMS 手動執行。先完成 EraseDummy.sql；只建立一位初始員工與 Designer 帳戶。
   保留資料表結構，未建立 Passkey；下一步執行「產生初始Passkey註冊連結.sql」。
   在三台電腦各自連線正確的 SQL Server／資料庫後執行。
*/
USE [LGSaleOut];
GO
SET NOCOUNT ON;
SET XACT_ABORT ON;

-- 可修改：每台可以使用相同員工編號，但資料各自獨立。
DECLARE @EmployeeNo nvarchar(30) = N'T0001';
DECLARE @EmployeeName nvarchar(100) = N'王正文';
DECLARE @HireDate date = '2026-01-01';
DECLARE @OrgUnitCode varchar(30) = 'TEST';
DECLARE @OrgUnitName nvarchar(100) = N'內湖';
DECLARE @PositionLevel varchar(30) = 'MANAGER'; -- 員工職級：SALES／DIRECTOR／MANAGER／ADMIN；Designer 另由 PermissionDesigner 指定

BEGIN TRY
    BEGIN TRANSACTION;
    IF EXISTS (SELECT 1 FROM dbo.Employee)
        THROW 51000, N'員工資料表並非空白。不要重複初始化；只要重新產生連結，請執行另一份註冊連結 SQL。', 1;
    IF NULLIF(LTRIM(RTRIM(@EmployeeNo)),N'') IS NULL OR NULLIF(LTRIM(RTRIM(@EmployeeName)),N'') IS NULL
        THROW 51000, N'請填寫員工編號與姓名。', 1;

    DECLARE @EmployeeId bigint, @OrgUnitId bigint;
    SELECT @OrgUnitId=OrgUnitId FROM dbo.OrganizationUnit WHERE OrgUnitCode=@OrgUnitCode;
    IF @OrgUnitId IS NULL
    BEGIN
        INSERT dbo.OrganizationUnit(OrgUnitCode,OrgUnitName,IsActive)
        VALUES(@OrgUnitCode,@OrgUnitName,1);
        SET @OrgUnitId=CONVERT(bigint,SCOPE_IDENTITY());
    END;
    IF NOT EXISTS(SELECT 1 FROM dbo.OrganizationUnit WHERE OrgUnitId=@OrgUnitId AND IsActive=1)
        THROW 51000, N'指定處所已停用，請確認設定。', 1;

    INSERT dbo.Employee(EmployeeNo,EmployeeName,HireDate) VALUES(@EmployeeNo,@EmployeeName,@HireDate);
    SET @EmployeeId=CONVERT(bigint,SCOPE_IDENTITY());
    INSERT dbo.EmployeePositionHistory(EmployeeId,PositionLevel,StartDateTime,ChangeReason,CreatedByEmployeeId)
    VALUES(@EmployeeId,@PositionLevel,CONVERT(datetime2(0),@HireDate),N'測試資料重置後初始化',@EmployeeId);
    INSERT dbo.EmployeeOrgAssignmentHistory(EmployeeId,OrgUnitId,StartDateTime,ChangeReason,CreatedByEmployeeId)
    VALUES(@EmployeeId,@OrgUnitId,CONVERT(datetime2(0),@HireDate),N'測試資料重置後初始化',@EmployeeId);
    INSERT dbo.UserAccount(AccountType,EmployeeId,IsLoginEnabled,AccountStatus)
    VALUES('EMPLOYEE',@EmployeeId,1,'ACTIVE');
    DECLARE @UserAccountId bigint=CONVERT(bigint,SCOPE_IDENTITY());
    IF OBJECT_ID(N'dbo.PermissionDesigner',N'U') IS NULL
        THROW 51000, N'尚未建立 PermissionDesigner；請先套用權限 Migration。', 1;
    EXEC sys.sp_executesql N'INSERT dbo.PermissionDesigner(UserAccountId) VALUES(@Id)',
        N'@Id bigint', @Id=@UserAccountId;
    DECLARE @IsDesigner bit=0;
    EXEC sys.sp_executesql
        N'SELECT @Flag=CAST(CASE WHEN EXISTS(SELECT 1 FROM dbo.PermissionDesigner WHERE UserAccountId=@Id) THEN 1 ELSE 0 END AS bit)',
        N'@Id bigint, @Flag bit OUTPUT', @Id=@UserAccountId, @Flag=@IsDesigner OUTPUT;
    IF @IsDesigner<>1
        THROW 51000, N'初始帳戶未取得 Designer 身分，已取消本次初始化。', 1;
    COMMIT TRANSACTION;

    SELECT DB_NAME() AS DatabaseName, @EmployeeNo AS EmployeeNo, @EmployeeName AS EmployeeName,
           @EmployeeId AS EmployeeId, ua.UserAccountId,
           @IsDesigner AS IsDesigner,
           @PositionLevel AS PositionLevel,
           N'初始 Designer 帳戶已建立；請執行「產生初始Passkey註冊連結.sql」。' AS NextStep
    FROM dbo.UserAccount AS ua
    WHERE ua.EmployeeId=@EmployeeId;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO

/* SSMS 手動執行：清空 LGSaleOut 全部測試資料，不備份、不刪除表結構。
   執行前先停止本台 LGSale；不重設 IDENTITY，避免舊登入 cookie 對應新帳戶。
   下一步：建立初始測試帳戶.sql → 產生初始Passkey註冊連結.sql。 */

USE [LGSaleOut];
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    /* Break the circular and self-referencing relationships first. */
    UPDATE dbo.VisitTask
       SET SampleTaskExecutionId = NULL,
           SampleApprovedByEmployeeId = NULL,
           SampleApprovedAt = NULL;

    UPDATE dbo.VisitTaskPhoto SET SampleTaskPhotoId = NULL;
    UPDATE dbo.ImportBatch SET ReplacedBatchId = NULL;

    /* Child tables to parent tables. */
    DELETE FROM dbo.VisitTaskPhoto;
    DELETE FROM dbo.VisitTaskExecution;
    DELETE FROM dbo.VisitTask;

    DELETE FROM dbo.StoreVisitProductDetail;
    DELETE FROM dbo.StoreVisit;

    DELETE FROM dbo.SellInTransaction;
    IF OBJECT_ID(N'dbo.OpeningInventoryCorrection',N'U') IS NOT NULL
        EXEC(N'DELETE FROM dbo.OpeningInventoryCorrection;');
    DELETE FROM dbo.MonthlyOpeningInventoryDetail;
    DELETE FROM dbo.OpeningInventoryProductExclusion;

    DELETE FROM dbo.PasskeyRegistrationInvitation;
    DELETE FROM dbo.PasskeyCredential;
    DELETE FROM dbo.UserAccount;

    DELETE FROM dbo.ImportBatch;
    DELETE FROM dbo.DealerTransferReview;
    DELETE FROM dbo.DealerAssignmentHistory;
    DELETE FROM dbo.DealerLevelHistory;
    DELETE FROM dbo.EmployeeOrgAssignmentHistory;
    DELETE FROM dbo.EmployeePositionHistory;

    DELETE FROM dbo.Product;
    DELETE FROM dbo.Dealer;
    DELETE FROM dbo.OrganizationUnit;
    DELETE FROM dbo.Employee;


    COMMIT TRANSACTION;

    SELECT N'全部測試資料已清空；表結構及 IDENTITY 序號保留。請繼續建立初始測試帳戶。' AS Result;
    SELECT N'Employee' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.Employee
    UNION ALL
    SELECT N'OrganizationUnit' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.OrganizationUnit
    UNION ALL
    SELECT N'EmployeePositionHistory' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.EmployeePositionHistory
    UNION ALL
    SELECT N'EmployeeOrgAssignmentHistory' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.EmployeeOrgAssignmentHistory
    UNION ALL
    SELECT N'Dealer' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.Dealer
    UNION ALL
    SELECT N'DealerLevelHistory' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.DealerLevelHistory
    UNION ALL
    SELECT N'DealerAssignmentHistory' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.DealerAssignmentHistory
    UNION ALL
    SELECT N'DealerTransferReview' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.DealerTransferReview
    UNION ALL
    SELECT N'UserAccount' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.UserAccount
    UNION ALL
    SELECT N'PasskeyCredential' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.PasskeyCredential
    UNION ALL
    SELECT N'PasskeyRegistrationInvitation' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.PasskeyRegistrationInvitation
    UNION ALL
    SELECT N'Product' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.Product
    UNION ALL
    SELECT N'ImportBatch' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.ImportBatch
    UNION ALL
    SELECT N'MonthlyOpeningInventoryDetail' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.MonthlyOpeningInventoryDetail
    UNION ALL
    SELECT N'OpeningInventoryProductExclusion' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.OpeningInventoryProductExclusion
    UNION ALL
    SELECT N'SellInTransaction' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.SellInTransaction
    UNION ALL
    SELECT N'StoreVisit' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.StoreVisit
    UNION ALL
    SELECT N'StoreVisitProductDetail' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.StoreVisitProductDetail
    UNION ALL
    SELECT N'VisitTask' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.VisitTask
    UNION ALL
    SELECT N'VisitTaskExecution' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.VisitTaskExecution
    UNION ALL
    SELECT N'VisitTaskPhoto' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.VisitTaskPhoto;
    IF OBJECT_ID(N'dbo.OpeningInventoryCorrection',N'U') IS NOT NULL
        EXEC(N'SELECT N''OpeningInventoryCorrection'' AS TableName, COUNT_BIG(*) AS RemainingRows FROM dbo.OpeningInventoryCorrection;');
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO

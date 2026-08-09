/*
    DANGER: This development script deletes ALL rows from every LGSaleOut
    business table, then resets all IDENTITY seeds. Tables and login/user remain.
*/

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
    DELETE FROM dbo.MonthlyOpeningInventoryDetail;
    DELETE FROM dbo.OpeningInventoryProductExclusion;

    DELETE FROM dbo.PasskeyRegistrationInvitation;
    DELETE FROM dbo.PasskeyCredential;
    DELETE FROM dbo.UserAccount;

    DELETE FROM dbo.ImportBatch;
    DELETE FROM dbo.DealerAssignmentHistory;
    DELETE FROM dbo.DealerLevelHistory;
    DELETE FROM dbo.EmployeeOrgAssignmentHistory;
    DELETE FROM dbo.EmployeePositionHistory;

    DELETE FROM dbo.Product;
    DELETE FROM dbo.Dealer;
    DELETE FROM dbo.OrganizationUnit;
    DELETE FROM dbo.Employee;

    DBCC CHECKIDENT ('dbo.VisitTaskPhoto', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.VisitTaskExecution', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.VisitTask', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.StoreVisitProductDetail', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.StoreVisit', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.SellInTransaction', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.MonthlyOpeningInventoryDetail', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.OpeningInventoryProductExclusion', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.PasskeyRegistrationInvitation', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.PasskeyCredential', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.UserAccount', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.ImportBatch', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.DealerAssignmentHistory', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.DealerLevelHistory', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.EmployeeOrgAssignmentHistory', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.EmployeePositionHistory', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.Product', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.Dealer', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.OrganizationUnit', RESEED, 0) WITH NO_INFOMSGS;
    DBCC CHECKIDENT ('dbo.Employee', RESEED, 0) WITH NO_INFOMSGS;

    COMMIT TRANSACTION;

    SELECT N'All LGSaleOut business data deleted; identity seeds reset.' AS Result;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO

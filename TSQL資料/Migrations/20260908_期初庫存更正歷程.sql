SET XACT_ABORT ON;
BEGIN TRANSACTION;
IF OBJECT_ID('dbo.OpeningInventoryCorrection','U') IS NULL
CREATE TABLE dbo.OpeningInventoryCorrection (
    CorrectionId bigint IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ImportBatchId bigint NOT NULL REFERENCES dbo.ImportBatch(ImportBatchId),
    OpeningInventoryDetailId bigint NOT NULL REFERENCES dbo.MonthlyOpeningInventoryDetail(OpeningInventoryDetailId),
    SourceRowNumber int NOT NULL,
    PreviousQuantity int NOT NULL,
    NewQuantity int NOT NULL,
    CreatedAt datetime2(0) NOT NULL DEFAULT sysdatetime(),
    CONSTRAINT UQ_OpeningInventoryCorrection UNIQUE(ImportBatchId,OpeningInventoryDetailId)
);
COMMIT TRANSACTION;

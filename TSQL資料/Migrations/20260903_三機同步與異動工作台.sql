USE LGSaleOut;
GO

SET XACT_ABORT ON;
GO

BEGIN TRY
    BEGIN TRANSACTION;

    IF COL_LENGTH('dbo.Dealer', 'TaxId') IS NULL
        ALTER TABLE dbo.Dealer ADD TaxId varchar(20) NULL;

    IF COL_LENGTH('dbo.Dealer', 'Area') IS NULL
        ALTER TABLE dbo.Dealer ADD Area nvarchar(100) NULL;

    IF COL_LENGTH('dbo.Dealer', 'DealerCondition') IS NULL
        ALTER TABLE dbo.Dealer ADD DealerCondition varchar(20) NOT NULL
            CONSTRAINT DF_Dealer_Condition DEFAULT ('ACTIVE') WITH VALUES;

    IF EXISTS
    (
        SELECT 1 FROM sys.columns
         WHERE object_id = OBJECT_ID('dbo.Dealer')
           AND name = 'DealerCondition'
           AND is_nullable = 1
    )
    BEGIN
        UPDATE dbo.Dealer SET DealerCondition = 'ACTIVE' WHERE DealerCondition IS NULL;
        ALTER TABLE dbo.Dealer ALTER COLUMN DealerCondition varchar(20) NOT NULL;
    END;

    IF NOT EXISTS
    (
        SELECT 1
          FROM sys.default_constraints dc
          JOIN sys.columns c ON c.object_id=dc.parent_object_id AND c.column_id=dc.parent_column_id
         WHERE dc.parent_object_id=OBJECT_ID('dbo.Dealer') AND c.name='DealerCondition'
    )
        ALTER TABLE dbo.Dealer ADD CONSTRAINT DF_Dealer_Condition DEFAULT ('ACTIVE') FOR DealerCondition;

    IF NOT EXISTS
    (
        SELECT 1 FROM sys.check_constraints
         WHERE parent_object_id = OBJECT_ID('dbo.Dealer')
           AND name = 'CK_Dealer_Condition'
    )
        ALTER TABLE dbo.Dealer ADD CONSTRAINT CK_Dealer_Condition
            CHECK (DealerCondition IN ('ACTIVE','PENDING','CLOSED'));

    IF OBJECT_ID('dbo.DealerTransferReview', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.DealerTransferReview
        (
            DealerTransferReviewId  bigint IDENTITY(1,1) NOT NULL,
            DealerId                bigint NOT NULL,
            SourceDealerAssignmentId bigint NULL,
            SourceEmployeeId        bigint NULL,
            TriggerType             varchar(30) NOT NULL,
            FromOrgUnitId           bigint NULL,
            ToOrgUnitId             bigint NULL,
            TriggeredAt             datetime2(0) NOT NULL,
            ReviewStatus            varchar(20) NOT NULL CONSTRAINT DF_DealerTransferReview_Status DEFAULT ('OPEN'),
            ResolvedEmployeeId      bigint NULL,
            ResolvedAt              datetime2(0) NULL,
            ResolvedByEmployeeId    bigint NULL,
            ResolutionNote          nvarchar(500) NULL,
            CreatedAt               datetime2(0) NOT NULL CONSTRAINT DF_DealerTransferReview_CreatedAt DEFAULT (sysdatetime()),
            CONSTRAINT PK_DealerTransferReview PRIMARY KEY CLUSTERED (DealerTransferReviewId),
            CONSTRAINT FK_DealerTransferReview_Dealer FOREIGN KEY (DealerId) REFERENCES dbo.Dealer (DealerId),
            CONSTRAINT FK_DealerTransferReview_SourceAssignment FOREIGN KEY (SourceDealerAssignmentId) REFERENCES dbo.DealerAssignmentHistory (DealerAssignmentId),
            CONSTRAINT FK_DealerTransferReview_SourceEmployee FOREIGN KEY (SourceEmployeeId) REFERENCES dbo.Employee (EmployeeId),
            CONSTRAINT FK_DealerTransferReview_FromOrg FOREIGN KEY (FromOrgUnitId) REFERENCES dbo.OrganizationUnit (OrgUnitId),
            CONSTRAINT FK_DealerTransferReview_ToOrg FOREIGN KEY (ToOrgUnitId) REFERENCES dbo.OrganizationUnit (OrgUnitId),
            CONSTRAINT FK_DealerTransferReview_ResolvedEmployee FOREIGN KEY (ResolvedEmployeeId) REFERENCES dbo.Employee (EmployeeId),
            CONSTRAINT FK_DealerTransferReview_ResolvedBy FOREIGN KEY (ResolvedByEmployeeId) REFERENCES dbo.Employee (EmployeeId),
            CONSTRAINT CK_DealerTransferReview_Trigger CHECK (TriggerType IN ('ORG_MOVE','TERMINATION','MANUAL_UNASSIGNED')),
            CONSTRAINT CK_DealerTransferReview_Status CHECK (ReviewStatus IN ('OPEN','RETAINED','TRANSFERRED'))
        );
    END;

    IF NOT EXISTS
    (
        SELECT 1 FROM sys.indexes
         WHERE object_id = OBJECT_ID('dbo.DealerTransferReview')
           AND name = 'UX_DealerTransferReview_Open'
    )
        CREATE UNIQUE INDEX UX_DealerTransferReview_Open
            ON dbo.DealerTransferReview (DealerId)
            WHERE ReviewStatus = 'OPEN';

    IF EXISTS
    (
        SELECT 1 FROM dbo.StoreVisitProductDetail
         WHERE DisplayQuantity IS NOT NULL AND DisplayQuantity NOT BETWEEN 1 AND 10
    )
        THROW 50030, N'既有陳列數量含有 1～10 以外的值；請先確認資料後再執行 Migration。', 1;

    IF EXISTS
    (
        SELECT 1 FROM sys.check_constraints
         WHERE parent_object_id = OBJECT_ID('dbo.StoreVisitProductDetail')
           AND name = 'CK_StoreVisitProductDetail_DisplayQuantity'
    )
        ALTER TABLE dbo.StoreVisitProductDetail
            DROP CONSTRAINT CK_StoreVisitProductDetail_DisplayQuantity;

    ALTER TABLE dbo.StoreVisitProductDetail WITH CHECK
        ADD CONSTRAINT CK_StoreVisitProductDetail_DisplayQuantity
        CHECK (DisplayQuantity IS NULL OR DisplayQuantity BETWEEN 1 AND 10);

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO

SELECT
    DB_NAME() AS DatabaseName,
    COL_LENGTH('dbo.Dealer', 'TaxId') AS DealerTaxIdColumn,
    COL_LENGTH('dbo.Dealer', 'Area') AS DealerAreaColumn,
    COL_LENGTH('dbo.Dealer', 'DealerCondition') AS DealerConditionColumn,
    OBJECT_ID('dbo.DealerTransferReview', 'U') AS DealerTransferReviewObjectId;
GO

/*
    LGSaleOut - SQL Server database creation script
    Source: Codex筆記/LGSale_ERD_標準.drawio
    Target: Microsoft SQL Server 2016+

    Notes:
    1. The ERD specifies logical string types but not every length. Practical lengths
       are assigned here and can be adjusted before production deployment.
    2. The script drops the existing LGSaleOut database and recreates it.
    3. Run this script in SSMS with an account allowed to CREATE DATABASE.
*/

USE [master];
GO

IF DB_ID(N'LGSaleOut') IS NOT NULL
BEGIN
    ALTER DATABASE [LGSaleOut]
        SET SINGLE_USER
        WITH ROLLBACK IMMEDIATE;

    DROP DATABASE [LGSaleOut];
END;
GO

CREATE DATABASE [LGSaleOut];
GO

USE [LGSaleOut];
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET CONCAT_NULL_YIELDS_NULL ON;
GO

/* =========================================================
   1. Organization and employee master data
   ========================================================= */

CREATE TABLE dbo.Employee
(
    EmployeeId       bigint IDENTITY(1,1) NOT NULL,
    EmployeeNo       nvarchar(30) NOT NULL,
    EmployeeName     nvarchar(100) NOT NULL,
    HireDate         date NOT NULL,
    TerminationDate  date NULL,

    CONSTRAINT PK_Employee PRIMARY KEY CLUSTERED (EmployeeId),
    CONSTRAINT UQ_Employee_EmployeeNo UNIQUE (EmployeeNo),
    CONSTRAINT CK_Employee_EmploymentDate
        CHECK (TerminationDate IS NULL OR TerminationDate >= HireDate)
);
GO

CREATE TABLE dbo.OrganizationUnit
(
    OrgUnitId    bigint IDENTITY(1,1) NOT NULL,
    OrgUnitCode  varchar(30) NOT NULL,
    OrgUnitName  nvarchar(100) NOT NULL,
    IsActive     bit NOT NULL
        CONSTRAINT DF_OrganizationUnit_IsActive DEFAULT (1),

    CONSTRAINT PK_OrganizationUnit PRIMARY KEY CLUSTERED (OrgUnitId),
    CONSTRAINT UQ_OrganizationUnit_OrgUnitCode UNIQUE (OrgUnitCode)
);
GO

CREATE TABLE dbo.EmployeePositionHistory
(
    EmployeePositionHistoryId  bigint IDENTITY(1,1) NOT NULL,
    EmployeeId                 bigint NOT NULL,
    PositionLevel              varchar(30) NOT NULL,
    StartDateTime              datetime2(0) NOT NULL,
    EndDateTime                datetime2(0) NULL,
    ChangeReason               nvarchar(500) NOT NULL,
    CreatedAt                  datetime2(0) NOT NULL
        CONSTRAINT DF_EmployeePositionHistory_CreatedAt DEFAULT (sysdatetime()),
    CreatedByEmployeeId        bigint NOT NULL,

    CONSTRAINT PK_EmployeePositionHistory
        PRIMARY KEY CLUSTERED (EmployeePositionHistoryId),
    CONSTRAINT FK_EmployeePositionHistory_Employee
        FOREIGN KEY (EmployeeId) REFERENCES dbo.Employee (EmployeeId),
    CONSTRAINT FK_EmployeePositionHistory_CreatedByEmployee
        FOREIGN KEY (CreatedByEmployeeId) REFERENCES dbo.Employee (EmployeeId),
    CONSTRAINT CK_EmployeePositionHistory_Period
        CHECK (EndDateTime IS NULL OR EndDateTime > StartDateTime)
);
GO

CREATE UNIQUE INDEX UX_EmployeePositionHistory_Current
    ON dbo.EmployeePositionHistory (EmployeeId)
    WHERE EndDateTime IS NULL;
GO

CREATE INDEX IX_EmployeePositionHistory_EmployeePeriod
    ON dbo.EmployeePositionHistory (EmployeeId, StartDateTime, EndDateTime);
GO

CREATE TABLE dbo.EmployeeOrgAssignmentHistory
(
    EmployeeOrgAssignmentId  bigint IDENTITY(1,1) NOT NULL,
    EmployeeId               bigint NOT NULL,
    OrgUnitId                bigint NOT NULL,
    StartDateTime            datetime2(0) NOT NULL,
    EndDateTime              datetime2(0) NULL,
    ChangeReason             nvarchar(500) NOT NULL,
    CreatedAt                datetime2(0) NOT NULL
        CONSTRAINT DF_EmployeeOrgAssignmentHistory_CreatedAt DEFAULT (sysdatetime()),
    CreatedByEmployeeId      bigint NOT NULL,

    CONSTRAINT PK_EmployeeOrgAssignmentHistory
        PRIMARY KEY CLUSTERED (EmployeeOrgAssignmentId),
    CONSTRAINT FK_EmployeeOrgAssignmentHistory_Employee
        FOREIGN KEY (EmployeeId) REFERENCES dbo.Employee (EmployeeId),
    CONSTRAINT FK_EmployeeOrgAssignmentHistory_OrganizationUnit
        FOREIGN KEY (OrgUnitId) REFERENCES dbo.OrganizationUnit (OrgUnitId),
    CONSTRAINT FK_EmployeeOrgAssignmentHistory_CreatedByEmployee
        FOREIGN KEY (CreatedByEmployeeId) REFERENCES dbo.Employee (EmployeeId),
    CONSTRAINT CK_EmployeeOrgAssignmentHistory_Period
        CHECK (EndDateTime IS NULL OR EndDateTime > StartDateTime)
);
GO

CREATE UNIQUE INDEX UX_EmployeeOrgAssignmentHistory_Current
    ON dbo.EmployeeOrgAssignmentHistory (EmployeeId)
    WHERE EndDateTime IS NULL;
GO

CREATE INDEX IX_EmployeeOrgAssignmentHistory_EmployeePeriod
    ON dbo.EmployeeOrgAssignmentHistory (EmployeeId, StartDateTime, EndDateTime);
GO

/* =========================================================
   2. Dealer master data and assignment history
   ========================================================= */

CREATE TABLE dbo.Dealer
(
    DealerId    bigint IDENTITY(1,1) NOT NULL,
    DealerCode  varchar(30) NOT NULL,
    DealerName  nvarchar(150) NOT NULL,
    TaxId       varchar(20) NULL,
    Area        nvarchar(100) NULL,
    DealerCondition varchar(20) NOT NULL
        CONSTRAINT DF_Dealer_Condition DEFAULT ('ACTIVE'),
    CreatedAt   datetime2(0) NOT NULL
        CONSTRAINT DF_Dealer_CreatedAt DEFAULT (sysdatetime()),

    CONSTRAINT PK_Dealer PRIMARY KEY CLUSTERED (DealerId),
    CONSTRAINT UQ_Dealer_DealerCode UNIQUE (DealerCode),
    CONSTRAINT CK_Dealer_Condition
        CHECK (DealerCondition IN ('ACTIVE','PENDING','CLOSED'))
);
GO

CREATE TABLE dbo.DealerLevelHistory
(
    DealerLevelHistoryId  bigint IDENTITY(1,1) NOT NULL,
    DealerId              bigint NOT NULL,
    DealerStatus          char(1) NOT NULL,
    StartDateTime         datetime2(0) NOT NULL,
    EndDateTime           datetime2(0) NULL,
    ChangeReason          varchar(max) NULL,
    CreatedAt             datetime2(0) NOT NULL
        CONSTRAINT DF_DealerLevelHistory_CreatedAt DEFAULT (sysdatetime()),

    CONSTRAINT PK_DealerLevelHistory
        PRIMARY KEY CLUSTERED (DealerLevelHistoryId),
    CONSTRAINT FK_DealerLevelHistory_Dealer
        FOREIGN KEY (DealerId) REFERENCES dbo.Dealer (DealerId),
    CONSTRAINT CK_DealerLevelHistory_Status
        CHECK (DealerStatus IN ('A','B','C','D','E','Z')),
    CONSTRAINT CK_DealerLevelHistory_Period
        CHECK (EndDateTime IS NULL OR EndDateTime > StartDateTime)
);
GO

CREATE UNIQUE INDEX UX_DealerLevelHistory_Current
    ON dbo.DealerLevelHistory (DealerId)
    WHERE EndDateTime IS NULL;
GO

CREATE INDEX IX_DealerLevelHistory_DealerPeriod
    ON dbo.DealerLevelHistory (DealerId, StartDateTime, EndDateTime);
GO

CREATE TABLE dbo.DealerAssignmentHistory
(
    DealerAssignmentId  bigint IDENTITY(1,1) NOT NULL,
    DealerId            bigint NOT NULL,
    EmployeeId          bigint NOT NULL,
    StartDateTime       datetime2(0) NOT NULL,
    EndDateTime         datetime2(0) NULL,
    ChangeReason        nvarchar(500) NOT NULL,
    CreatedAt           datetime2(0) NOT NULL
        CONSTRAINT DF_DealerAssignmentHistory_CreatedAt DEFAULT (sysdatetime()),
    CreatedByEmployeeId bigint NOT NULL,

    CONSTRAINT PK_DealerAssignmentHistory
        PRIMARY KEY CLUSTERED (DealerAssignmentId),
    CONSTRAINT FK_DealerAssignmentHistory_Dealer
        FOREIGN KEY (DealerId) REFERENCES dbo.Dealer (DealerId),
    CONSTRAINT FK_DealerAssignmentHistory_Employee
        FOREIGN KEY (EmployeeId) REFERENCES dbo.Employee (EmployeeId),
    CONSTRAINT FK_DealerAssignmentHistory_CreatedByEmployee
        FOREIGN KEY (CreatedByEmployeeId) REFERENCES dbo.Employee (EmployeeId),
    CONSTRAINT CK_DealerAssignmentHistory_Period
        CHECK (EndDateTime IS NULL OR EndDateTime > StartDateTime)
);
GO

CREATE UNIQUE INDEX UX_DealerAssignmentHistory_Current
    ON dbo.DealerAssignmentHistory (DealerId)
    WHERE EndDateTime IS NULL;
GO

CREATE INDEX IX_DealerAssignmentHistory_DealerPeriod
    ON dbo.DealerAssignmentHistory (DealerId, StartDateTime, EndDateTime);
GO

CREATE TABLE dbo.DealerTransferReview
(
    DealerTransferReviewId bigint IDENTITY(1,1) NOT NULL,
    DealerId                bigint NOT NULL,
    SourceDealerAssignmentId bigint NULL,
    SourceEmployeeId        bigint NULL,
    TriggerType             varchar(30) NOT NULL,
    FromOrgUnitId           bigint NULL,
    ToOrgUnitId             bigint NULL,
    TriggeredAt             datetime2(0) NOT NULL,
    ReviewStatus            varchar(20) NOT NULL DEFAULT ('OPEN'),
    ResolvedEmployeeId      bigint NULL,
    ResolvedAt              datetime2(0) NULL,
    ResolvedByEmployeeId    bigint NULL,
    ResolutionNote          nvarchar(500) NULL,
    CreatedAt               datetime2(0) NOT NULL DEFAULT (sysdatetime()),
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
GO

CREATE UNIQUE INDEX UX_DealerTransferReview_Open
    ON dbo.DealerTransferReview (DealerId)
    WHERE ReviewStatus = 'OPEN';
GO

/* =========================================================
   3. User accounts and passkeys
   ========================================================= */

CREATE TABLE dbo.UserAccount
(
    UserAccountId  bigint IDENTITY(1,1) NOT NULL,
    AccountType    varchar(20) NOT NULL,
    EmployeeId     bigint NULL,
    DealerId       bigint NULL,
    IsLoginEnabled bit NOT NULL
        CONSTRAINT DF_UserAccount_IsLoginEnabled DEFAULT (1),
    AccountStatus  varchar(20) NOT NULL
        CONSTRAINT DF_UserAccount_AccountStatus DEFAULT ('ACTIVE'),
    LastLoginAt    datetime2(0) NULL,
    CreatedAt      datetime2(0) NOT NULL
        CONSTRAINT DF_UserAccount_CreatedAt DEFAULT (sysdatetime()),

    CONSTRAINT PK_UserAccount PRIMARY KEY CLUSTERED (UserAccountId),
    CONSTRAINT FK_UserAccount_Employee
        FOREIGN KEY (EmployeeId) REFERENCES dbo.Employee (EmployeeId),
    CONSTRAINT FK_UserAccount_Dealer
        FOREIGN KEY (DealerId) REFERENCES dbo.Dealer (DealerId),
    CONSTRAINT CK_UserAccount_AccountType
        CHECK (AccountType IN ('EMPLOYEE', 'DEALER')),
    CONSTRAINT CK_UserAccount_Owner
        CHECK
        (
            (AccountType = 'EMPLOYEE' AND EmployeeId IS NOT NULL AND DealerId IS NULL)
            OR
            (AccountType = 'DEALER' AND DealerId IS NOT NULL AND EmployeeId IS NULL)
        ),
    CONSTRAINT CK_UserAccount_Status
        CHECK (AccountStatus IN ('ACTIVE', 'LOCKED', 'DISABLED'))
);
GO

CREATE UNIQUE INDEX UX_UserAccount_Employee
    ON dbo.UserAccount (EmployeeId)
    WHERE EmployeeId IS NOT NULL;
GO

CREATE UNIQUE INDEX UX_UserAccount_Dealer
    ON dbo.UserAccount (DealerId)
    WHERE DealerId IS NOT NULL;
GO

CREATE TABLE dbo.PasskeyCredential
(
    PasskeyCredentialId bigint IDENTITY(1,1) NOT NULL,
    UserAccountId       bigint NOT NULL,
    CredentialId        varbinary(1024) NOT NULL,
    PublicKey           varbinary(max) NOT NULL,
    SignCount           bigint NOT NULL
        CONSTRAINT DF_PasskeyCredential_SignCount DEFAULT (0),
    Transports          varchar(200) NULL,
    DeviceName          nvarchar(100) NULL,
    CreatedAt           datetime2(0) NOT NULL
        CONSTRAINT DF_PasskeyCredential_CreatedAt DEFAULT (sysdatetime()),
    LastUsedAt          datetime2(0) NULL,
    RevokedAt           datetime2(0) NULL,

    CONSTRAINT PK_PasskeyCredential
        PRIMARY KEY CLUSTERED (PasskeyCredentialId),
    CONSTRAINT FK_PasskeyCredential_UserAccount
        FOREIGN KEY (UserAccountId) REFERENCES dbo.UserAccount (UserAccountId),
    CONSTRAINT UQ_PasskeyCredential_CredentialId UNIQUE (CredentialId),
    CONSTRAINT CK_PasskeyCredential_SignCount CHECK (SignCount >= 0)
);
GO

CREATE INDEX IX_PasskeyCredential_UserAccount
    ON dbo.PasskeyCredential (UserAccountId, RevokedAt);
GO

CREATE TABLE dbo.PasskeyRegistrationInvitation
(
    InvitationId        bigint IDENTITY(1,1) NOT NULL,
    UserAccountId       bigint NOT NULL,
    TokenHash           varbinary(64) NOT NULL,
    ExpiresAt           datetime2(0) NOT NULL,
    UsedAt              datetime2(0) NULL,
    RevokedAt           datetime2(0) NULL,
    CreatedAt           datetime2(0) NOT NULL
        CONSTRAINT DF_PasskeyRegistrationInvitation_CreatedAt DEFAULT (sysdatetime()),
    CreatedByEmployeeId bigint NOT NULL,

    CONSTRAINT PK_PasskeyRegistrationInvitation
        PRIMARY KEY CLUSTERED (InvitationId),
    CONSTRAINT FK_PasskeyRegistrationInvitation_UserAccount
        FOREIGN KEY (UserAccountId) REFERENCES dbo.UserAccount (UserAccountId),
    CONSTRAINT FK_PasskeyRegistrationInvitation_CreatedByEmployee
        FOREIGN KEY (CreatedByEmployeeId) REFERENCES dbo.Employee (EmployeeId),
    CONSTRAINT UQ_PasskeyRegistrationInvitation_TokenHash UNIQUE (TokenHash),
    CONSTRAINT CK_PasskeyRegistrationInvitation_Expiry
        CHECK (ExpiresAt > CreatedAt)
);
GO

CREATE INDEX IX_PasskeyRegistrationInvitation_AccountExpiry
    ON dbo.PasskeyRegistrationInvitation (UserAccountId, ExpiresAt);
GO

/* =========================================================
   4. Product and import data
   ========================================================= */

CREATE TABLE dbo.Product
(
    ProductId      bigint IDENTITY(1,1) NOT NULL,
    ProductCode    varchar(50) NOT NULL,
    ProductName    nvarchar(200) NOT NULL,
    CategoryLevel1 nvarchar(100) NULL,
    CategoryLevel2 nvarchar(100) NULL,
    IsActive       bit NOT NULL
        CONSTRAINT DF_Product_IsActive DEFAULT (1),
    CreatedAt      datetime2(0) NOT NULL
        CONSTRAINT DF_Product_CreatedAt DEFAULT (sysdatetime()),

    CONSTRAINT PK_Product PRIMARY KEY CLUSTERED (ProductId),
    CONSTRAINT UQ_Product_ProductCode UNIQUE (ProductCode)
);
GO

CREATE TABLE dbo.ImportBatch
(
    ImportBatchId        bigint IDENTITY(1,1) NOT NULL,
    ImportType           varchar(30) NOT NULL,
    DataMonth            char(6) NULL,
    DataDate             date NULL,
    OriginalFileName     nvarchar(260) NOT NULL,
    StoredFilePath       nvarchar(1000) NOT NULL,
    FileHash             varchar(128) NOT NULL,
    FileSize             bigint NOT NULL,
    ImportStatus         varchar(20) NOT NULL
        CONSTRAINT DF_ImportBatch_ImportStatus DEFAULT ('Processing'),
    ReplacedBatchId      bigint NULL,
    TotalRowCount        int NOT NULL
        CONSTRAINT DF_ImportBatch_TotalRowCount DEFAULT (0),
    SuccessRowCount      int NOT NULL
        CONSTRAINT DF_ImportBatch_SuccessRowCount DEFAULT (0),
    ErrorRowCount        int NOT NULL
        CONSTRAINT DF_ImportBatch_ErrorRowCount DEFAULT (0),
    ErrorSummary         nvarchar(max) NULL,
    ImportedAt           datetime2(0) NOT NULL
        CONSTRAINT DF_ImportBatch_ImportedAt DEFAULT (sysdatetime()),
    ImportedByEmployeeId bigint NOT NULL,

    CONSTRAINT PK_ImportBatch PRIMARY KEY CLUSTERED (ImportBatchId),
    CONSTRAINT FK_ImportBatch_ImportedByEmployee
        FOREIGN KEY (ImportedByEmployeeId) REFERENCES dbo.Employee (EmployeeId),
    CONSTRAINT FK_ImportBatch_ReplacedBatch
        FOREIGN KEY (ReplacedBatchId) REFERENCES dbo.ImportBatch (ImportBatchId),
    CONSTRAINT CK_ImportBatch_DataPeriod
        CHECK
        (
            (DataMonth IS NOT NULL AND DataDate IS NULL)
            OR (DataMonth IS NULL AND DataDate IS NOT NULL)
        ),
    CONSTRAINT CK_ImportBatch_DataMonth
        CHECK
        (
            DataMonth IS NULL
            OR
            (
                DataMonth NOT LIKE '%[^0-9]%'
                AND SUBSTRING(DataMonth, 5, 2) BETWEEN '01' AND '12'
            )
        ),
    CONSTRAINT CK_ImportBatch_Status
        CHECK (ImportStatus IN ('Processing','Failed','Official','Superseded','Voided')),
    CONSTRAINT CK_ImportBatch_FileSize CHECK (FileSize >= 0),
    CONSTRAINT CK_ImportBatch_RowCounts
        CHECK
        (
            TotalRowCount >= 0
            AND SuccessRowCount >= 0
            AND ErrorRowCount >= 0
            AND SuccessRowCount + ErrorRowCount <= TotalRowCount
        ),
    CONSTRAINT CK_ImportBatch_NotSelfReplaced
        CHECK (ReplacedBatchId IS NULL OR ReplacedBatchId <> ImportBatchId)
);
GO

CREATE INDEX IX_ImportBatch_TypePeriod
    ON dbo.ImportBatch (ImportType, DataMonth, DataDate, ImportStatus);
GO

CREATE TABLE dbo.MonthlyOpeningInventoryDetail
(
    OpeningInventoryDetailId bigint IDENTITY(1,1) NOT NULL,
    ImportBatchId            bigint NOT NULL,
    SourceRowNumber          int NOT NULL,
    DealerId                bigint NOT NULL,
    ProductId               bigint NOT NULL,
    OpeningQuantity          int NOT NULL,

    CONSTRAINT PK_MonthlyOpeningInventoryDetail
        PRIMARY KEY CLUSTERED (OpeningInventoryDetailId),
    CONSTRAINT FK_MonthlyOpeningInventoryDetail_ImportBatch
        FOREIGN KEY (ImportBatchId) REFERENCES dbo.ImportBatch (ImportBatchId),
    CONSTRAINT FK_MonthlyOpeningInventoryDetail_Dealer
        FOREIGN KEY (DealerId) REFERENCES dbo.Dealer (DealerId),
    CONSTRAINT FK_MonthlyOpeningInventoryDetail_Product
        FOREIGN KEY (ProductId) REFERENCES dbo.Product (ProductId),
    CONSTRAINT UQ_MonthlyOpeningInventoryDetail
        UNIQUE (ImportBatchId, DealerId, ProductId),
    CONSTRAINT CK_MonthlyOpeningInventoryDetail_SourceRow
        CHECK (SourceRowNumber > 0),
    CONSTRAINT CK_MonthlyOpeningInventoryDetail_Quantity
        CHECK (OpeningQuantity >= 0)
);
GO

CREATE INDEX IX_MonthlyOpeningInventoryDetail_DealerProduct
    ON dbo.MonthlyOpeningInventoryDetail (DealerId, ProductId, ImportBatchId);
GO

CREATE TABLE dbo.SellInTransaction
(
    SellInTransactionId   bigint IDENTITY(1,1) NOT NULL,
    ImportBatchId         bigint NOT NULL,
    SourceRowNumber       int NOT NULL,
    DealerId              bigint NOT NULL,
    ProductId             bigint NOT NULL,
    SalesDocumentNo       varchar(50) NOT NULL,
    SalesDocumentItemNo   varchar(20) NOT NULL,
    InvoiceNo             varchar(50) NULL,
    OrderDate             date NOT NULL,
    BillingDate           date NOT NULL,
    InvoiceDate           date NULL,
    InventoryEffectiveDate date NOT NULL,
    Quantity              decimal(18,3) NOT NULL,
    TransactionType       varchar(20) NOT NULL,
    TransactionStatus     varchar(20) NOT NULL,
    ReviewStatus          varchar(20) NOT NULL,
    CreatedAt             datetime2(0) NOT NULL
        CONSTRAINT DF_SellInTransaction_CreatedAt DEFAULT (sysdatetime()),
    UpdatedAt             datetime2(0) NULL,

    CONSTRAINT PK_SellInTransaction
        PRIMARY KEY CLUSTERED (SellInTransactionId),
    CONSTRAINT FK_SellInTransaction_ImportBatch
        FOREIGN KEY (ImportBatchId) REFERENCES dbo.ImportBatch (ImportBatchId),
    CONSTRAINT FK_SellInTransaction_Dealer
        FOREIGN KEY (DealerId) REFERENCES dbo.Dealer (DealerId),
    CONSTRAINT FK_SellInTransaction_Product
        FOREIGN KEY (ProductId) REFERENCES dbo.Product (ProductId),
    CONSTRAINT UQ_SellInTransaction_DocumentItem
        UNIQUE (SalesDocumentNo, SalesDocumentItemNo),
    CONSTRAINT CK_SellInTransaction_SourceRow CHECK (SourceRowNumber > 0),
    CONSTRAINT CK_SellInTransaction_Quantity CHECK (Quantity <> 0)
);
GO

CREATE INDEX IX_SellInTransaction_Inventory
    ON dbo.SellInTransaction (DealerId, ProductId, InventoryEffectiveDate)
    INCLUDE (Quantity, TransactionStatus, ReviewStatus);
GO

CREATE INDEX IX_SellInTransaction_ImportBatch
    ON dbo.SellInTransaction (ImportBatchId, SourceRowNumber);
GO

/* =========================================================
   5. Store visits
   ========================================================= */

CREATE TABLE dbo.StoreVisit
(
    StoreVisitId              bigint IDENTITY(1,1) NOT NULL,
    DealerId                 bigint NOT NULL,
    DealerAssignmentId       bigint NULL,
    EntrySourceType          varchar(20) NOT NULL,
    ReportDateTime           datetime2(0) NOT NULL
        CONSTRAINT DF_StoreVisit_ReportDateTime DEFAULT (sysdatetime()),
    RecordStatus             varchar(20) NOT NULL
        CONSTRAINT DF_StoreVisit_RecordStatus DEFAULT ('ACTIVE'),
    CreatedAt                datetime2(0) NOT NULL
        CONSTRAINT DF_StoreVisit_CreatedAt DEFAULT (sysdatetime()),
    CreatedByUserAccountId   bigint NOT NULL,
    UpdatedAt                datetime2(0) NULL,
    UpdatedByUserAccountId   bigint NULL,

    CONSTRAINT PK_StoreVisit PRIMARY KEY CLUSTERED (StoreVisitId),
    CONSTRAINT FK_StoreVisit_Dealer
        FOREIGN KEY (DealerId) REFERENCES dbo.Dealer (DealerId),
    CONSTRAINT FK_StoreVisit_DealerAssignment
        FOREIGN KEY (DealerAssignmentId)
        REFERENCES dbo.DealerAssignmentHistory (DealerAssignmentId),
    CONSTRAINT FK_StoreVisit_CreatedByUserAccount
        FOREIGN KEY (CreatedByUserAccountId)
        REFERENCES dbo.UserAccount (UserAccountId),
    CONSTRAINT FK_StoreVisit_UpdatedByUserAccount
        FOREIGN KEY (UpdatedByUserAccountId)
        REFERENCES dbo.UserAccount (UserAccountId),
    CONSTRAINT CK_StoreVisit_EntrySourceType
        CHECK (EntrySourceType IN ('EMPLOYEE', 'DEALER')),
    CONSTRAINT CK_StoreVisit_RecordStatus
        CHECK (RecordStatus IN ('ACTIVE', 'VOIDED')),
    CONSTRAINT CK_StoreVisit_UpdateAudit
        CHECK
        (
            (UpdatedAt IS NULL AND UpdatedByUserAccountId IS NULL)
            OR (UpdatedAt IS NOT NULL AND UpdatedByUserAccountId IS NOT NULL)
        )
);
GO

CREATE INDEX IX_StoreVisit_DealerReportDate
    ON dbo.StoreVisit (DealerId, ReportDateTime DESC);
GO

CREATE TABLE dbo.StoreVisitProductDetail
(
    StoreVisitProductDetailId bigint IDENTITY(1,1) NOT NULL,
    StoreVisitId              bigint NOT NULL,
    ProductId                 bigint NOT NULL,
    SellOutQuantity           int NULL,
    SellOutDate               date NULL,
    DisplayQuantity           int NULL,
    CreatedAt                 datetime2(0) NOT NULL
        CONSTRAINT DF_StoreVisitProductDetail_CreatedAt DEFAULT (sysdatetime()),
    UpdatedAt                 datetime2(0) NULL,

    CONSTRAINT PK_StoreVisitProductDetail
        PRIMARY KEY CLUSTERED (StoreVisitProductDetailId),
    CONSTRAINT FK_StoreVisitProductDetail_StoreVisit
        FOREIGN KEY (StoreVisitId) REFERENCES dbo.StoreVisit (StoreVisitId),
    CONSTRAINT FK_StoreVisitProductDetail_Product
        FOREIGN KEY (ProductId) REFERENCES dbo.Product (ProductId),
    CONSTRAINT UQ_StoreVisitProductDetail
        UNIQUE (StoreVisitId, ProductId),
    CONSTRAINT CK_StoreVisitProductDetail_SellOutQuantity
        CHECK (SellOutQuantity IS NULL OR SellOutQuantity >= 0),
    CONSTRAINT CK_StoreVisitProductDetail_DisplayQuantity
        CHECK (DisplayQuantity IS NULL OR DisplayQuantity BETWEEN 1 AND 10),
    CONSTRAINT CK_StoreVisitProductDetail_HasValue
        CHECK
        (
            SellOutQuantity IS NOT NULL
            OR SellOutDate IS NOT NULL
            OR DisplayQuantity IS NOT NULL
        )
);
GO

CREATE INDEX IX_StoreVisitProductDetail_Product
    ON dbo.StoreVisitProductDetail (ProductId, StoreVisitId);
GO

/* =========================================================
   6. Visit tasks
   ========================================================= */

CREATE TABLE dbo.VisitTask
(
    VisitTaskId                  bigint IDENTITY(1,1) NOT NULL,
    TaskTitle                    nvarchar(200) NOT NULL,
    Instruction                  nvarchar(max) NOT NULL,
    ValidFrom                    date NOT NULL,
    DueDate                      date NOT NULL,
    RecordStatus                 varchar(20) NOT NULL
        CONSTRAINT DF_VisitTask_RecordStatus DEFAULT ('ACTIVE'),
    SampleTaskExecutionId        bigint NULL,
    SampleApprovedByEmployeeId   bigint NULL,
    SampleApprovedAt             datetime2(0) NULL,
    CreatedByEmployeeId          bigint NOT NULL,
    CreatedAt                    datetime2(0) NOT NULL
        CONSTRAINT DF_VisitTask_CreatedAt DEFAULT (sysdatetime()),
    UpdatedByEmployeeId          bigint NULL,
    UpdatedAt                    datetime2(0) NULL,

    CONSTRAINT PK_VisitTask PRIMARY KEY CLUSTERED (VisitTaskId),
    CONSTRAINT FK_VisitTask_SampleApprovedByEmployee
        FOREIGN KEY (SampleApprovedByEmployeeId)
        REFERENCES dbo.Employee (EmployeeId),
    CONSTRAINT FK_VisitTask_CreatedByEmployee
        FOREIGN KEY (CreatedByEmployeeId) REFERENCES dbo.Employee (EmployeeId),
    CONSTRAINT FK_VisitTask_UpdatedByEmployee
        FOREIGN KEY (UpdatedByEmployeeId) REFERENCES dbo.Employee (EmployeeId),
    CONSTRAINT UQ_VisitTask_VisitTask_SampleExecution
        UNIQUE (VisitTaskId, SampleTaskExecutionId),
    CONSTRAINT CK_VisitTask_DateRange CHECK (DueDate >= ValidFrom),
    CONSTRAINT CK_VisitTask_RecordStatus
        CHECK (RecordStatus IN ('ACTIVE', 'VOIDED')),
    CONSTRAINT CK_VisitTask_UpdateAudit
        CHECK
        (
            (UpdatedAt IS NULL AND UpdatedByEmployeeId IS NULL)
            OR (UpdatedAt IS NOT NULL AND UpdatedByEmployeeId IS NOT NULL)
        ),
    CONSTRAINT CK_VisitTask_SampleApprovalAudit
        CHECK
        (
            (SampleApprovedAt IS NULL AND SampleApprovedByEmployeeId IS NULL)
            OR
            (
                SampleApprovedAt IS NOT NULL
                AND SampleApprovedByEmployeeId IS NOT NULL
                AND SampleTaskExecutionId IS NOT NULL
            )
        )
);
GO

CREATE UNIQUE INDEX UX_VisitTask_SampleTaskExecution
    ON dbo.VisitTask (SampleTaskExecutionId)
    WHERE SampleTaskExecutionId IS NOT NULL;
GO

CREATE TABLE dbo.VisitTaskExecution
(
    TaskExecutionId          bigint IDENTITY(1,1) NOT NULL,
    VisitTaskId             bigint NOT NULL,
    DealerId                bigint NOT NULL,
    ResponsibleEmployeeId   bigint NOT NULL,
    CompletedByEmployeeId   bigint NULL,
    ExecutionNote           nvarchar(max) NULL,
    SubmittedAt             datetime2(0) NULL,
    CreatedAt               datetime2(0) NOT NULL
        CONSTRAINT DF_VisitTaskExecution_CreatedAt DEFAULT (sysdatetime()),

    CONSTRAINT PK_VisitTaskExecution
        PRIMARY KEY CLUSTERED (TaskExecutionId),
    CONSTRAINT UQ_VisitTaskExecution_TaskExecution
        UNIQUE (VisitTaskId, TaskExecutionId),
    CONSTRAINT UQ_VisitTaskExecution_TaskDealer
        UNIQUE (VisitTaskId, DealerId),
    CONSTRAINT FK_VisitTaskExecution_VisitTask
        FOREIGN KEY (VisitTaskId) REFERENCES dbo.VisitTask (VisitTaskId),
    CONSTRAINT FK_VisitTaskExecution_Dealer
        FOREIGN KEY (DealerId) REFERENCES dbo.Dealer (DealerId),
    CONSTRAINT FK_VisitTaskExecution_ResponsibleEmployee
        FOREIGN KEY (ResponsibleEmployeeId) REFERENCES dbo.Employee (EmployeeId),
    CONSTRAINT FK_VisitTaskExecution_CompletedByEmployee
        FOREIGN KEY (CompletedByEmployeeId) REFERENCES dbo.Employee (EmployeeId),
    CONSTRAINT CK_VisitTaskExecution_Submission
        CHECK
        (
            SubmittedAt IS NULL
            OR CompletedByEmployeeId IS NOT NULL
        )
);
GO

ALTER TABLE dbo.VisitTask
ADD CONSTRAINT FK_VisitTask_SampleExecution
    FOREIGN KEY (VisitTaskId, SampleTaskExecutionId)
    REFERENCES dbo.VisitTaskExecution (VisitTaskId, TaskExecutionId);
GO

CREATE INDEX IX_VisitTaskExecution_Employee
    ON dbo.VisitTaskExecution (ResponsibleEmployeeId, SubmittedAt, VisitTaskId);
GO

CREATE TABLE dbo.VisitTaskPhoto
(
    TaskPhotoId        bigint IDENTITY(1,1) NOT NULL,
    TaskExecutionId   bigint NOT NULL,
    SampleTaskPhotoId bigint NULL,
    PhotoDescription  nvarchar(500) NULL,
    StoredFileName    nvarchar(260) NOT NULL,
    StoredFilePath    nvarchar(1000) NOT NULL,
    CapturedAt        datetime2(0) NOT NULL,
    SortOrder         int NOT NULL
        CONSTRAINT DF_VisitTaskPhoto_SortOrder DEFAULT (0),
    UploadedAt        datetime2(0) NOT NULL
        CONSTRAINT DF_VisitTaskPhoto_UploadedAt DEFAULT (sysdatetime()),

    CONSTRAINT PK_VisitTaskPhoto PRIMARY KEY CLUSTERED (TaskPhotoId),
    CONSTRAINT FK_VisitTaskPhoto_TaskExecution
        FOREIGN KEY (TaskExecutionId)
        REFERENCES dbo.VisitTaskExecution (TaskExecutionId),
    CONSTRAINT FK_VisitTaskPhoto_SampleTaskPhoto
        FOREIGN KEY (SampleTaskPhotoId)
        REFERENCES dbo.VisitTaskPhoto (TaskPhotoId),
    CONSTRAINT CK_VisitTaskPhoto_SortOrder CHECK (SortOrder >= 0),
    CONSTRAINT CK_VisitTaskPhoto_NotSelfReference
        CHECK (SampleTaskPhotoId IS NULL OR SampleTaskPhotoId <> TaskPhotoId)
);
GO

CREATE INDEX IX_VisitTaskPhoto_TaskExecution
    ON dbo.VisitTaskPhoto (TaskExecutionId, SortOrder, TaskPhotoId);
GO

CREATE INDEX IX_VisitTaskPhoto_SampleTaskPhoto
    ON dbo.VisitTaskPhoto (SampleTaskPhotoId)
    WHERE SampleTaskPhotoId IS NOT NULL;
GO

/* =========================================================
   7. Verification
   ========================================================= */

SELECT
    DB_NAME() AS DatabaseName,
    COUNT(*) AS UserTableCount
FROM sys.tables
WHERE is_ms_shipped = 0;
GO

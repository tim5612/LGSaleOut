/*
    LGSaleOut database creation script
    Target: Microsoft SQL Server 2016 or later
    Purpose: Monthly dealer ending-inventory snapshots

    This script creates schema only. It does not import any Excel data.
    It is non-destructive: existing database objects are not dropped.
*/

USE [master];
GO

IF DB_ID(N'LGSaleOut') IS NULL
BEGIN
    EXEC (N'CREATE DATABASE [LGSaleOut];');
END;
GO

USE [LGSaleOut];
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET CONCAT_NULL_YIELDS_NULL ON;
GO

/* Import audit ---------------------------------------------------------- */
IF OBJECT_ID(N'dbo.ImportBatch', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.ImportBatch
    (
        ImportBatchId   bigint IDENTITY(1,1) NOT NULL,
        PeriodEnd       date NOT NULL,
        SourceFileName  nvarchar(260) NOT NULL,
        SourceSheetName nvarchar(128) NOT NULL,
        SourceRowCount  int NULL,
        ImportedRowCount int NULL,
        RejectedRowCount int NULL,
        ImportStatus    varchar(20) NOT NULL
            CONSTRAINT DF_ImportBatch_ImportStatus DEFAULT ('Pending'),
        ImportedAt      datetime2(0) NOT NULL
            CONSTRAINT DF_ImportBatch_ImportedAt DEFAULT (sysdatetime()),
        ImportedBy      nvarchar(128) NOT NULL
            CONSTRAINT DF_ImportBatch_ImportedBy DEFAULT (suser_sname()),
        CompletedAt     datetime2(0) NULL,
        ErrorMessage    nvarchar(2000) NULL,

        CONSTRAINT PK_ImportBatch PRIMARY KEY CLUSTERED (ImportBatchId),
        CONSTRAINT CK_ImportBatch_PeriodEnd
            CHECK (PeriodEnd = EOMONTH(PeriodEnd)),
        CONSTRAINT CK_ImportBatch_Status
            CHECK (ImportStatus IN ('Pending', 'Staged', 'Validated', 'Completed', 'Failed')),
        CONSTRAINT CK_ImportBatch_RowCounts
            CHECK
            (
                (SourceRowCount IS NULL OR SourceRowCount >= 0)
                AND (ImportedRowCount IS NULL OR ImportedRowCount >= 0)
                AND (RejectedRowCount IS NULL OR RejectedRowCount >= 0)
            )
    );

    CREATE INDEX IX_ImportBatch_PeriodEnd
        ON dbo.ImportBatch (PeriodEnd, ImportBatchId DESC);
END;
GO

/* Master data ----------------------------------------------------------- */
IF OBJECT_ID(N'dbo.Dealer', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Dealer
    (
        DealerId       int IDENTITY(1,1) NOT NULL,
        DealerCode     varchar(12) NOT NULL,
        ShortName      nvarchar(50) NOT NULL,
        IsActive       bit NOT NULL CONSTRAINT DF_Dealer_IsActive DEFAULT (1),
        CreatedAt      datetime2(0) NOT NULL CONSTRAINT DF_Dealer_CreatedAt DEFAULT (sysdatetime()),
        ModifiedAt     datetime2(0) NOT NULL CONSTRAINT DF_Dealer_ModifiedAt DEFAULT (sysdatetime()),
        RowVersion     rowversion NOT NULL,

        CONSTRAINT PK_Dealer PRIMARY KEY CLUSTERED (DealerId),
        CONSTRAINT UQ_Dealer_DealerCode UNIQUE (DealerCode),
        CONSTRAINT CK_Dealer_DealerCode
            CHECK (DealerCode LIKE 'TW[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]H'),
        CONSTRAINT CK_Dealer_ShortName_NotBlank
            CHECK (LEN(LTRIM(RTRIM(ShortName))) > 0)
    );
END;
GO

IF OBJECT_ID(N'dbo.Salesperson', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Salesperson
    (
        SalespersonId   int IDENTITY(1,1) NOT NULL,
        SalespersonName nvarchar(50) NOT NULL,
        IsActive        bit NOT NULL CONSTRAINT DF_Salesperson_IsActive DEFAULT (1),
        CreatedAt       datetime2(0) NOT NULL CONSTRAINT DF_Salesperson_CreatedAt DEFAULT (sysdatetime()),
        ModifiedAt      datetime2(0) NOT NULL CONSTRAINT DF_Salesperson_ModifiedAt DEFAULT (sysdatetime()),
        RowVersion      rowversion NOT NULL,

        CONSTRAINT PK_Salesperson PRIMARY KEY CLUSTERED (SalespersonId),
        CONSTRAINT UQ_Salesperson_Name UNIQUE (SalespersonName),
        CONSTRAINT CK_Salesperson_Name_NotBlank
            CHECK (LEN(LTRIM(RTRIM(SalespersonName))) > 0)
    );
END;
GO

IF OBJECT_ID(N'dbo.ProductCategory', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.ProductCategory
    (
        CategoryId      int IDENTITY(1,1) NOT NULL,
        CategoryCode    nvarchar(50) NOT NULL,
        SubcategoryName nvarchar(100) NOT NULL,
        IsActive        bit NOT NULL CONSTRAINT DF_ProductCategory_IsActive DEFAULT (1),
        CreatedAt       datetime2(0) NOT NULL CONSTRAINT DF_ProductCategory_CreatedAt DEFAULT (sysdatetime()),
        ModifiedAt      datetime2(0) NOT NULL CONSTRAINT DF_ProductCategory_ModifiedAt DEFAULT (sysdatetime()),
        RowVersion      rowversion NOT NULL,

        CONSTRAINT PK_ProductCategory PRIMARY KEY CLUSTERED (CategoryId),
        CONSTRAINT UQ_ProductCategory UNIQUE (CategoryCode, SubcategoryName),
        CONSTRAINT CK_ProductCategory_Code_NotBlank
            CHECK (LEN(LTRIM(RTRIM(CategoryCode))) > 0),
        CONSTRAINT CK_ProductCategory_Name_NotBlank
            CHECK (LEN(LTRIM(RTRIM(SubcategoryName))) > 0)
    );
END;
GO

IF OBJECT_ID(N'dbo.Product', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Product
    (
        ProductId   int IDENTITY(1,1) NOT NULL,
        ModelCode   varchar(50) NOT NULL,
        CategoryId  int NOT NULL,
        IsActive    bit NOT NULL CONSTRAINT DF_Product_IsActive DEFAULT (1),
        CreatedAt   datetime2(0) NOT NULL CONSTRAINT DF_Product_CreatedAt DEFAULT (sysdatetime()),
        ModifiedAt  datetime2(0) NOT NULL CONSTRAINT DF_Product_ModifiedAt DEFAULT (sysdatetime()),
        RowVersion  rowversion NOT NULL,

        CONSTRAINT PK_Product PRIMARY KEY CLUSTERED (ProductId),
        CONSTRAINT UQ_Product_ModelCode UNIQUE (ModelCode),
        CONSTRAINT FK_Product_ProductCategory
            FOREIGN KEY (CategoryId) REFERENCES dbo.ProductCategory (CategoryId),
        CONSTRAINT CK_Product_ModelCode_NotBlank
            CHECK (LEN(LTRIM(RTRIM(ModelCode))) > 0)
    );

    CREATE INDEX IX_Product_CategoryId
        ON dbo.Product (CategoryId, ProductId)
        INCLUDE (ModelCode, IsActive);
END;
GO

/* Raw staging: retain source text for validation and traceability -------- */
IF OBJECT_ID(N'dbo.InventoryMonthEndStage', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.InventoryMonthEndStage
    (
        StageId          bigint IDENTITY(1,1) NOT NULL,
        ImportBatchId    bigint NOT NULL,
        SourceRowNumber  int NOT NULL,
        DealerCodeRaw    nvarchar(100) NULL,
        ShortNameRaw     nvarchar(100) NULL,
        CategoryRaw      nvarchar(100) NULL,
        SubcategoryRaw   nvarchar(100) NULL,
        ModelCodeRaw     nvarchar(100) NULL,
        DisplayQtyRaw    nvarchar(100) NULL,
        EndingQtyRaw     nvarchar(100) NULL,
        ExcludedRaw      nvarchar(100) NULL,
        SalespersonRaw   nvarchar(100) NULL,
        ValidationStatus varchar(20) NOT NULL
            CONSTRAINT DF_InventoryMonthEndStage_Status DEFAULT ('Pending'),
        ValidationError  nvarchar(2000) NULL,
        StagedAt         datetime2(0) NOT NULL
            CONSTRAINT DF_InventoryMonthEndStage_StagedAt DEFAULT (sysdatetime()),

        CONSTRAINT PK_InventoryMonthEndStage PRIMARY KEY CLUSTERED (StageId),
        CONSTRAINT FK_InventoryMonthEndStage_ImportBatch
            FOREIGN KEY (ImportBatchId) REFERENCES dbo.ImportBatch (ImportBatchId),
        CONSTRAINT UQ_InventoryMonthEndStage_SourceRow
            UNIQUE (ImportBatchId, SourceRowNumber),
        CONSTRAINT CK_InventoryMonthEndStage_RowNumber
            CHECK (SourceRowNumber > 0),
        CONSTRAINT CK_InventoryMonthEndStage_Status
            CHECK (ValidationStatus IN ('Pending', 'Valid', 'Rejected', 'Loaded'))
    );

    CREATE INDEX IX_InventoryMonthEndStage_Validation
        ON dbo.InventoryMonthEndStage (ImportBatchId, ValidationStatus)
        INCLUDE (SourceRowNumber, ValidationError);
END;
GO

/* Monthly fact ---------------------------------------------------------- */
IF OBJECT_ID(N'dbo.InventoryMonthEnd', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.InventoryMonthEnd
    (
        PeriodEnd       date NOT NULL,
        DealerId        int NOT NULL,
        ProductId       int NOT NULL,
        SalespersonId   int NOT NULL,
        DisplayQuantity smallint NULL,
        EndingQuantity  smallint NOT NULL,
        IsExcluded      bit NOT NULL CONSTRAINT DF_InventoryMonthEnd_IsExcluded DEFAULT (0),
        ImportBatchId   bigint NOT NULL,
        SourceRowNumber int NOT NULL,
        CreatedAt       datetime2(0) NOT NULL
            CONSTRAINT DF_InventoryMonthEnd_CreatedAt DEFAULT (sysdatetime()),
        ModifiedAt      datetime2(0) NOT NULL
            CONSTRAINT DF_InventoryMonthEnd_ModifiedAt DEFAULT (sysdatetime()),
        RowVersion      rowversion NOT NULL,

        CONSTRAINT PK_InventoryMonthEnd
            PRIMARY KEY CLUSTERED (PeriodEnd, DealerId, ProductId),
        CONSTRAINT FK_InventoryMonthEnd_Dealer
            FOREIGN KEY (DealerId) REFERENCES dbo.Dealer (DealerId),
        CONSTRAINT FK_InventoryMonthEnd_Product
            FOREIGN KEY (ProductId) REFERENCES dbo.Product (ProductId),
        CONSTRAINT FK_InventoryMonthEnd_Salesperson
            FOREIGN KEY (SalespersonId) REFERENCES dbo.Salesperson (SalespersonId),
        CONSTRAINT FK_InventoryMonthEnd_ImportBatch
            FOREIGN KEY (ImportBatchId) REFERENCES dbo.ImportBatch (ImportBatchId),
        CONSTRAINT CK_InventoryMonthEnd_PeriodEnd
            CHECK (PeriodEnd = EOMONTH(PeriodEnd)),
        CONSTRAINT CK_InventoryMonthEnd_DisplayQuantity
            CHECK (DisplayQuantity IS NULL OR DisplayQuantity >= 0),
        CONSTRAINT CK_InventoryMonthEnd_SourceRowNumber
            CHECK (SourceRowNumber > 0)
    );

    CREATE INDEX IX_InventoryMonthEnd_DealerPeriod
        ON dbo.InventoryMonthEnd (DealerId, PeriodEnd DESC)
        INCLUDE (ProductId, SalespersonId, DisplayQuantity, EndingQuantity, IsExcluded);

    CREATE INDEX IX_InventoryMonthEnd_ProductPeriod
        ON dbo.InventoryMonthEnd (ProductId, PeriodEnd DESC)
        INCLUDE (DealerId, SalespersonId, DisplayQuantity, EndingQuantity, IsExcluded);

    CREATE INDEX IX_InventoryMonthEnd_SalespersonPeriod
        ON dbo.InventoryMonthEnd (SalespersonId, PeriodEnd DESC)
        INCLUDE (DealerId, ProductId, DisplayQuantity, EndingQuantity, IsExcluded);

    CREATE INDEX IX_InventoryMonthEnd_ImportBatch
        ON dbo.InventoryMonthEnd (ImportBatchId, SourceRowNumber);
END;
GO

/* Reporting view -------------------------------------------------------- */
CREATE OR ALTER VIEW dbo.vwInventoryMonthEndDetail
AS
    SELECT
        f.PeriodEnd,
        d.DealerCode,
        d.ShortName,
        c.CategoryCode,
        c.SubcategoryName,
        p.ModelCode,
        f.DisplayQuantity,
        f.EndingQuantity,
        f.IsExcluded,
        s.SalespersonName,
        f.ImportBatchId,
        f.SourceRowNumber
    FROM dbo.InventoryMonthEnd AS f
    INNER JOIN dbo.Dealer AS d
        ON d.DealerId = f.DealerId
    INNER JOIN dbo.Product AS p
        ON p.ProductId = f.ProductId
    INNER JOIN dbo.ProductCategory AS c
        ON c.CategoryId = p.CategoryId
    INNER JOIN dbo.Salesperson AS s
        ON s.SalespersonId = f.SalespersonId;
GO

/* Useful summary view; excluded inventory is kept but not counted. ------ */
CREATE OR ALTER VIEW dbo.vwInventoryMonthEndSummary
AS
    SELECT
        f.PeriodEnd,
        c.CategoryCode,
        c.SubcategoryName,
        SUM(CONVERT(bigint, ISNULL(f.DisplayQuantity, 0))) AS DisplayQuantity,
        SUM(CONVERT(bigint, f.EndingQuantity)) AS EndingQuantity,
        SUM(CONVERT(bigint, CASE WHEN f.IsExcluded = 0 THEN f.EndingQuantity ELSE 0 END))
            AS CountedEndingQuantity,
        SUM(CONVERT(bigint, CASE WHEN f.IsExcluded = 1 THEN f.EndingQuantity ELSE 0 END))
            AS ExcludedEndingQuantity
    FROM dbo.InventoryMonthEnd AS f
    INNER JOIN dbo.Product AS p
        ON p.ProductId = f.ProductId
    INNER JOIN dbo.ProductCategory AS c
        ON c.CategoryId = p.CategoryId
    GROUP BY
        f.PeriodEnd,
        c.CategoryCode,
        c.SubcategoryName;
GO

PRINT N'LGSaleOut database schema is ready. No source data was imported.';
GO

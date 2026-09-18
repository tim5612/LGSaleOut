/* Run manually after reviewing and backing up the target database. */
USE [LGSaleOut];
GO
SET XACT_ABORT ON;
BEGIN TRY
    BEGIN TRANSACTION;
    IF COL_LENGTH('dbo.Dealer','ShortName') IS NULL ALTER TABLE dbo.Dealer ADD ShortName nvarchar(150) NULL;
    IF COL_LENGTH('dbo.Dealer','ContactName') IS NULL ALTER TABLE dbo.Dealer ADD ContactName nvarchar(100) NULL;
    IF COL_LENGTH('dbo.Dealer','MobilePhone') IS NULL ALTER TABLE dbo.Dealer ADD MobilePhone nvarchar(30) NULL;
    IF COL_LENGTH('dbo.Dealer','CompanyPhone') IS NULL ALTER TABLE dbo.Dealer ADD CompanyPhone nvarchar(30) NULL;
    IF COL_LENGTH('dbo.Dealer','PostalCode') IS NULL ALTER TABLE dbo.Dealer ADD PostalCode nvarchar(20) NULL;
    IF COL_LENGTH('dbo.Dealer','StreetAddress') IS NULL ALTER TABLE dbo.Dealer ADD StreetAddress nvarchar(500) NULL;

    IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE parent_object_id=OBJECT_ID('dbo.DealerLevelHistory') AND name='CK_DealerLevelHistory_Status')
        ALTER TABLE dbo.DealerLevelHistory DROP CONSTRAINT CK_DealerLevelHistory_Status;
    ALTER TABLE dbo.DealerLevelHistory ALTER COLUMN DealerStatus nvarchar(20) NOT NULL;
    UPDATE dbo.DealerLevelHistory SET DealerStatus=N'失聯店' WHERE DealerStatus=N'Z';
    /* Historical A-E values have no approved mapping; retain them for audit. */
    ALTER TABLE dbo.DealerLevelHistory ADD CONSTRAINT CK_DealerLevelHistory_Status
        CHECK (DealerStatus IN (N'一般店',N'DC店',N'專售店',N'AC店',N'批店',N'失聯店',N'A',N'B',N'C',N'D',N'E'));
    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO

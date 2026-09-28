SET XACT_ABORT ON;
BEGIN TRANSACTION;

CREATE TABLE dbo.DealerLocation
(
    DealerLocationId bigint IDENTITY(1,1) NOT NULL,
    DealerId         bigint NOT NULL,
    LocationName     nvarchar(150) NOT NULL,
    StreetAddress    nvarchar(500) NULL,
    ContactName      nvarchar(100) NULL,
    Phone            nvarchar(30) NULL,
    IsPrimary        bit NOT NULL CONSTRAINT DF_DealerLocation_IsPrimary DEFAULT (0),
    IsActive         bit NOT NULL CONSTRAINT DF_DealerLocation_IsActive DEFAULT (1),
    CreatedAt        datetime2(0) NOT NULL CONSTRAINT DF_DealerLocation_CreatedAt DEFAULT (sysdatetime()),
    UpdatedAt        datetime2(0) NULL,
    CONSTRAINT PK_DealerLocation PRIMARY KEY CLUSTERED (DealerLocationId),
    CONSTRAINT UQ_DealerLocation_LocationDealer UNIQUE (DealerLocationId,DealerId),
    CONSTRAINT FK_DealerLocation_Dealer FOREIGN KEY (DealerId) REFERENCES dbo.Dealer (DealerId)
);

CREATE UNIQUE INDEX UX_DealerLocation_Primary
    ON dbo.DealerLocation (DealerId) WHERE IsPrimary=1;
CREATE INDEX IX_DealerLocation_DealerActive
    ON dbo.DealerLocation (DealerId,IsActive,DealerLocationId);

INSERT dbo.DealerLocation(DealerId,LocationName,StreetAddress,ContactName,Phone,IsPrimary,IsActive)
SELECT DealerId,DealerName,StreetAddress,ContactName,COALESCE(CompanyPhone,MobilePhone),1,1
FROM dbo.Dealer;

ALTER TABLE dbo.StoreVisit ADD DealerLocationId bigint NULL;
UPDATE v SET DealerLocationId=l.DealerLocationId
FROM dbo.StoreVisit v JOIN dbo.DealerLocation l ON l.DealerId=v.DealerId AND l.IsPrimary=1;
ALTER TABLE dbo.StoreVisit ALTER COLUMN DealerLocationId bigint NOT NULL;
ALTER TABLE dbo.StoreVisit ADD CONSTRAINT FK_StoreVisit_DealerLocation
    FOREIGN KEY (DealerLocationId,DealerId) REFERENCES dbo.DealerLocation(DealerLocationId,DealerId);
CREATE INDEX IX_StoreVisit_LocationReportDate
    ON dbo.StoreVisit(DealerLocationId,ReportDateTime DESC);

ALTER TABLE dbo.VisitTaskExecution ADD DealerLocationId bigint NULL;
UPDATE e SET DealerLocationId=l.DealerLocationId
FROM dbo.VisitTaskExecution e JOIN dbo.DealerLocation l ON l.DealerId=e.DealerId AND l.IsPrimary=1;
ALTER TABLE dbo.VisitTaskExecution ALTER COLUMN DealerLocationId bigint NOT NULL;
ALTER TABLE dbo.VisitTaskExecution ADD CONSTRAINT FK_VisitTaskExecution_DealerLocation
    FOREIGN KEY (DealerLocationId,DealerId) REFERENCES dbo.DealerLocation(DealerLocationId,DealerId);
ALTER TABLE dbo.VisitTaskExecution DROP CONSTRAINT UQ_VisitTaskExecution_TaskDealer;
ALTER TABLE dbo.VisitTaskExecution ADD CONSTRAINT UQ_VisitTaskExecution_TaskLocation
    UNIQUE (VisitTaskId,DealerLocationId);

ALTER TABLE dbo.DealerProductDisplayPhoto ADD DealerLocationId bigint NULL;
UPDATE p SET DealerLocationId=l.DealerLocationId
FROM dbo.DealerProductDisplayPhoto p JOIN dbo.DealerLocation l ON l.DealerId=p.DealerId AND l.IsPrimary=1;
ALTER TABLE dbo.DealerProductDisplayPhoto ALTER COLUMN DealerLocationId bigint NOT NULL;
ALTER TABLE dbo.DealerProductDisplayPhoto ADD CONSTRAINT FK_DealerProductDisplayPhoto_DealerLocation
    FOREIGN KEY (DealerLocationId,DealerId) REFERENCES dbo.DealerLocation(DealerLocationId,DealerId);
DROP INDEX UX_DealerProductDisplayPhoto_Current ON dbo.DealerProductDisplayPhoto;
DROP INDEX IX_DealerProductDisplayPhoto_Psi ON dbo.DealerProductDisplayPhoto;
CREATE UNIQUE INDEX UX_DealerProductDisplayPhoto_Current
    ON dbo.DealerProductDisplayPhoto(DataMonth,DealerLocationId,ProductId) WHERE RecordStatus='ACTIVE';
CREATE INDEX IX_DealerProductDisplayPhoto_Psi
    ON dbo.DealerProductDisplayPhoto(DataMonth,DealerId,ProductId,DealerLocationId,RecordStatus)
    INCLUDE (ThumbnailFilePath,CapturedAt,UploadedByUserAccountId);

EXEC(N'CREATE TRIGGER dbo.TR_Dealer_CreatePrimaryLocation
ON dbo.Dealer AFTER INSERT AS
BEGIN
    SET NOCOUNT ON;
    INSERT dbo.DealerLocation(DealerId,LocationName,StreetAddress,ContactName,Phone,IsPrimary,IsActive)
    SELECT i.DealerId,i.DealerName,i.StreetAddress,i.ContactName,COALESCE(i.CompanyPhone,i.MobilePhone),1,1
    FROM inserted i
    WHERE NOT EXISTS (SELECT 1 FROM dbo.DealerLocation l WHERE l.DealerId=i.DealerId);
END');

COMMIT;
GO

SET XACT_ABORT ON;
BEGIN TRANSACTION;

IF OBJECT_ID(N'dbo.DealerProductDisplayPhoto', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DealerProductDisplayPhoto
    (
        DisplayPhotoId          bigint IDENTITY(1,1) NOT NULL,
        DataMonth               char(6) NOT NULL,
        DealerId                bigint NOT NULL,
        ProductId               bigint NOT NULL,
        SourceStoreVisitId      bigint NULL,
        OriginalFileName        nvarchar(260) NOT NULL,
        OriginalFilePath        nvarchar(1000) NOT NULL,
        ThumbnailFilePath       nvarchar(1000) NOT NULL,
        OriginalFileSize        int NOT NULL,
        ThumbnailFileSize       int NOT NULL,
        FileHash                char(64) NOT NULL,
        CapturedAt              datetime2(0) NOT NULL,
        UploadedAt              datetime2(0) NOT NULL
            CONSTRAINT DF_DealerProductDisplayPhoto_UploadedAt DEFAULT (sysdatetime()),
        UploadedByUserAccountId bigint NOT NULL,
        RecordStatus            varchar(20) NOT NULL
            CONSTRAINT DF_DealerProductDisplayPhoto_Status DEFAULT ('ACTIVE'),
        ReplacedPhotoId         bigint NULL,
        OriginalDeletedAt       datetime2(0) NULL,

        CONSTRAINT PK_DealerProductDisplayPhoto PRIMARY KEY CLUSTERED (DisplayPhotoId),
        CONSTRAINT FK_DealerProductDisplayPhoto_Dealer FOREIGN KEY (DealerId) REFERENCES dbo.Dealer (DealerId),
        CONSTRAINT FK_DealerProductDisplayPhoto_Product FOREIGN KEY (ProductId) REFERENCES dbo.Product (ProductId),
        CONSTRAINT FK_DealerProductDisplayPhoto_StoreVisit FOREIGN KEY (SourceStoreVisitId) REFERENCES dbo.StoreVisit (StoreVisitId),
        CONSTRAINT FK_DealerProductDisplayPhoto_UploadedBy FOREIGN KEY (UploadedByUserAccountId) REFERENCES dbo.UserAccount (UserAccountId),
        CONSTRAINT FK_DealerProductDisplayPhoto_ReplacedPhoto FOREIGN KEY (ReplacedPhotoId) REFERENCES dbo.DealerProductDisplayPhoto (DisplayPhotoId),
        CONSTRAINT CK_DealerProductDisplayPhoto_Month CHECK (DataMonth LIKE '[12][0-9][0-9][0-9][01][0-9]'),
        CONSTRAINT CK_DealerProductDisplayPhoto_Size CHECK (OriginalFileSize > 0 AND ThumbnailFileSize > 0),
        CONSTRAINT CK_DealerProductDisplayPhoto_Status CHECK (RecordStatus IN ('ACTIVE','SUPERSEDED')),
        CONSTRAINT CK_DealerProductDisplayPhoto_NotSelf CHECK (ReplacedPhotoId IS NULL OR ReplacedPhotoId <> DisplayPhotoId)
    );

    CREATE UNIQUE INDEX UX_DealerProductDisplayPhoto_Current
        ON dbo.DealerProductDisplayPhoto (DataMonth,DealerId,ProductId)
        WHERE RecordStatus='ACTIVE';

    CREATE INDEX IX_DealerProductDisplayPhoto_Psi
        ON dbo.DealerProductDisplayPhoto (DataMonth,DealerId,ProductId,RecordStatus)
        INCLUDE (ThumbnailFilePath,CapturedAt,UploadedByUserAccountId);
END;

COMMIT TRANSACTION;

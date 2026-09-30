USE LGSaleOut;
GO
SET XACT_ABORT ON;
GO
BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @Prefix char(4)=LEFT(CONVERT(char(6),GETDATE(),12),4);
    DECLARE @Base int=ISNULL((
        SELECT MAX(TRY_CONVERT(int,RIGHT(OrgUnitCode,2)))
        FROM dbo.OrganizationUnit
        WHERE LEN(OrgUnitCode)=6
          AND LEFT(OrgUnitCode,4)=@Prefix
          AND RIGHT(OrgUnitCode,2) NOT LIKE '%[^0-9]%'
    ),0);
    DECLARE @LegacyCount int=(
        SELECT COUNT(*)
        FROM dbo.OrganizationUnit
        WHERE LEN(OrgUnitCode)=20
          AND LEFT(OrgUnitCode,4)='ORG-'
          AND SUBSTRING(OrgUnitCode,5,16) COLLATE Latin1_General_100_BIN2 NOT LIKE '%[^0-9A-F]%'
    );

    IF @Base+@LegacyCount>99
        THROW 50040,N'處所 yymm 兩碼流水號不足，請先調整代碼規則。',1;

    ;WITH Legacy AS
    (
        SELECT OrgUnitId,
               ROW_NUMBER() OVER(ORDER BY OrgUnitId) AS SequenceNo
        FROM dbo.OrganizationUnit
        WHERE LEN(OrgUnitCode)=20
          AND LEFT(OrgUnitCode,4)='ORG-'
          AND SUBSTRING(OrgUnitCode,5,16) COLLATE Latin1_General_100_BIN2 NOT LIKE '%[^0-9A-F]%'
    )
    UPDATE o
       SET OrgUnitCode=@Prefix+RIGHT('00'+CONVERT(varchar(2),@Base+l.SequenceNo),2)
      FROM dbo.OrganizationUnit o
      JOIN Legacy l ON l.OrgUnitId=o.OrgUnitId;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO

SELECT OrgUnitId,OrgUnitCode,OrgUnitName,IsActive
FROM dbo.OrganizationUnit
ORDER BY OrgUnitId;
GO

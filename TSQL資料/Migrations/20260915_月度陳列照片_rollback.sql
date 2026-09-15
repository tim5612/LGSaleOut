/* 回復程式版本且確認不需保留陳列照片資料後，才可人工執行。 */
SET XACT_ABORT ON;
BEGIN TRANSACTION;

IF OBJECT_ID(N'dbo.DealerProductDisplayPhoto', N'U') IS NOT NULL
    DROP TABLE dbo.DealerProductDisplayPhoto;

COMMIT TRANSACTION;

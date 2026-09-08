-- Do not add source/display columns. Preserve signed opening quantities.
SET XACT_ABORT ON;
BEGIN TRANSACTION;
IF EXISTS(SELECT 1 FROM sys.check_constraints WHERE name='CK_MonthlyOpeningInventoryDetail_Quantity' AND parent_object_id=OBJECT_ID('dbo.MonthlyOpeningInventoryDetail'))
    ALTER TABLE dbo.MonthlyOpeningInventoryDetail DROP CONSTRAINT CK_MonthlyOpeningInventoryDetail_Quantity;
COMMIT TRANSACTION;

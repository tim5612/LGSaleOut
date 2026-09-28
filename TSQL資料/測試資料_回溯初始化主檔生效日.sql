/*
用途：初始化測試主檔完成後，將初始人員、處所、經銷商負責關係及經銷商級別
      回溯到測試資料起始日，使歷史月份 PSI 能找到當時有效的區域與負責業務。

安全範圍：
1. 只處理 ChangeReason = N'初始化匯入' 的歷程。
2. 只處理該員工／經銷商在對應歷程表中「恰好一筆」的資料。
3. 已有調職、調處、轉移或級別異動歷程者不會被修改，並會在結果中列為略過。
4. 可重複執行；已早於或等於目標日期的資料不會再次異動。

測試資料預設從 2026-01-01 生效。正式資料庫不得直接套用本腳本。
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

DECLARE @TargetDateTime datetime2(0) = '2026-01-01T00:00:00';
DECLARE @TargetHireDate date = CAST(@TargetDateTime AS date);
DECLARE @CommitChanges bit = 1; -- 改為 0 時只預覽並回滾。

BEGIN TRY
    BEGIN TRANSACTION;

    CREATE TABLE #TargetEmployee
    (
        EmployeeId bigint NOT NULL PRIMARY KEY
    );

    INSERT #TargetEmployee(EmployeeId)
    SELECT e.EmployeeId
    FROM dbo.Employee e
    WHERE
        (
            EXISTS
            (
                SELECT 1
                FROM dbo.EmployeePositionHistory p
                WHERE p.EmployeeId=e.EmployeeId
                  AND p.ChangeReason=N'初始化匯入'
            )
            OR EXISTS
            (
                SELECT 1
                FROM dbo.EmployeeOrgAssignmentHistory o
                WHERE o.EmployeeId=e.EmployeeId
                  AND o.ChangeReason=N'初始化匯入'
            )
        )
        AND (SELECT COUNT_BIG(*) FROM dbo.EmployeePositionHistory p WHERE p.EmployeeId=e.EmployeeId)=1
        AND (SELECT COUNT_BIG(*) FROM dbo.EmployeeOrgAssignmentHistory o WHERE o.EmployeeId=e.EmployeeId)=1;

    CREATE TABLE #TargetDealer
    (
        DealerId bigint NOT NULL PRIMARY KEY
    );

    INSERT #TargetDealer(DealerId)
    SELECT d.DealerId
    FROM dbo.Dealer d
    WHERE EXISTS
    (
        SELECT 1
        FROM dbo.DealerAssignmentHistory a
        WHERE a.DealerId=d.DealerId
          AND a.ChangeReason=N'初始化匯入'
    )
      AND (SELECT COUNT_BIG(*) FROM dbo.DealerAssignmentHistory a WHERE a.DealerId=d.DealerId)=1;

    CREATE TABLE #TargetDealerLevel
    (
        DealerId bigint NOT NULL PRIMARY KEY
    );

    INSERT #TargetDealerLevel(DealerId)
    SELECT d.DealerId
    FROM dbo.Dealer d
    WHERE EXISTS
    (
        SELECT 1
        FROM dbo.DealerLevelHistory h
        WHERE h.DealerId=d.DealerId
          AND h.ChangeReason=N'初始化匯入'
    )
      AND (SELECT COUNT_BIG(*) FROM dbo.DealerLevelHistory h WHERE h.DealerId=d.DealerId)=1;

    DECLARE @EmployeeHireDateCount int = 0;
    DECLARE @EmployeePositionCount int = 0;
    DECLARE @EmployeeOrgCount int = 0;
    DECLARE @DealerAssignmentCount int = 0;
    DECLARE @DealerLevelCount int = 0;

    UPDATE e
       SET e.HireDate=@TargetHireDate
    FROM dbo.Employee e
    JOIN #TargetEmployee t ON t.EmployeeId=e.EmployeeId
    WHERE e.HireDate>@TargetHireDate;
    SET @EmployeeHireDateCount=@@ROWCOUNT;

    UPDATE p
       SET p.StartDateTime=@TargetDateTime
    FROM dbo.EmployeePositionHistory p
    JOIN #TargetEmployee t ON t.EmployeeId=p.EmployeeId
    WHERE p.ChangeReason=N'初始化匯入'
      AND p.StartDateTime>@TargetDateTime
      AND (p.EndDateTime IS NULL OR p.EndDateTime>@TargetDateTime);
    SET @EmployeePositionCount=@@ROWCOUNT;

    UPDATE o
       SET o.StartDateTime=@TargetDateTime
    FROM dbo.EmployeeOrgAssignmentHistory o
    JOIN #TargetEmployee t ON t.EmployeeId=o.EmployeeId
    WHERE o.ChangeReason=N'初始化匯入'
      AND o.StartDateTime>@TargetDateTime
      AND (o.EndDateTime IS NULL OR o.EndDateTime>@TargetDateTime);
    SET @EmployeeOrgCount=@@ROWCOUNT;

    UPDATE a
       SET a.StartDateTime=@TargetDateTime
    FROM dbo.DealerAssignmentHistory a
    JOIN #TargetDealer t ON t.DealerId=a.DealerId
    WHERE a.ChangeReason=N'初始化匯入'
      AND a.StartDateTime>@TargetDateTime
      AND (a.EndDateTime IS NULL OR a.EndDateTime>@TargetDateTime);
    SET @DealerAssignmentCount=@@ROWCOUNT;

    UPDATE h
       SET h.StartDateTime=@TargetDateTime
    FROM dbo.DealerLevelHistory h
    JOIN #TargetDealerLevel t ON t.DealerId=h.DealerId
    WHERE h.ChangeReason=N'初始化匯入'
      AND h.StartDateTime>@TargetDateTime
      AND (h.EndDateTime IS NULL OR h.EndDateTime>@TargetDateTime);
    SET @DealerLevelCount=@@ROWCOUNT;

    SELECT
        @TargetDateTime AS TargetDateTime,
        @EmployeeHireDateCount AS EmployeeHireDateUpdated,
        @EmployeePositionCount AS EmployeePositionHistoryUpdated,
        @EmployeeOrgCount AS EmployeeOrgAssignmentHistoryUpdated,
        @DealerAssignmentCount AS DealerAssignmentHistoryUpdated,
        @DealerLevelCount AS DealerLevelHistoryUpdated,
        (
            SELECT COUNT_BIG(*)
            FROM dbo.EmployeePositionHistory p
            WHERE p.ChangeReason=N'初始化匯入'
              AND p.StartDateTime>@TargetDateTime
              AND (SELECT COUNT_BIG(*) FROM dbo.EmployeePositionHistory x WHERE x.EmployeeId=p.EmployeeId)>1
        ) AS EmployeePositionSkippedMultipleHistory,
        (
            SELECT COUNT_BIG(*)
            FROM dbo.EmployeeOrgAssignmentHistory o
            WHERE o.ChangeReason=N'初始化匯入'
              AND o.StartDateTime>@TargetDateTime
              AND (SELECT COUNT_BIG(*) FROM dbo.EmployeeOrgAssignmentHistory x WHERE x.EmployeeId=o.EmployeeId)>1
        ) AS EmployeeOrgSkippedMultipleHistory,
        (
            SELECT COUNT_BIG(*)
            FROM dbo.DealerAssignmentHistory a
            WHERE a.ChangeReason=N'初始化匯入'
              AND a.StartDateTime>@TargetDateTime
              AND (SELECT COUNT_BIG(*) FROM dbo.DealerAssignmentHistory x WHERE x.DealerId=a.DealerId)>1
        ) AS DealerAssignmentSkippedMultipleHistory,
        (
            SELECT COUNT_BIG(*)
            FROM dbo.DealerLevelHistory h
            WHERE h.ChangeReason=N'初始化匯入'
              AND h.StartDateTime>@TargetDateTime
              AND (SELECT COUNT_BIG(*) FROM dbo.DealerLevelHistory x WHERE x.DealerId=h.DealerId)>1
        ) AS DealerLevelSkippedMultipleHistory;

    SELECT TOP (100)
        d.DealerCode,
        d.DealerName,
        e.EmployeeName,
        o.OrgUnitName,
        a.StartDateTime AS DealerAssignmentStartDateTime,
        eh.StartDateTime AS EmployeeOrgStartDateTime
    FROM dbo.DealerAssignmentHistory a
    JOIN dbo.Dealer d ON d.DealerId=a.DealerId
    JOIN dbo.Employee e ON e.EmployeeId=a.EmployeeId
    LEFT JOIN dbo.EmployeeOrgAssignmentHistory eh
      ON eh.EmployeeId=e.EmployeeId
     AND eh.StartDateTime<=@TargetDateTime
     AND (eh.EndDateTime IS NULL OR eh.EndDateTime>@TargetDateTime)
    LEFT JOIN dbo.OrganizationUnit o ON o.OrgUnitId=eh.OrgUnitId
    WHERE a.StartDateTime<=@TargetDateTime
      AND (a.EndDateTime IS NULL OR a.EndDateTime>@TargetDateTime)
    ORDER BY o.OrgUnitName,e.EmployeeName,d.DealerCode;

    IF @CommitChanges=1
    BEGIN
        COMMIT TRANSACTION;
        PRINT N'已提交：初始化測試主檔生效日已回溯。';
    END
    ELSE
    BEGIN
        ROLLBACK TRANSACTION;
        PRINT N'僅預覽：交易已回滾。將 @CommitChanges 改為 1 才會正式更新。';
    END;
END TRY
BEGIN CATCH
    IF XACT_STATE()<>0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;

USE LGSaleOut;
GO
SET XACT_ABORT ON;
GO
BEGIN TRY
    BEGIN TRANSACTION;
    IF COL_LENGTH('dbo.VisitTask','ScopeOrgUnitId') IS NULL ALTER TABLE dbo.VisitTask ADD ScopeOrgUnitId bigint NULL;
    IF COL_LENGTH('dbo.VisitTask','ScopeNameSnapshot') IS NULL ALTER TABLE dbo.VisitTask ADD ScopeNameSnapshot nvarchar(100) NULL;
    IF COL_LENGTH('dbo.VisitTask','ScopeDealerCount') IS NULL ALTER TABLE dbo.VisitTask ADD ScopeDealerCount int NULL;
    IF COL_LENGTH('dbo.VisitTask','ScopeExecutionCount') IS NULL ALTER TABLE dbo.VisitTask ADD ScopeExecutionCount int NULL;

    EXEC(N';WITH ScopeStats AS
    (
        SELECT t.VisitTaskId,COUNT(DISTINCT e.DealerId) DealerCount,
               COUNT(DISTINCT e.TaskExecutionId) ExecutionCount,
               CASE WHEN COUNT(DISTINCT h.OrgUnitId)=1 THEN MIN(h.OrgUnitId) END OrgUnitId
          FROM dbo.VisitTask t
          LEFT JOIN dbo.VisitTaskExecution e ON e.VisitTaskId=t.VisitTaskId
          LEFT JOIN dbo.EmployeeOrgAssignmentHistory h ON h.EmployeeId=e.ResponsibleEmployeeId
           AND h.StartDateTime<DATEADD(day,1,CAST(t.ValidFrom AS datetime2))
           AND (h.EndDateTime IS NULL OR h.EndDateTime>=CAST(t.ValidFrom AS datetime2))
         GROUP BY t.VisitTaskId
    )
    UPDATE t SET ScopeOrgUnitId=s.OrgUnitId,
           ScopeNameSnapshot=CASE WHEN s.OrgUnitId IS NULL THEN N''全部有效經銷商'' ELSE o.OrgUnitName END,
           ScopeDealerCount=s.DealerCount,ScopeExecutionCount=s.ExecutionCount
      FROM dbo.VisitTask t JOIN ScopeStats s ON s.VisitTaskId=t.VisitTaskId
      LEFT JOIN dbo.OrganizationUnit o ON o.OrgUnitId=s.OrgUnitId
     WHERE t.ScopeNameSnapshot IS NULL OR t.ScopeDealerCount IS NULL OR t.ScopeExecutionCount IS NULL;');

    EXEC(N'IF EXISTS(SELECT 1 FROM dbo.VisitTask WHERE ScopeNameSnapshot IS NULL OR ScopeDealerCount IS NULL OR ScopeExecutionCount IS NULL)
        THROW 50001, N''VisitTask 範圍快照回填失敗。'', 1;');
    EXEC(N'ALTER TABLE dbo.VisitTask ALTER COLUMN ScopeNameSnapshot nvarchar(100) NOT NULL;');
    EXEC(N'ALTER TABLE dbo.VisitTask ALTER COLUMN ScopeDealerCount int NOT NULL;');
    EXEC(N'ALTER TABLE dbo.VisitTask ALTER COLUMN ScopeExecutionCount int NOT NULL;');
    IF NOT EXISTS(SELECT 1 FROM sys.foreign_keys WHERE name='FK_VisitTask_ScopeOrganization')
        EXEC(N'ALTER TABLE dbo.VisitTask ADD CONSTRAINT FK_VisitTask_ScopeOrganization FOREIGN KEY (ScopeOrgUnitId) REFERENCES dbo.OrganizationUnit(OrgUnitId);');
    IF NOT EXISTS(SELECT 1 FROM sys.check_constraints WHERE name='CK_VisitTask_ScopeCounts')
        EXEC(N'ALTER TABLE dbo.VisitTask ADD CONSTRAINT CK_VisitTask_ScopeCounts CHECK (ScopeDealerCount>=0 AND ScopeExecutionCount>=ScopeDealerCount);');
    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO

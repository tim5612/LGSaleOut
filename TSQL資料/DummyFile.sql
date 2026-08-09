/*
    LGSaleOut coherent development data.
    Run after CreateDB.sql. This script expects empty business tables.
*/

USE [LGSaleOut];
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;

IF EXISTS (SELECT 1 FROM dbo.Employee)
   OR EXISTS (SELECT 1 FROM dbo.OrganizationUnit)
   OR EXISTS (SELECT 1 FROM dbo.Dealer)
   OR EXISTS (SELECT 1 FROM dbo.Product)
   OR EXISTS (SELECT 1 FROM dbo.ImportBatch)
   OR EXISTS (SELECT 1 FROM dbo.VisitTask)
    THROW 50100, N'資料庫已有資料；請先執行 EraseDummy.sql，再執行 DummyFile.sql。', 1;

BEGIN TRY
    BEGIN TRANSACTION;

    /* Organization and employees */
    INSERT dbo.OrganizationUnit (OrgUnitCode, OrgUnitName, IsActive)
    VALUES ('TP01', N'台北一處', 1),
           ('HC01', N'新竹處', 1),
           ('TC01', N'台中處', 1);

    INSERT dbo.Employee (EmployeeNo, EmployeeName, HireDate, TerminationDate)
    VALUES (N'E0001', N'林怡君', '2022-01-03', NULL),
           (N'S0128', N'王小明', '2023-03-01', NULL),
           (N'S0096', N'李小華', '2021-08-16', NULL),
           (N'D0007', N'陳美玲', '2019-05-06', NULL),
           (N'S0144', N'張志豪', '2024-02-15', NULL),
           (N'S0066', N'周志明', '2020-04-01', '2026-06-30');

    DECLARE @Admin bigint = (SELECT EmployeeId FROM dbo.Employee WHERE EmployeeNo=N'E0001');
    DECLARE @Wang bigint = (SELECT EmployeeId FROM dbo.Employee WHERE EmployeeNo=N'S0128');
    DECLARE @Li bigint = (SELECT EmployeeId FROM dbo.Employee WHERE EmployeeNo=N'S0096');
    DECLARE @Chen bigint = (SELECT EmployeeId FROM dbo.Employee WHERE EmployeeNo=N'D0007');
    DECLARE @Zhang bigint = (SELECT EmployeeId FROM dbo.Employee WHERE EmployeeNo=N'S0144');
    DECLARE @Former bigint = (SELECT EmployeeId FROM dbo.Employee WHERE EmployeeNo=N'S0066');
    DECLARE @Taipei bigint = (SELECT OrgUnitId FROM dbo.OrganizationUnit WHERE OrgUnitCode='TP01');
    DECLARE @Hsinchu bigint = (SELECT OrgUnitId FROM dbo.OrganizationUnit WHERE OrgUnitCode='HC01');
    DECLARE @Taichung bigint = (SELECT OrgUnitId FROM dbo.OrganizationUnit WHERE OrgUnitCode='TC01');

    INSERT dbo.EmployeePositionHistory
        (EmployeeId, PositionLevel, StartDateTime, EndDateTime, ChangeReason, CreatedByEmployeeId)
    VALUES (@Admin, 'MANAGER', '2022-01-03', NULL, N'建立測試管理員', @Admin),
           (@Wang, 'SALES', '2023-03-01', NULL, N'建立業務職級', @Admin),
           (@Li, 'SALES', '2021-08-16', NULL, N'建立業務職級', @Admin),
           (@Chen, 'DIRECTOR', '2019-05-06', NULL, N'建立處長職級', @Admin),
           (@Zhang, 'SALES', '2024-02-15', NULL, N'建立業務職級', @Admin),
           (@Former, 'SALES', '2020-04-01', '2026-07-01', N'人員離職', @Admin);

    INSERT dbo.EmployeeOrgAssignmentHistory
        (EmployeeId, OrgUnitId, StartDateTime, EndDateTime, ChangeReason, CreatedByEmployeeId)
    VALUES (@Admin, @Taipei, '2022-01-03', NULL, N'建立處所歸屬', @Admin),
           (@Wang, @Taipei, '2023-03-01', NULL, N'建立處所歸屬', @Admin),
           (@Li, @Taipei, '2021-08-16', NULL, N'建立處所歸屬', @Admin),
           (@Chen, @Taipei, '2019-05-06', NULL, N'建立處所歸屬', @Admin),
           (@Zhang, @Hsinchu, '2024-02-15', NULL, N'建立處所歸屬', @Admin),
           (@Former, @Taichung, '2020-04-01', '2026-07-01', N'人員離職', @Admin);

    /* Dealers, levels and current/historical assignments */
    INSERT dbo.Dealer (DealerCode, DealerName)
    VALUES ('D1024', N'光華家電'), ('D1088', N'三民電器'),
           ('D1142', N'東區生活館'), ('D1201', N'宏達通訊'),
           ('D1260', N'北門冷氣行'), ('D1305', N'中原生活館');

    DECLARE @D1 bigint=(SELECT DealerId FROM dbo.Dealer WHERE DealerCode='D1024');
    DECLARE @D2 bigint=(SELECT DealerId FROM dbo.Dealer WHERE DealerCode='D1088');
    DECLARE @D3 bigint=(SELECT DealerId FROM dbo.Dealer WHERE DealerCode='D1142');
    DECLARE @D4 bigint=(SELECT DealerId FROM dbo.Dealer WHERE DealerCode='D1201');
    DECLARE @D5 bigint=(SELECT DealerId FROM dbo.Dealer WHERE DealerCode='D1260');
    DECLARE @D6 bigint=(SELECT DealerId FROM dbo.Dealer WHERE DealerCode='D1305');

    INSERT dbo.DealerLevelHistory (DealerId, DealerStatus, StartDateTime, EndDateTime, ChangeReason)
    VALUES (@D1,'A','2024-01-01',NULL,N'重點經銷商'),
           (@D2,'B','2024-01-01',NULL,N'一般經銷商'),
           (@D3,'C','2024-01-01',NULL,N'一般經銷商'),
           (@D4,'D','2024-01-01',NULL,N'觀察名單'),
           (@D5,'E','2024-01-01',NULL,N'低頻交易'),
           (@D6,'Z','2024-01-01',NULL,N'停止經銷');

    INSERT dbo.DealerAssignmentHistory
        (DealerId, EmployeeId, StartDateTime, EndDateTime, ChangeReason, CreatedByEmployeeId)
    VALUES (@D1,@Former,'2025-01-01','2026-07-01',N'原負責人離職',@Admin),
           (@D1,@Wang,'2026-07-01',NULL,N'接手經銷商',@Admin),
           (@D2,@Wang,'2025-01-01',NULL,N'建立負責關係',@Admin),
           (@D3,@Zhang,'2025-01-01',NULL,N'建立負責關係',@Admin),
           (@D4,@Li,'2025-01-01',NULL,N'建立負責關係',@Admin),
           (@D5,@Chen,'2025-01-01',NULL,N'處長直接負責',@Admin),
           (@D6,@Li,'2025-01-01',NULL,N'保留結束經銷商歷史',@Admin);

    DECLARE @A1 bigint=(SELECT DealerAssignmentId FROM dbo.DealerAssignmentHistory WHERE DealerId=@D1 AND EndDateTime IS NULL);
    DECLARE @A2 bigint=(SELECT DealerAssignmentId FROM dbo.DealerAssignmentHistory WHERE DealerId=@D2 AND EndDateTime IS NULL);
    DECLARE @A3 bigint=(SELECT DealerAssignmentId FROM dbo.DealerAssignmentHistory WHERE DealerId=@D3 AND EndDateTime IS NULL);

    /* Shared application accounts and sample WebAuthn records */
    INSERT dbo.UserAccount (AccountType, EmployeeId, DealerId, IsLoginEnabled, AccountStatus)
    SELECT 'EMPLOYEE', EmployeeId, NULL, CASE WHEN TerminationDate IS NULL THEN 1 ELSE 0 END,
           CASE WHEN TerminationDate IS NULL THEN 'ACTIVE' ELSE 'DISABLED' END
    FROM dbo.Employee;

    INSERT dbo.UserAccount (AccountType, EmployeeId, DealerId, IsLoginEnabled, AccountStatus)
    SELECT 'DEALER', NULL, DealerId, CASE WHEN DealerId=@D6 THEN 0 ELSE 1 END,
           CASE WHEN DealerId=@D6 THEN 'DISABLED' ELSE 'ACTIVE' END
    FROM dbo.Dealer;

    DECLARE @AdminAccount bigint=(SELECT UserAccountId FROM dbo.UserAccount WHERE EmployeeId=@Admin);
    DECLARE @WangAccount bigint=(SELECT UserAccountId FROM dbo.UserAccount WHERE EmployeeId=@Wang);
    DECLARE @DealerAccount bigint=(SELECT UserAccountId FROM dbo.UserAccount WHERE DealerId=@D2);

    INSERT dbo.PasskeyCredential
        (UserAccountId, CredentialId, PublicKey, SignCount, Transports, DeviceName, LastUsedAt)
    VALUES (@AdminAccount,HASHBYTES('SHA2_256','dummy-admin-passkey'),0x010203040506,12,'internal,hybrid',N'林怡君的 Windows Hello','2026-08-08 09:12'),
           (@WangAccount,HASHBYTES('SHA2_256','dummy-wang-passkey'),0x111213141516,3,'internal',N'王小明的 iPhone','2026-08-07 17:30'),
           (@DealerAccount,HASHBYTES('SHA2_256','dummy-dealer-passkey'),0x212223242526,0,'hybrid',N'三民電器店用手機',NULL);

    INSERT dbo.PasskeyRegistrationInvitation
        (UserAccountId, TokenHash, ExpiresAt, CreatedAt, CreatedByEmployeeId)
    VALUES ((SELECT UserAccountId FROM dbo.UserAccount WHERE DealerId=@D5),
            HASHBYTES('SHA2_256','dummy-invitation'), '2026-08-20', '2026-08-05', @Admin);

    /* Products and inventory/import facts */
    INSERT dbo.Product (ProductCode, ProductName, CategoryLevel1, CategoryLevel2, IsActive)
    VALUES ('P-FR-001',N'雙門變頻冰箱 500L',N'冰箱',N'雙門',1),
           ('P-FR-002',N'鏡面多門冰箱 600L',N'冰箱',N'多門',1),
           ('P-AC-001',N'一對一變頻冷氣 3.6kW',N'空調',N'分離式',1),
           ('P-WM-001',N'滾筒洗衣機 15kg',N'洗衣機',N'滾筒',1),
           ('P-TV-001',N'65 吋智慧電視',N'電視',N'OLED',1);

    DECLARE @P1 bigint=(SELECT ProductId FROM dbo.Product WHERE ProductCode='P-FR-001');
    DECLARE @P2 bigint=(SELECT ProductId FROM dbo.Product WHERE ProductCode='P-FR-002');
    DECLARE @P3 bigint=(SELECT ProductId FROM dbo.Product WHERE ProductCode='P-AC-001');
    DECLARE @P4 bigint=(SELECT ProductId FROM dbo.Product WHERE ProductCode='P-WM-001');

    INSERT dbo.OpeningInventoryProductExclusion
        (ProductId, ScopeType, DealerId, EffectiveFromMonth, EffectiveToMonth, ExclusionReason, CreatedByEmployeeId)
    VALUES (@P4,'ALL',NULL,'202608',NULL,N'洗衣機暫不納入期初庫存',@Admin),
           (@P3,'DEALER',@D5,'202608','202609',N'指定經銷商測試排除',@Admin);

    INSERT dbo.ImportBatch
        (ImportType,DataMonth,DataDate,OriginalFileName,StoredFilePath,FileHash,FileSize,ImportStatus,TotalRowCount,SuccessRowCount,ErrorRowCount,ImportedAt,ImportedByEmployeeId)
    VALUES ('OPENING_INVENTORY','202608',NULL,N'202608期初庫存.xlsx',N'/dummy/import/202608-opening.xlsx','DUMMY-HASH-OPENING',20480,'Official',6,6,0,'2026-08-01 08:00',@Admin),
           ('SELL_IN',NULL,'2026-08-05',N'20260805進貨.xlsx',N'/dummy/import/20260805-sellin.xlsx','DUMMY-HASH-SELLIN',12288,'Official',4,4,0,'2026-08-05 18:00',@Admin);

    DECLARE @OpeningBatch bigint=(SELECT ImportBatchId FROM dbo.ImportBatch WHERE FileHash='DUMMY-HASH-OPENING');
    DECLARE @SellInBatch bigint=(SELECT ImportBatchId FROM dbo.ImportBatch WHERE FileHash='DUMMY-HASH-SELLIN');

    INSERT dbo.MonthlyOpeningInventoryDetail
        (ImportBatchId,SourceRowNumber,DealerId,ProductId,OpeningQuantity)
    VALUES (@OpeningBatch,2,@D1,@P1,8),(@OpeningBatch,3,@D1,@P2,5),
           (@OpeningBatch,4,@D2,@P1,6),(@OpeningBatch,5,@D2,@P3,4),
           (@OpeningBatch,6,@D3,@P2,3),(@OpeningBatch,7,@D4,@P3,7);

    INSERT dbo.SellInTransaction
        (ImportBatchId,SourceRowNumber,DealerId,ProductId,SalesDocumentNo,SalesDocumentItemNo,InvoiceNo,OrderDate,BillingDate,InvoiceDate,InventoryEffectiveDate,Quantity,TransactionType,TransactionStatus,ReviewStatus)
    VALUES (@SellInBatch,2,@D1,@P1,'SO-DUMMY-001','10','INV-DUMMY-001','2026-08-03','2026-08-05','2026-08-05','2026-08-05',3,'SALE','VALID','APPROVED'),
           (@SellInBatch,3,@D2,@P3,'SO-DUMMY-002','10','INV-DUMMY-002','2026-08-03','2026-08-05','2026-08-05','2026-08-05',2,'SALE','VALID','APPROVED'),
           (@SellInBatch,4,@D3,@P2,'SO-DUMMY-003','10','INV-DUMMY-003','2026-08-04','2026-08-05','2026-08-05','2026-08-05',4,'SALE','VALID','APPROVED'),
           (@SellInBatch,5,@D1,@P1,'SO-DUMMY-004','10','CN-DUMMY-001','2026-08-05','2026-08-06','2026-08-06','2026-08-06',-1,'RETURN','VALID','APPROVED');

    /* Employee-entered and dealer-entered visit reports */
    INSERT dbo.StoreVisit
        (DealerId,DealerAssignmentId,EntrySourceType,ReportDateTime,RecordStatus,CreatedAt,CreatedByUserAccountId)
    VALUES (@D1,@A1,'EMPLOYEE','2026-08-06 15:20','ACTIVE','2026-08-06 15:20',@WangAccount),
           (@D2,@A2,'DEALER','2026-08-07 11:10','ACTIVE','2026-08-07 11:10',@DealerAccount),
           (@D3,@A3,'EMPLOYEE','2026-07-30 14:00','VOIDED','2026-07-30 14:00',(SELECT UserAccountId FROM dbo.UserAccount WHERE EmployeeId=@Zhang));

    DECLARE @V1 bigint=(SELECT StoreVisitId FROM dbo.StoreVisit WHERE DealerId=@D1 AND ReportDateTime='2026-08-06 15:20');
    DECLARE @V2 bigint=(SELECT StoreVisitId FROM dbo.StoreVisit WHERE DealerId=@D2 AND ReportDateTime='2026-08-07 11:10');
    DECLARE @V3 bigint=(SELECT StoreVisitId FROM dbo.StoreVisit WHERE DealerId=@D3 AND ReportDateTime='2026-07-30 14:00');

    INSERT dbo.StoreVisitProductDetail
        (StoreVisitId,ProductId,SellOutQuantity,SellOutDate,DisplayQuantity)
    VALUES (@V1,@P1,2,'2026-08-06',1),(@V1,@P2,NULL,NULL,1),
           (@V2,@P1,1,'2026-08-07',NULL),(@V3,@P2,3,'2026-07-30',1);

    /* Task states: approved sample, awaiting sample, future and voided */
    INSERT dbo.VisitTask
        (TaskTitle,Instruction,ValidFrom,DueDate,RecordStatus,CreatedByEmployeeId)
    VALUES (N'新機上市展示布置',N'依序拍攝跳跳牌、製冰盒與鏡面烤漆區域。','2026-08-05','2026-08-16','ACTIVE',@Admin),
           (N'夏季冰箱清潔檢查',N'清潔並拍攝冰箱內外觀。','2026-08-08','2026-08-22','ACTIVE',@Chen),
           (N'九月冷氣 POP 更新',N'更新指定 POP 並拍照。','2026-09-01','2026-09-10','ACTIVE',@Admin),
           (N'已取消的舊版陳列任務',N'測試作廢任務。','2026-07-01','2026-07-10','VOIDED',@Admin);

    DECLARE @T1 bigint=(SELECT VisitTaskId FROM dbo.VisitTask WHERE TaskTitle=N'新機上市展示布置');
    DECLARE @T2 bigint=(SELECT VisitTaskId FROM dbo.VisitTask WHERE TaskTitle=N'夏季冰箱清潔檢查');
    DECLARE @T3 bigint=(SELECT VisitTaskId FROM dbo.VisitTask WHERE TaskTitle=N'九月冷氣 POP 更新');
    DECLARE @T4 bigint=(SELECT VisitTaskId FROM dbo.VisitTask WHERE TaskTitle=N'已取消的舊版陳列任務');

    INSERT dbo.VisitTaskExecution
        (VisitTaskId,DealerId,ResponsibleEmployeeId,CompletedByEmployeeId,ExecutionNote,SubmittedAt)
    VALUES (@T1,@D1,@Wang,@Wang,NULL,'2026-08-06 16:00'),
           (@T1,@D2,@Wang,NULL,NULL,NULL),
           (@T1,@D3,@Zhang,@Zhang,NULL,'2026-08-07 13:30'),
           (@T2,@D1,@Wang,@Wang,N'現場施工，無法拍照。','2026-08-09 10:00'),
           (@T2,@D2,@Wang,NULL,NULL,NULL),
           (@T3,@D4,@Li,NULL,NULL,NULL),
           (@T4,@D5,@Chen,NULL,NULL,NULL);

    DECLARE @E11 bigint=(SELECT TaskExecutionId FROM dbo.VisitTaskExecution WHERE VisitTaskId=@T1 AND DealerId=@D1);
    DECLARE @E13 bigint=(SELECT TaskExecutionId FROM dbo.VisitTaskExecution WHERE VisitTaskId=@T1 AND DealerId=@D3);

    INSERT dbo.VisitTaskPhoto
        (TaskExecutionId,SampleTaskPhotoId,PhotoDescription,StoredFileName,StoredFilePath,CapturedAt,SortOrder,UploadedAt)
    VALUES (@E11,NULL,N'跳跳牌照片',N'dummy-sample-01.jpg',N'/dummy/task/sample-01.jpg','2026-08-06 15:40',1,'2026-08-06 15:41'),
           (@E11,NULL,N'製冰盒照片',N'dummy-sample-02.jpg',N'/dummy/task/sample-02.jpg','2026-08-06 15:42',2,'2026-08-06 15:43'),
           (@E11,NULL,N'鏡面烤漆照片',N'dummy-sample-03.jpg',N'/dummy/task/sample-03.jpg','2026-08-06 15:44',3,'2026-08-06 15:45');

    DECLARE @SP1 bigint=(SELECT TaskPhotoId FROM dbo.VisitTaskPhoto WHERE TaskExecutionId=@E11 AND SortOrder=1);
    DECLARE @SP2 bigint=(SELECT TaskPhotoId FROM dbo.VisitTaskPhoto WHERE TaskExecutionId=@E11 AND SortOrder=2);
    DECLARE @SP3 bigint=(SELECT TaskPhotoId FROM dbo.VisitTaskPhoto WHERE TaskExecutionId=@E11 AND SortOrder=3);

    INSERT dbo.VisitTaskPhoto
        (TaskExecutionId,SampleTaskPhotoId,PhotoDescription,StoredFileName,StoredFilePath,CapturedAt,SortOrder,UploadedAt)
    VALUES (@E13,@SP1,NULL,N'dummy-general-01.jpg',N'/dummy/task/general-01.jpg','2026-08-07 13:10',1,'2026-08-07 13:11'),
           (@E13,@SP2,NULL,N'dummy-general-02.jpg',N'/dummy/task/general-02.jpg','2026-08-07 13:12',2,'2026-08-07 13:13'),
           (@E13,@SP3,NULL,N'dummy-general-03.jpg',N'/dummy/task/general-03.jpg','2026-08-07 13:14',3,'2026-08-07 13:15');

    UPDATE dbo.VisitTask
       SET SampleTaskExecutionId=@E11,
           SampleApprovedByEmployeeId=@Chen,
           SampleApprovedAt='2026-08-06 17:00',
           UpdatedByEmployeeId=@Chen,
           UpdatedAt='2026-08-06 17:00'
     WHERE VisitTaskId=@T1;

    COMMIT TRANSACTION;

    SELECT N'Dummy data created' AS Result,
           (SELECT COUNT(*) FROM dbo.Employee) AS Employees,
           (SELECT COUNT(*) FROM dbo.Dealer) AS Dealers,
           (SELECT COUNT(*) FROM dbo.Product) AS Products,
           (SELECT COUNT(*) FROM dbo.VisitTask) AS VisitTasks;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO

/*
    Grant the existing SQL login [Tim] access to LGSaleOut.
    Run this script using a sysadmin account in SSMS.
*/

USE [master];
GO

IF DB_ID(N'LGSaleOut') IS NULL
BEGIN
    THROW 50001, N'找不到資料庫 LGSaleOut，請先執行 Create_LGSaleOut.sql。', 1;
END;
GO

IF SUSER_ID(N'Tim') IS NULL
BEGIN
    CREATE LOGIN [Tim]
        WITH PASSWORD = N'561202',
             CHECK_POLICY = OFF,
             CHECK_EXPIRATION = OFF,
             DEFAULT_DATABASE = [LGSaleOut];
END
ELSE
BEGIN
    ALTER LOGIN [Tim] WITH DEFAULT_DATABASE = [LGSaleOut];
    GRANT CONNECT SQL TO [Tim];
END;
GO

USE [LGSaleOut];
GO

IF USER_ID(N'Tim') IS NULL
BEGIN
    CREATE USER [Tim] FOR LOGIN [Tim] WITH DEFAULT_SCHEMA = [dbo];
END
ELSE
BEGIN
    ALTER USER [Tim] WITH LOGIN = [Tim], DEFAULT_SCHEMA = [dbo];
END;
GO

GRANT CONNECT TO [Tim];

IF IS_ROLEMEMBER(N'db_datareader', N'Tim') <> 1
    ALTER ROLE [db_datareader] ADD MEMBER [Tim];

IF IS_ROLEMEMBER(N'db_datawriter', N'Tim') <> 1
    ALTER ROLE [db_datawriter] ADD MEMBER [Tim];
GO

/* Verification --------------------------------------------------------- */
SELECT
    DB_NAME() AS DatabaseName,
    dp.name AS DatabaseUser,
    dp.type_desc AS UserType,
    dp.default_schema_name AS DefaultSchema
FROM sys.database_principals AS dp
WHERE dp.name = N'Tim';

SELECT
    role_principal.name AS RoleName,
    member_principal.name AS MemberName
FROM sys.database_role_members AS drm
INNER JOIN sys.database_principals AS role_principal
    ON role_principal.principal_id = drm.role_principal_id
INNER JOIN sys.database_principals AS member_principal
    ON member_principal.principal_id = drm.member_principal_id
WHERE member_principal.name = N'Tim';
GO

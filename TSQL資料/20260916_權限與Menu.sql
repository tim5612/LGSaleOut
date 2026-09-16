/* Role defaults remain in lgsale_permissions.py. These tables store only
   Designer changes, so new capabilities have a safe, reviewable default. */
CREATE TABLE dbo.PermissionRoleOverride (
    RoleCode varchar(20) NOT NULL,
    Capability varchar(80) NOT NULL,
    IsAllowed bit NOT NULL,
    UpdatedByUserAccountId bigint NOT NULL,
    UpdatedAt datetime2(0) NOT NULL CONSTRAINT DF_PermissionRoleOverride_UpdatedAt DEFAULT sysdatetime(),
    CONSTRAINT PK_PermissionRoleOverride PRIMARY KEY (RoleCode, Capability),
    CONSTRAINT FK_PermissionRoleOverride_Actor FOREIGN KEY (UpdatedByUserAccountId)
        REFERENCES dbo.UserAccount(UserAccountId)
);
GO
CREATE TABLE dbo.PermissionAccountOverride (
    UserAccountId bigint NOT NULL,
    Capability varchar(80) NOT NULL,
    IsAllowed bit NOT NULL,
    UpdatedByUserAccountId bigint NOT NULL,
    UpdatedAt datetime2(0) NOT NULL CONSTRAINT DF_PermissionAccountOverride_UpdatedAt DEFAULT sysdatetime(),
    CONSTRAINT PK_PermissionAccountOverride PRIMARY KEY (UserAccountId, Capability),
    CONSTRAINT FK_PermissionAccountOverride_Account FOREIGN KEY (UserAccountId)
        REFERENCES dbo.UserAccount(UserAccountId),
    CONSTRAINT FK_PermissionAccountOverride_Actor FOREIGN KEY (UpdatedByUserAccountId)
        REFERENCES dbo.UserAccount(UserAccountId)
);
GO
CREATE TABLE dbo.PermissionDesigner (
    UserAccountId bigint NOT NULL PRIMARY KEY,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_PermissionDesigner_CreatedAt DEFAULT sysdatetime(),
    CONSTRAINT FK_PermissionDesigner_Account FOREIGN KEY (UserAccountId)
        REFERENCES dbo.UserAccount(UserAccountId)
);
GO
CREATE TABLE dbo.PermissionAudit (
    PermissionAuditId bigint IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ActorUserAccountId bigint NOT NULL,
    SubjectType varchar(20) NOT NULL,
    SubjectId varchar(80) NOT NULL,
    Capability varchar(80) NOT NULL,
    OldValue bit NULL,
    NewValue bit NULL,
    ChangedAt datetime2(0) NOT NULL CONSTRAINT DF_PermissionAudit_ChangedAt DEFAULT sysdatetime(),
    CONSTRAINT FK_PermissionAudit_Actor FOREIGN KEY (ActorUserAccountId)
        REFERENCES dbo.UserAccount(UserAccountId)
);
GO
/* PermissionDesigner starts empty. The first successful EMPLOYEE Passkey login
   after database reset claims it atomically. Later logins cannot replace it.
   Keep Designer assignment out of the web permission editor. */

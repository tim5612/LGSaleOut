/* Global rollout switch. Existing photos and PSI history remain untouched. */
CREATE TABLE dbo.FeatureSetting (
    FeatureKey varchar(80) NOT NULL PRIMARY KEY,
    IsEnabled bit NOT NULL,
    UpdatedByUserAccountId bigint NULL,
    UpdatedAt datetime2(0) NOT NULL CONSTRAINT DF_FeatureSetting_UpdatedAt DEFAULT sysdatetime(),
    CONSTRAINT FK_FeatureSetting_Actor FOREIGN KEY (UpdatedByUserAccountId)
        REFERENCES dbo.UserAccount(UserAccountId)
);
GO
INSERT dbo.FeatureSetting(FeatureKey, IsEnabled)
VALUES ('display_photo', 0);
GO

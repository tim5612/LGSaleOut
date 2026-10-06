USE [LGSaleOut];
GO

/* Required global feature setting. Business and test data are intentionally absent. */
IF NOT EXISTS (
    SELECT 1
    FROM dbo.FeatureSetting
    WHERE FeatureKey = 'display_photo'
)
BEGIN
    INSERT dbo.FeatureSetting (FeatureKey, IsEnabled, UpdatedByUserAccountId)
    VALUES ('display_photo', 0, NULL);
END;
GO

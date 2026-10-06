/*
  LGSaleOut schema-only baseline
  Source: 127.0.0.1,49172 / LGSaleOut
  Generated: 2026-10-06 16:43:45 +08:00
  Contains no table data, SQL logins, database users, or permissions.
*/

/****** Cannot script Unresolved Entities : Server[@Name='VM240705SQLDEV']/Database[@Name='LGSaleOut']/UnresolvedEntity[@Name='inserted'] ******/
USE [LGSaleOut]
/****** Object:  Table [dbo].[VisitTaskPhoto]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[VisitTaskPhoto](
	[TaskPhotoId] [bigint] IDENTITY(1,1) NOT NULL,
	[TaskExecutionId] [bigint] NOT NULL,
	[SampleTaskPhotoId] [bigint] NULL,
	[PhotoDescription] [nvarchar](500) NULL,
	[StoredFileName] [nvarchar](260) NOT NULL,
	[StoredFilePath] [nvarchar](1000) NOT NULL,
	[CapturedAt] [datetime2](0) NOT NULL,
	[SortOrder] [int] NOT NULL,
	[UploadedAt] [datetime2](0) NOT NULL,
 CONSTRAINT [PK_VisitTaskPhoto] PRIMARY KEY CLUSTERED 
(
	[TaskPhotoId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[PermissionRoleOverride]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[PermissionRoleOverride](
	[RoleCode] [varchar](20) NOT NULL,
	[Capability] [varchar](80) NOT NULL,
	[IsAllowed] [bit] NOT NULL,
	[UpdatedByUserAccountId] [bigint] NOT NULL,
	[UpdatedAt] [datetime2](0) NOT NULL,
 CONSTRAINT [PK_PermissionRoleOverride] PRIMARY KEY CLUSTERED 
(
	[RoleCode] ASC,
	[Capability] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[PermissionDesigner]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[PermissionDesigner](
	[UserAccountId] [bigint] NOT NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[UserAccountId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[PermissionAudit]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[PermissionAudit](
	[PermissionAuditId] [bigint] IDENTITY(1,1) NOT NULL,
	[ActorUserAccountId] [bigint] NOT NULL,
	[SubjectType] [varchar](20) NOT NULL,
	[SubjectId] [varchar](80) NOT NULL,
	[Capability] [varchar](80) NOT NULL,
	[OldValue] [bit] NULL,
	[NewValue] [bit] NULL,
	[ChangedAt] [datetime2](0) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[PermissionAuditId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[PermissionAccountOverride]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[PermissionAccountOverride](
	[UserAccountId] [bigint] NOT NULL,
	[Capability] [varchar](80) NOT NULL,
	[IsAllowed] [bit] NOT NULL,
	[UpdatedByUserAccountId] [bigint] NOT NULL,
	[UpdatedAt] [datetime2](0) NOT NULL,
 CONSTRAINT [PK_PermissionAccountOverride] PRIMARY KEY CLUSTERED 
(
	[UserAccountId] ASC,
	[Capability] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[PasskeyCredential]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[PasskeyCredential](
	[PasskeyCredentialId] [bigint] IDENTITY(1,1) NOT NULL,
	[UserAccountId] [bigint] NOT NULL,
	[CredentialId] [varbinary](1024) NOT NULL,
	[PublicKey] [varbinary](max) NOT NULL,
	[SignCount] [bigint] NOT NULL,
	[Transports] [varchar](200) NULL,
	[DeviceName] [nvarchar](100) NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
	[LastUsedAt] [datetime2](0) NULL,
	[RevokedAt] [datetime2](0) NULL,
 CONSTRAINT [PK_PasskeyCredential] PRIMARY KEY CLUSTERED 
(
	[PasskeyCredentialId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_PasskeyCredential_CredentialId] UNIQUE NONCLUSTERED 
(
	[CredentialId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

/****** Object:  Table [dbo].[FeatureSetting]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[FeatureSetting](
	[FeatureKey] [varchar](80) NOT NULL,
	[IsEnabled] [bit] NOT NULL,
	[UpdatedByUserAccountId] [bigint] NULL,
	[UpdatedAt] [datetime2](0) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[FeatureKey] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[StoreVisit]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[StoreVisit](
	[StoreVisitId] [bigint] IDENTITY(1,1) NOT NULL,
	[DealerId] [bigint] NOT NULL,
	[DealerAssignmentId] [bigint] NULL,
	[EntrySourceType] [varchar](20) NOT NULL,
	[ReportDateTime] [datetime2](0) NOT NULL,
	[RecordStatus] [varchar](20) NOT NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
	[CreatedByUserAccountId] [bigint] NOT NULL,
	[UpdatedAt] [datetime2](0) NULL,
	[UpdatedByUserAccountId] [bigint] NULL,
	[DealerLocationId] [bigint] NOT NULL,
 CONSTRAINT [PK_StoreVisit] PRIMARY KEY CLUSTERED 
(
	[StoreVisitId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[DealerLocation]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[DealerLocation](
	[DealerLocationId] [bigint] IDENTITY(1,1) NOT NULL,
	[DealerId] [bigint] NOT NULL,
	[LocationName] [nvarchar](150) NOT NULL,
	[StreetAddress] [nvarchar](500) NULL,
	[ContactName] [nvarchar](100) NULL,
	[Phone] [nvarchar](30) NULL,
	[IsPrimary] [bit] NOT NULL,
	[IsActive] [bit] NOT NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
	[UpdatedAt] [datetime2](0) NULL,
 CONSTRAINT [PK_DealerLocation] PRIMARY KEY CLUSTERED 
(
	[DealerLocationId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_DealerLocation_LocationDealer] UNIQUE NONCLUSTERED 
(
	[DealerLocationId] ASC,
	[DealerId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[DealerLevelHistory]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[DealerLevelHistory](
	[DealerLevelHistoryId] [bigint] IDENTITY(1,1) NOT NULL,
	[DealerId] [bigint] NOT NULL,
	[DealerStatus] [nvarchar](20) NOT NULL,
	[StartDateTime] [datetime2](0) NOT NULL,
	[EndDateTime] [datetime2](0) NULL,
	[ChangeReason] [varchar](max) NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
 CONSTRAINT [PK_DealerLevelHistory] PRIMARY KEY CLUSTERED 
(
	[DealerLevelHistoryId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

/****** Object:  Table [dbo].[VisitTaskExecution]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[VisitTaskExecution](
	[TaskExecutionId] [bigint] IDENTITY(1,1) NOT NULL,
	[VisitTaskId] [bigint] NOT NULL,
	[DealerId] [bigint] NOT NULL,
	[ResponsibleEmployeeId] [bigint] NOT NULL,
	[CompletedByEmployeeId] [bigint] NULL,
	[ExecutionNote] [nvarchar](max) NULL,
	[SubmittedAt] [datetime2](0) NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
	[DealerLocationId] [bigint] NOT NULL,
 CONSTRAINT [PK_VisitTaskExecution] PRIMARY KEY CLUSTERED 
(
	[TaskExecutionId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_VisitTaskExecution_TaskExecution] UNIQUE NONCLUSTERED 
(
	[VisitTaskId] ASC,
	[TaskExecutionId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_VisitTaskExecution_TaskLocation] UNIQUE NONCLUSTERED 
(
	[VisitTaskId] ASC,
	[DealerLocationId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

/****** Object:  Table [dbo].[UserAccount]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[UserAccount](
	[UserAccountId] [bigint] IDENTITY(1,1) NOT NULL,
	[AccountType] [varchar](20) NOT NULL,
	[EmployeeId] [bigint] NULL,
	[DealerId] [bigint] NULL,
	[IsLoginEnabled] [bit] NOT NULL,
	[AccountStatus] [varchar](20) NOT NULL,
	[LastLoginAt] [datetime2](0) NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
 CONSTRAINT [PK_UserAccount] PRIMARY KEY CLUSTERED 
(
	[UserAccountId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[PasskeyRegistrationInvitation]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[PasskeyRegistrationInvitation](
	[InvitationId] [bigint] IDENTITY(1,1) NOT NULL,
	[UserAccountId] [bigint] NOT NULL,
	[TokenHash] [varbinary](64) NOT NULL,
	[ExpiresAt] [datetime2](0) NOT NULL,
	[UsedAt] [datetime2](0) NULL,
	[RevokedAt] [datetime2](0) NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
	[CreatedByEmployeeId] [bigint] NOT NULL,
 CONSTRAINT [PK_PasskeyRegistrationInvitation] PRIMARY KEY CLUSTERED 
(
	[InvitationId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_PasskeyRegistrationInvitation_TokenHash] UNIQUE NONCLUSTERED 
(
	[TokenHash] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[DealerAssignmentHistory]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[DealerAssignmentHistory](
	[DealerAssignmentId] [bigint] IDENTITY(1,1) NOT NULL,
	[DealerId] [bigint] NOT NULL,
	[EmployeeId] [bigint] NOT NULL,
	[StartDateTime] [datetime2](0) NOT NULL,
	[EndDateTime] [datetime2](0) NULL,
	[ChangeReason] [nvarchar](500) NOT NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
	[CreatedByEmployeeId] [bigint] NOT NULL,
 CONSTRAINT [PK_DealerAssignmentHistory] PRIMARY KEY CLUSTERED 
(
	[DealerAssignmentId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[Employee]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[Employee](
	[EmployeeId] [bigint] IDENTITY(1,1) NOT NULL,
	[EmployeeNo] [nvarchar](30) NOT NULL,
	[EmployeeName] [nvarchar](100) NOT NULL,
	[HireDate] [date] NOT NULL,
	[TerminationDate] [date] NULL,
 CONSTRAINT [PK_Employee] PRIMARY KEY CLUSTERED 
(
	[EmployeeId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_Employee_EmployeeNo] UNIQUE NONCLUSTERED 
(
	[EmployeeNo] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[Dealer]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[Dealer](
	[DealerId] [bigint] IDENTITY(1,1) NOT NULL,
	[DealerCode] [varchar](30) NOT NULL,
	[DealerName] [nvarchar](150) NOT NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
	[TaxId] [varchar](20) NULL,
	[Area] [nvarchar](100) NULL,
	[DealerCondition] [varchar](20) NOT NULL,
	[ShortName] [nvarchar](150) NULL,
	[ContactName] [nvarchar](100) NULL,
	[MobilePhone] [nvarchar](30) NULL,
	[CompanyPhone] [nvarchar](30) NULL,
	[PostalCode] [nvarchar](20) NULL,
	[StreetAddress] [nvarchar](500) NULL,
 CONSTRAINT [PK_Dealer] PRIMARY KEY CLUSTERED 
(
	[DealerId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_Dealer_DealerCode] UNIQUE NONCLUSTERED 
(
	[DealerCode] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[StoreVisitProductDetail]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[StoreVisitProductDetail](
	[StoreVisitProductDetailId] [bigint] IDENTITY(1,1) NOT NULL,
	[StoreVisitId] [bigint] NOT NULL,
	[ProductId] [bigint] NOT NULL,
	[SellOutQuantity] [int] NULL,
	[SellOutDate] [date] NULL,
	[DisplayQuantity] [int] NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
	[UpdatedAt] [datetime2](0) NULL,
 CONSTRAINT [PK_StoreVisitProductDetail] PRIMARY KEY CLUSTERED 
(
	[StoreVisitProductDetailId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_StoreVisitProductDetail] UNIQUE NONCLUSTERED 
(
	[StoreVisitId] ASC,
	[ProductId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[OpeningInventoryProductExclusion]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[OpeningInventoryProductExclusion](
	[ExclusionId] [bigint] IDENTITY(1,1) NOT NULL,
	[ProductId] [bigint] NOT NULL,
	[ScopeType] [varchar](20) NOT NULL,
	[DealerId] [bigint] NULL,
	[EffectiveFromMonth] [char](6) NOT NULL,
	[EffectiveToMonth] [char](6) NULL,
	[ExclusionReason] [nvarchar](500) NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
	[CreatedByEmployeeId] [bigint] NOT NULL,
 CONSTRAINT [PK_OpeningInventoryProductExclusion] PRIMARY KEY CLUSTERED 
(
	[ExclusionId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[DealerProductDisplayPhoto]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[DealerProductDisplayPhoto](
	[DisplayPhotoId] [bigint] IDENTITY(1,1) NOT NULL,
	[DataMonth] [char](6) NOT NULL,
	[DealerId] [bigint] NOT NULL,
	[ProductId] [bigint] NOT NULL,
	[SourceStoreVisitId] [bigint] NULL,
	[OriginalFileName] [nvarchar](260) NOT NULL,
	[OriginalFilePath] [nvarchar](1000) NOT NULL,
	[ThumbnailFilePath] [nvarchar](1000) NOT NULL,
	[OriginalFileSize] [int] NOT NULL,
	[ThumbnailFileSize] [int] NOT NULL,
	[FileHash] [char](64) NOT NULL,
	[CapturedAt] [datetime2](0) NOT NULL,
	[UploadedAt] [datetime2](0) NOT NULL,
	[UploadedByUserAccountId] [bigint] NOT NULL,
	[RecordStatus] [varchar](20) NOT NULL,
	[ReplacedPhotoId] [bigint] NULL,
	[OriginalDeletedAt] [datetime2](0) NULL,
	[DealerLocationId] [bigint] NOT NULL,
 CONSTRAINT [PK_DealerProductDisplayPhoto] PRIMARY KEY CLUSTERED 
(
	[DisplayPhotoId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[Product]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[Product](
	[ProductId] [bigint] IDENTITY(1,1) NOT NULL,
	[ProductCode] [varchar](50) NOT NULL,
	[ProductName] [nvarchar](200) NOT NULL,
	[CategoryLevel1] [nvarchar](100) NULL,
	[CategoryLevel2] [nvarchar](100) NULL,
	[IsActive] [bit] NOT NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
 CONSTRAINT [PK_Product] PRIMARY KEY CLUSTERED 
(
	[ProductId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_Product_ProductCode] UNIQUE NONCLUSTERED 
(
	[ProductCode] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[VisitTask]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[VisitTask](
	[VisitTaskId] [bigint] IDENTITY(1,1) NOT NULL,
	[TaskTitle] [nvarchar](200) NOT NULL,
	[Instruction] [nvarchar](max) NOT NULL,
	[ValidFrom] [date] NOT NULL,
	[DueDate] [date] NOT NULL,
	[RecordStatus] [varchar](20) NOT NULL,
	[SampleTaskExecutionId] [bigint] NULL,
	[SampleApprovedByEmployeeId] [bigint] NULL,
	[SampleApprovedAt] [datetime2](0) NULL,
	[CreatedByEmployeeId] [bigint] NOT NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
	[UpdatedByEmployeeId] [bigint] NULL,
	[UpdatedAt] [datetime2](0) NULL,
	[ScopeOrgUnitId] [bigint] NULL,
	[ScopeNameSnapshot] [nvarchar](100) NOT NULL,
	[ScopeDealerCount] [int] NOT NULL,
	[ScopeExecutionCount] [int] NOT NULL,
 CONSTRAINT [PK_VisitTask] PRIMARY KEY CLUSTERED 
(
	[VisitTaskId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_VisitTask_VisitTask_SampleExecution] UNIQUE NONCLUSTERED 
(
	[VisitTaskId] ASC,
	[SampleTaskExecutionId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

/****** Object:  Table [dbo].[DealerTransferReview]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[DealerTransferReview](
	[DealerTransferReviewId] [bigint] IDENTITY(1,1) NOT NULL,
	[DealerId] [bigint] NOT NULL,
	[SourceDealerAssignmentId] [bigint] NULL,
	[SourceEmployeeId] [bigint] NULL,
	[TriggerType] [varchar](30) NOT NULL,
	[FromOrgUnitId] [bigint] NULL,
	[ToOrgUnitId] [bigint] NULL,
	[TriggeredAt] [datetime2](0) NOT NULL,
	[ReviewStatus] [varchar](20) NOT NULL,
	[ResolvedEmployeeId] [bigint] NULL,
	[ResolvedAt] [datetime2](0) NULL,
	[ResolvedByEmployeeId] [bigint] NULL,
	[ResolutionNote] [nvarchar](500) NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
 CONSTRAINT [PK_DealerTransferReview] PRIMARY KEY CLUSTERED 
(
	[DealerTransferReviewId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[OrganizationUnit]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[OrganizationUnit](
	[OrgUnitId] [bigint] IDENTITY(1,1) NOT NULL,
	[OrgUnitCode] [varchar](30) NOT NULL,
	[OrgUnitName] [nvarchar](100) NOT NULL,
	[IsActive] [bit] NOT NULL,
 CONSTRAINT [PK_OrganizationUnit] PRIMARY KEY CLUSTERED 
(
	[OrgUnitId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_OrganizationUnit_OrgUnitCode] UNIQUE NONCLUSTERED 
(
	[OrgUnitCode] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[EmployeePositionHistory]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[EmployeePositionHistory](
	[EmployeePositionHistoryId] [bigint] IDENTITY(1,1) NOT NULL,
	[EmployeeId] [bigint] NOT NULL,
	[PositionLevel] [varchar](30) NOT NULL,
	[StartDateTime] [datetime2](0) NOT NULL,
	[EndDateTime] [datetime2](0) NULL,
	[ChangeReason] [nvarchar](500) NOT NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
	[CreatedByEmployeeId] [bigint] NOT NULL,
 CONSTRAINT [PK_EmployeePositionHistory] PRIMARY KEY CLUSTERED 
(
	[EmployeePositionHistoryId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[EmployeeOrgAssignmentHistory]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[EmployeeOrgAssignmentHistory](
	[EmployeeOrgAssignmentId] [bigint] IDENTITY(1,1) NOT NULL,
	[EmployeeId] [bigint] NOT NULL,
	[OrgUnitId] [bigint] NOT NULL,
	[StartDateTime] [datetime2](0) NOT NULL,
	[EndDateTime] [datetime2](0) NULL,
	[ChangeReason] [nvarchar](500) NOT NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
	[CreatedByEmployeeId] [bigint] NOT NULL,
 CONSTRAINT [PK_EmployeeOrgAssignmentHistory] PRIMARY KEY CLUSTERED 
(
	[EmployeeOrgAssignmentId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[SellInTransaction]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[SellInTransaction](
	[SellInTransactionId] [bigint] IDENTITY(1,1) NOT NULL,
	[ImportBatchId] [bigint] NOT NULL,
	[SourceRowNumber] [int] NOT NULL,
	[DealerId] [bigint] NOT NULL,
	[ProductId] [bigint] NOT NULL,
	[SalesDocumentNo] [varchar](50) NOT NULL,
	[SalesDocumentItemNo] [varchar](20) NOT NULL,
	[InvoiceNo] [varchar](50) NULL,
	[OrderDate] [date] NOT NULL,
	[BillingDate] [date] NOT NULL,
	[InvoiceDate] [date] NULL,
	[InventoryEffectiveDate] [date] NOT NULL,
	[Quantity] [decimal](18, 3) NOT NULL,
	[TransactionType] [varchar](20) NOT NULL,
	[TransactionStatus] [varchar](20) NOT NULL,
	[ReviewStatus] [varchar](20) NOT NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
	[UpdatedAt] [datetime2](0) NULL,
 CONSTRAINT [PK_SellInTransaction] PRIMARY KEY CLUSTERED 
(
	[SellInTransactionId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_SellInTransaction_DocumentItem] UNIQUE NONCLUSTERED 
(
	[SalesDocumentNo] ASC,
	[SalesDocumentItemNo] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[OpeningInventoryCorrection]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[OpeningInventoryCorrection](
	[CorrectionId] [bigint] IDENTITY(1,1) NOT NULL,
	[ImportBatchId] [bigint] NOT NULL,
	[OpeningInventoryDetailId] [bigint] NOT NULL,
	[SourceRowNumber] [int] NOT NULL,
	[PreviousQuantity] [int] NOT NULL,
	[NewQuantity] [int] NOT NULL,
	[CreatedAt] [datetime2](0) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[CorrectionId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_OpeningInventoryCorrection] UNIQUE NONCLUSTERED 
(
	[ImportBatchId] ASC,
	[OpeningInventoryDetailId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[MonthlyOpeningInventoryDetail]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[MonthlyOpeningInventoryDetail](
	[OpeningInventoryDetailId] [bigint] IDENTITY(1,1) NOT NULL,
	[ImportBatchId] [bigint] NOT NULL,
	[SourceRowNumber] [int] NOT NULL,
	[DealerId] [bigint] NOT NULL,
	[ProductId] [bigint] NOT NULL,
	[OpeningQuantity] [int] NOT NULL,
 CONSTRAINT [PK_MonthlyOpeningInventoryDetail] PRIMARY KEY CLUSTERED 
(
	[OpeningInventoryDetailId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_MonthlyOpeningInventoryDetail] UNIQUE NONCLUSTERED 
(
	[ImportBatchId] ASC,
	[DealerId] ASC,
	[ProductId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

/****** Object:  Table [dbo].[ImportBatch]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TABLE [dbo].[ImportBatch](
	[ImportBatchId] [bigint] IDENTITY(1,1) NOT NULL,
	[ImportType] [varchar](30) NOT NULL,
	[DataMonth] [char](6) NULL,
	[DataDate] [date] NULL,
	[OriginalFileName] [nvarchar](260) NOT NULL,
	[StoredFilePath] [nvarchar](1000) NOT NULL,
	[FileHash] [varchar](128) NOT NULL,
	[FileSize] [bigint] NOT NULL,
	[ImportStatus] [varchar](20) NOT NULL,
	[ReplacedBatchId] [bigint] NULL,
	[TotalRowCount] [int] NOT NULL,
	[SuccessRowCount] [int] NOT NULL,
	[ErrorRowCount] [int] NOT NULL,
	[ErrorSummary] [nvarchar](max) NULL,
	[ImportedAt] [datetime2](0) NOT NULL,
	[ImportedByEmployeeId] [bigint] NOT NULL,
 CONSTRAINT [PK_ImportBatch] PRIMARY KEY CLUSTERED 
(
	[ImportBatchId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

/****** Object:  Index [IX_VisitTaskPhoto_SampleTaskPhoto]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_VisitTaskPhoto_SampleTaskPhoto] ON [dbo].[VisitTaskPhoto]
(
	[SampleTaskPhotoId] ASC
)
WHERE ([SampleTaskPhotoId] IS NOT NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [IX_VisitTaskPhoto_TaskExecution]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_VisitTaskPhoto_TaskExecution] ON [dbo].[VisitTaskPhoto]
(
	[TaskExecutionId] ASC,
	[SortOrder] ASC,
	[TaskPhotoId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [IX_PasskeyCredential_UserAccount]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_PasskeyCredential_UserAccount] ON [dbo].[PasskeyCredential]
(
	[UserAccountId] ASC,
	[RevokedAt] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [IX_StoreVisit_DealerReportDate]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_StoreVisit_DealerReportDate] ON [dbo].[StoreVisit]
(
	[DealerId] ASC,
	[ReportDateTime] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [IX_StoreVisit_LocationReportDate]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_StoreVisit_LocationReportDate] ON [dbo].[StoreVisit]
(
	[DealerLocationId] ASC,
	[ReportDateTime] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [IX_DealerLocation_DealerActive]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_DealerLocation_DealerActive] ON [dbo].[DealerLocation]
(
	[DealerId] ASC,
	[IsActive] ASC,
	[DealerLocationId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [UX_DealerLocation_Primary]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE UNIQUE NONCLUSTERED INDEX [UX_DealerLocation_Primary] ON [dbo].[DealerLocation]
(
	[DealerId] ASC
)
WHERE ([IsPrimary]=(1))
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [IX_DealerLevelHistory_DealerPeriod]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_DealerLevelHistory_DealerPeriod] ON [dbo].[DealerLevelHistory]
(
	[DealerId] ASC,
	[StartDateTime] ASC,
	[EndDateTime] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [UX_DealerLevelHistory_Current]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE UNIQUE NONCLUSTERED INDEX [UX_DealerLevelHistory_Current] ON [dbo].[DealerLevelHistory]
(
	[DealerId] ASC
)
WHERE ([EndDateTime] IS NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [IX_VisitTaskExecution_Employee]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_VisitTaskExecution_Employee] ON [dbo].[VisitTaskExecution]
(
	[ResponsibleEmployeeId] ASC,
	[SubmittedAt] ASC,
	[VisitTaskId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [UX_UserAccount_Dealer]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE UNIQUE NONCLUSTERED INDEX [UX_UserAccount_Dealer] ON [dbo].[UserAccount]
(
	[DealerId] ASC
)
WHERE ([DealerId] IS NOT NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [UX_UserAccount_Employee]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE UNIQUE NONCLUSTERED INDEX [UX_UserAccount_Employee] ON [dbo].[UserAccount]
(
	[EmployeeId] ASC
)
WHERE ([EmployeeId] IS NOT NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [IX_PasskeyRegistrationInvitation_AccountExpiry]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_PasskeyRegistrationInvitation_AccountExpiry] ON [dbo].[PasskeyRegistrationInvitation]
(
	[UserAccountId] ASC,
	[ExpiresAt] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [IX_DealerAssignmentHistory_DealerPeriod]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_DealerAssignmentHistory_DealerPeriod] ON [dbo].[DealerAssignmentHistory]
(
	[DealerId] ASC,
	[StartDateTime] ASC,
	[EndDateTime] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [UX_DealerAssignmentHistory_Current]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE UNIQUE NONCLUSTERED INDEX [UX_DealerAssignmentHistory_Current] ON [dbo].[DealerAssignmentHistory]
(
	[DealerId] ASC
)
WHERE ([EndDateTime] IS NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [IX_StoreVisitProductDetail_Product]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_StoreVisitProductDetail_Product] ON [dbo].[StoreVisitProductDetail]
(
	[ProductId] ASC,
	[StoreVisitId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
SET ANSI_PADDING ON

/****** Object:  Index [IX_OpeningInventoryProductExclusion_EffectivePeriod]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_OpeningInventoryProductExclusion_EffectivePeriod] ON [dbo].[OpeningInventoryProductExclusion]
(
	[ProductId] ASC,
	[DealerId] ASC,
	[EffectiveFromMonth] ASC,
	[EffectiveToMonth] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
SET ANSI_PADDING ON

/****** Object:  Index [UX_OpeningInventoryProductExclusion_All]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE UNIQUE NONCLUSTERED INDEX [UX_OpeningInventoryProductExclusion_All] ON [dbo].[OpeningInventoryProductExclusion]
(
	[ProductId] ASC,
	[EffectiveFromMonth] ASC
)
WHERE ([ScopeType]='ALL')
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
SET ANSI_PADDING ON

/****** Object:  Index [UX_OpeningInventoryProductExclusion_Dealer]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE UNIQUE NONCLUSTERED INDEX [UX_OpeningInventoryProductExclusion_Dealer] ON [dbo].[OpeningInventoryProductExclusion]
(
	[DealerId] ASC,
	[ProductId] ASC,
	[EffectiveFromMonth] ASC
)
WHERE ([ScopeType]='DEALER')
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
SET ANSI_PADDING ON

/****** Object:  Index [IX_DealerProductDisplayPhoto_Psi]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_DealerProductDisplayPhoto_Psi] ON [dbo].[DealerProductDisplayPhoto]
(
	[DataMonth] ASC,
	[DealerId] ASC,
	[ProductId] ASC,
	[DealerLocationId] ASC,
	[RecordStatus] ASC
)
INCLUDE([ThumbnailFilePath],[CapturedAt],[UploadedByUserAccountId]) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
SET ANSI_PADDING ON

/****** Object:  Index [UX_DealerProductDisplayPhoto_Current]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE UNIQUE NONCLUSTERED INDEX [UX_DealerProductDisplayPhoto_Current] ON [dbo].[DealerProductDisplayPhoto]
(
	[DataMonth] ASC,
	[DealerLocationId] ASC,
	[ProductId] ASC
)
WHERE ([RecordStatus]='ACTIVE')
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [UX_VisitTask_SampleTaskExecution]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE UNIQUE NONCLUSTERED INDEX [UX_VisitTask_SampleTaskExecution] ON [dbo].[VisitTask]
(
	[SampleTaskExecutionId] ASC
)
WHERE ([SampleTaskExecutionId] IS NOT NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [UX_DealerTransferReview_Open]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE UNIQUE NONCLUSTERED INDEX [UX_DealerTransferReview_Open] ON [dbo].[DealerTransferReview]
(
	[DealerId] ASC
)
WHERE ([ReviewStatus]='OPEN')
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [IX_EmployeePositionHistory_EmployeePeriod]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_EmployeePositionHistory_EmployeePeriod] ON [dbo].[EmployeePositionHistory]
(
	[EmployeeId] ASC,
	[StartDateTime] ASC,
	[EndDateTime] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [UX_EmployeePositionHistory_Current]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE UNIQUE NONCLUSTERED INDEX [UX_EmployeePositionHistory_Current] ON [dbo].[EmployeePositionHistory]
(
	[EmployeeId] ASC
)
WHERE ([EndDateTime] IS NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [IX_EmployeeOrgAssignmentHistory_EmployeePeriod]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_EmployeeOrgAssignmentHistory_EmployeePeriod] ON [dbo].[EmployeeOrgAssignmentHistory]
(
	[EmployeeId] ASC,
	[StartDateTime] ASC,
	[EndDateTime] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [UX_EmployeeOrgAssignmentHistory_Current]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE UNIQUE NONCLUSTERED INDEX [UX_EmployeeOrgAssignmentHistory_Current] ON [dbo].[EmployeeOrgAssignmentHistory]
(
	[EmployeeId] ASC
)
WHERE ([EndDateTime] IS NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [IX_SellInTransaction_ImportBatch]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_SellInTransaction_ImportBatch] ON [dbo].[SellInTransaction]
(
	[ImportBatchId] ASC,
	[SourceRowNumber] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [IX_SellInTransaction_Inventory]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_SellInTransaction_Inventory] ON [dbo].[SellInTransaction]
(
	[DealerId] ASC,
	[ProductId] ASC,
	[InventoryEffectiveDate] ASC
)
INCLUDE([Quantity],[TransactionStatus],[ReviewStatus]) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
/****** Object:  Index [IX_MonthlyOpeningInventoryDetail_DealerProduct]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_MonthlyOpeningInventoryDetail_DealerProduct] ON [dbo].[MonthlyOpeningInventoryDetail]
(
	[DealerId] ASC,
	[ProductId] ASC,
	[ImportBatchId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
SET ANSI_PADDING ON

/****** Object:  Index [IX_ImportBatch_TypePeriod]    Script Date: 2026/10/6 下午 04:43:45 ******/
CREATE NONCLUSTERED INDEX [IX_ImportBatch_TypePeriod] ON [dbo].[ImportBatch]
(
	[ImportType] ASC,
	[DataMonth] ASC,
	[DataDate] ASC,
	[ImportStatus] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
ALTER TABLE [dbo].[VisitTaskPhoto] ADD  CONSTRAINT [DF_VisitTaskPhoto_SortOrder]  DEFAULT ((0)) FOR [SortOrder]
ALTER TABLE [dbo].[VisitTaskPhoto] ADD  CONSTRAINT [DF_VisitTaskPhoto_UploadedAt]  DEFAULT (sysdatetime()) FOR [UploadedAt]
ALTER TABLE [dbo].[PermissionRoleOverride] ADD  CONSTRAINT [DF_PermissionRoleOverride_UpdatedAt]  DEFAULT (sysdatetime()) FOR [UpdatedAt]
ALTER TABLE [dbo].[PermissionDesigner] ADD  CONSTRAINT [DF_PermissionDesigner_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[PermissionAudit] ADD  CONSTRAINT [DF_PermissionAudit_ChangedAt]  DEFAULT (sysdatetime()) FOR [ChangedAt]
ALTER TABLE [dbo].[PermissionAccountOverride] ADD  CONSTRAINT [DF_PermissionAccountOverride_UpdatedAt]  DEFAULT (sysdatetime()) FOR [UpdatedAt]
ALTER TABLE [dbo].[PasskeyCredential] ADD  CONSTRAINT [DF_PasskeyCredential_SignCount]  DEFAULT ((0)) FOR [SignCount]
ALTER TABLE [dbo].[PasskeyCredential] ADD  CONSTRAINT [DF_PasskeyCredential_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[FeatureSetting] ADD  CONSTRAINT [DF_FeatureSetting_UpdatedAt]  DEFAULT (sysdatetime()) FOR [UpdatedAt]
ALTER TABLE [dbo].[StoreVisit] ADD  CONSTRAINT [DF_StoreVisit_ReportDateTime]  DEFAULT (sysdatetime()) FOR [ReportDateTime]
ALTER TABLE [dbo].[StoreVisit] ADD  CONSTRAINT [DF_StoreVisit_RecordStatus]  DEFAULT ('ACTIVE') FOR [RecordStatus]
ALTER TABLE [dbo].[StoreVisit] ADD  CONSTRAINT [DF_StoreVisit_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[DealerLocation] ADD  CONSTRAINT [DF_DealerLocation_IsPrimary]  DEFAULT ((0)) FOR [IsPrimary]
ALTER TABLE [dbo].[DealerLocation] ADD  CONSTRAINT [DF_DealerLocation_IsActive]  DEFAULT ((1)) FOR [IsActive]
ALTER TABLE [dbo].[DealerLocation] ADD  CONSTRAINT [DF_DealerLocation_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[DealerLevelHistory] ADD  CONSTRAINT [DF_DealerLevelHistory_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[VisitTaskExecution] ADD  CONSTRAINT [DF_VisitTaskExecution_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[UserAccount] ADD  CONSTRAINT [DF_UserAccount_IsLoginEnabled]  DEFAULT ((1)) FOR [IsLoginEnabled]
ALTER TABLE [dbo].[UserAccount] ADD  CONSTRAINT [DF_UserAccount_AccountStatus]  DEFAULT ('ACTIVE') FOR [AccountStatus]
ALTER TABLE [dbo].[UserAccount] ADD  CONSTRAINT [DF_UserAccount_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[PasskeyRegistrationInvitation] ADD  CONSTRAINT [DF_PasskeyRegistrationInvitation_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[DealerAssignmentHistory] ADD  CONSTRAINT [DF_DealerAssignmentHistory_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[Dealer] ADD  CONSTRAINT [DF_Dealer_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[Dealer] ADD  CONSTRAINT [DF_Dealer_Condition]  DEFAULT ('ACTIVE') FOR [DealerCondition]
ALTER TABLE [dbo].[StoreVisitProductDetail] ADD  CONSTRAINT [DF_StoreVisitProductDetail_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[OpeningInventoryProductExclusion] ADD  CONSTRAINT [DF_OpeningInventoryProductExclusion_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[DealerProductDisplayPhoto] ADD  CONSTRAINT [DF_DealerProductDisplayPhoto_UploadedAt]  DEFAULT (sysdatetime()) FOR [UploadedAt]
ALTER TABLE [dbo].[DealerProductDisplayPhoto] ADD  CONSTRAINT [DF_DealerProductDisplayPhoto_Status]  DEFAULT ('ACTIVE') FOR [RecordStatus]
ALTER TABLE [dbo].[Product] ADD  CONSTRAINT [DF_Product_IsActive]  DEFAULT ((1)) FOR [IsActive]
ALTER TABLE [dbo].[Product] ADD  CONSTRAINT [DF_Product_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[VisitTask] ADD  CONSTRAINT [DF_VisitTask_RecordStatus]  DEFAULT ('ACTIVE') FOR [RecordStatus]
ALTER TABLE [dbo].[VisitTask] ADD  CONSTRAINT [DF_VisitTask_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[DealerTransferReview] ADD  CONSTRAINT [DF_DealerTransferReview_Status]  DEFAULT ('OPEN') FOR [ReviewStatus]
ALTER TABLE [dbo].[DealerTransferReview] ADD  CONSTRAINT [DF_DealerTransferReview_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[OrganizationUnit] ADD  CONSTRAINT [DF_OrganizationUnit_IsActive]  DEFAULT ((1)) FOR [IsActive]
ALTER TABLE [dbo].[EmployeePositionHistory] ADD  CONSTRAINT [DF_EmployeePositionHistory_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[EmployeeOrgAssignmentHistory] ADD  CONSTRAINT [DF_EmployeeOrgAssignmentHistory_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[SellInTransaction] ADD  CONSTRAINT [DF_SellInTransaction_CreatedAt]  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[OpeningInventoryCorrection] ADD  DEFAULT (sysdatetime()) FOR [CreatedAt]
ALTER TABLE [dbo].[ImportBatch] ADD  CONSTRAINT [DF_ImportBatch_ImportStatus]  DEFAULT ('Processing') FOR [ImportStatus]
ALTER TABLE [dbo].[ImportBatch] ADD  CONSTRAINT [DF_ImportBatch_TotalRowCount]  DEFAULT ((0)) FOR [TotalRowCount]
ALTER TABLE [dbo].[ImportBatch] ADD  CONSTRAINT [DF_ImportBatch_SuccessRowCount]  DEFAULT ((0)) FOR [SuccessRowCount]
ALTER TABLE [dbo].[ImportBatch] ADD  CONSTRAINT [DF_ImportBatch_ErrorRowCount]  DEFAULT ((0)) FOR [ErrorRowCount]
ALTER TABLE [dbo].[ImportBatch] ADD  CONSTRAINT [DF_ImportBatch_ImportedAt]  DEFAULT (sysdatetime()) FOR [ImportedAt]
ALTER TABLE [dbo].[VisitTaskPhoto]  WITH CHECK ADD  CONSTRAINT [FK_VisitTaskPhoto_SampleTaskPhoto] FOREIGN KEY([SampleTaskPhotoId])
REFERENCES [dbo].[VisitTaskPhoto] ([TaskPhotoId])
ALTER TABLE [dbo].[VisitTaskPhoto] CHECK CONSTRAINT [FK_VisitTaskPhoto_SampleTaskPhoto]
ALTER TABLE [dbo].[VisitTaskPhoto]  WITH CHECK ADD  CONSTRAINT [FK_VisitTaskPhoto_TaskExecution] FOREIGN KEY([TaskExecutionId])
REFERENCES [dbo].[VisitTaskExecution] ([TaskExecutionId])
ALTER TABLE [dbo].[VisitTaskPhoto] CHECK CONSTRAINT [FK_VisitTaskPhoto_TaskExecution]
ALTER TABLE [dbo].[PermissionRoleOverride]  WITH CHECK ADD  CONSTRAINT [FK_PermissionRoleOverride_Actor] FOREIGN KEY([UpdatedByUserAccountId])
REFERENCES [dbo].[UserAccount] ([UserAccountId])
ALTER TABLE [dbo].[PermissionRoleOverride] CHECK CONSTRAINT [FK_PermissionRoleOverride_Actor]
ALTER TABLE [dbo].[PermissionDesigner]  WITH CHECK ADD  CONSTRAINT [FK_PermissionDesigner_Account] FOREIGN KEY([UserAccountId])
REFERENCES [dbo].[UserAccount] ([UserAccountId])
ALTER TABLE [dbo].[PermissionDesigner] CHECK CONSTRAINT [FK_PermissionDesigner_Account]
ALTER TABLE [dbo].[PermissionAudit]  WITH CHECK ADD  CONSTRAINT [FK_PermissionAudit_Actor] FOREIGN KEY([ActorUserAccountId])
REFERENCES [dbo].[UserAccount] ([UserAccountId])
ALTER TABLE [dbo].[PermissionAudit] CHECK CONSTRAINT [FK_PermissionAudit_Actor]
ALTER TABLE [dbo].[PermissionAccountOverride]  WITH CHECK ADD  CONSTRAINT [FK_PermissionAccountOverride_Account] FOREIGN KEY([UserAccountId])
REFERENCES [dbo].[UserAccount] ([UserAccountId])
ALTER TABLE [dbo].[PermissionAccountOverride] CHECK CONSTRAINT [FK_PermissionAccountOverride_Account]
ALTER TABLE [dbo].[PermissionAccountOverride]  WITH CHECK ADD  CONSTRAINT [FK_PermissionAccountOverride_Actor] FOREIGN KEY([UpdatedByUserAccountId])
REFERENCES [dbo].[UserAccount] ([UserAccountId])
ALTER TABLE [dbo].[PermissionAccountOverride] CHECK CONSTRAINT [FK_PermissionAccountOverride_Actor]
ALTER TABLE [dbo].[PasskeyCredential]  WITH CHECK ADD  CONSTRAINT [FK_PasskeyCredential_UserAccount] FOREIGN KEY([UserAccountId])
REFERENCES [dbo].[UserAccount] ([UserAccountId])
ALTER TABLE [dbo].[PasskeyCredential] CHECK CONSTRAINT [FK_PasskeyCredential_UserAccount]
ALTER TABLE [dbo].[FeatureSetting]  WITH CHECK ADD  CONSTRAINT [FK_FeatureSetting_Actor] FOREIGN KEY([UpdatedByUserAccountId])
REFERENCES [dbo].[UserAccount] ([UserAccountId])
ALTER TABLE [dbo].[FeatureSetting] CHECK CONSTRAINT [FK_FeatureSetting_Actor]
ALTER TABLE [dbo].[StoreVisit]  WITH CHECK ADD  CONSTRAINT [FK_StoreVisit_CreatedByUserAccount] FOREIGN KEY([CreatedByUserAccountId])
REFERENCES [dbo].[UserAccount] ([UserAccountId])
ALTER TABLE [dbo].[StoreVisit] CHECK CONSTRAINT [FK_StoreVisit_CreatedByUserAccount]
ALTER TABLE [dbo].[StoreVisit]  WITH CHECK ADD  CONSTRAINT [FK_StoreVisit_Dealer] FOREIGN KEY([DealerId])
REFERENCES [dbo].[Dealer] ([DealerId])
ALTER TABLE [dbo].[StoreVisit] CHECK CONSTRAINT [FK_StoreVisit_Dealer]
ALTER TABLE [dbo].[StoreVisit]  WITH CHECK ADD  CONSTRAINT [FK_StoreVisit_DealerAssignment] FOREIGN KEY([DealerAssignmentId])
REFERENCES [dbo].[DealerAssignmentHistory] ([DealerAssignmentId])
ALTER TABLE [dbo].[StoreVisit] CHECK CONSTRAINT [FK_StoreVisit_DealerAssignment]
ALTER TABLE [dbo].[StoreVisit]  WITH CHECK ADD  CONSTRAINT [FK_StoreVisit_DealerLocation] FOREIGN KEY([DealerLocationId], [DealerId])
REFERENCES [dbo].[DealerLocation] ([DealerLocationId], [DealerId])
ALTER TABLE [dbo].[StoreVisit] CHECK CONSTRAINT [FK_StoreVisit_DealerLocation]
ALTER TABLE [dbo].[StoreVisit]  WITH CHECK ADD  CONSTRAINT [FK_StoreVisit_UpdatedByUserAccount] FOREIGN KEY([UpdatedByUserAccountId])
REFERENCES [dbo].[UserAccount] ([UserAccountId])
ALTER TABLE [dbo].[StoreVisit] CHECK CONSTRAINT [FK_StoreVisit_UpdatedByUserAccount]
ALTER TABLE [dbo].[DealerLocation]  WITH CHECK ADD  CONSTRAINT [FK_DealerLocation_Dealer] FOREIGN KEY([DealerId])
REFERENCES [dbo].[Dealer] ([DealerId])
ALTER TABLE [dbo].[DealerLocation] CHECK CONSTRAINT [FK_DealerLocation_Dealer]
ALTER TABLE [dbo].[DealerLevelHistory]  WITH CHECK ADD  CONSTRAINT [FK_DealerLevelHistory_Dealer] FOREIGN KEY([DealerId])
REFERENCES [dbo].[Dealer] ([DealerId])
ALTER TABLE [dbo].[DealerLevelHistory] CHECK CONSTRAINT [FK_DealerLevelHistory_Dealer]
ALTER TABLE [dbo].[VisitTaskExecution]  WITH CHECK ADD  CONSTRAINT [FK_VisitTaskExecution_CompletedByEmployee] FOREIGN KEY([CompletedByEmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[VisitTaskExecution] CHECK CONSTRAINT [FK_VisitTaskExecution_CompletedByEmployee]
ALTER TABLE [dbo].[VisitTaskExecution]  WITH CHECK ADD  CONSTRAINT [FK_VisitTaskExecution_Dealer] FOREIGN KEY([DealerId])
REFERENCES [dbo].[Dealer] ([DealerId])
ALTER TABLE [dbo].[VisitTaskExecution] CHECK CONSTRAINT [FK_VisitTaskExecution_Dealer]
ALTER TABLE [dbo].[VisitTaskExecution]  WITH CHECK ADD  CONSTRAINT [FK_VisitTaskExecution_DealerLocation] FOREIGN KEY([DealerLocationId], [DealerId])
REFERENCES [dbo].[DealerLocation] ([DealerLocationId], [DealerId])
ALTER TABLE [dbo].[VisitTaskExecution] CHECK CONSTRAINT [FK_VisitTaskExecution_DealerLocation]
ALTER TABLE [dbo].[VisitTaskExecution]  WITH CHECK ADD  CONSTRAINT [FK_VisitTaskExecution_ResponsibleEmployee] FOREIGN KEY([ResponsibleEmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[VisitTaskExecution] CHECK CONSTRAINT [FK_VisitTaskExecution_ResponsibleEmployee]
ALTER TABLE [dbo].[VisitTaskExecution]  WITH CHECK ADD  CONSTRAINT [FK_VisitTaskExecution_VisitTask] FOREIGN KEY([VisitTaskId])
REFERENCES [dbo].[VisitTask] ([VisitTaskId])
ALTER TABLE [dbo].[VisitTaskExecution] CHECK CONSTRAINT [FK_VisitTaskExecution_VisitTask]
ALTER TABLE [dbo].[UserAccount]  WITH CHECK ADD  CONSTRAINT [FK_UserAccount_Dealer] FOREIGN KEY([DealerId])
REFERENCES [dbo].[Dealer] ([DealerId])
ALTER TABLE [dbo].[UserAccount] CHECK CONSTRAINT [FK_UserAccount_Dealer]
ALTER TABLE [dbo].[UserAccount]  WITH CHECK ADD  CONSTRAINT [FK_UserAccount_Employee] FOREIGN KEY([EmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[UserAccount] CHECK CONSTRAINT [FK_UserAccount_Employee]
ALTER TABLE [dbo].[PasskeyRegistrationInvitation]  WITH CHECK ADD  CONSTRAINT [FK_PasskeyRegistrationInvitation_CreatedByEmployee] FOREIGN KEY([CreatedByEmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[PasskeyRegistrationInvitation] CHECK CONSTRAINT [FK_PasskeyRegistrationInvitation_CreatedByEmployee]
ALTER TABLE [dbo].[PasskeyRegistrationInvitation]  WITH CHECK ADD  CONSTRAINT [FK_PasskeyRegistrationInvitation_UserAccount] FOREIGN KEY([UserAccountId])
REFERENCES [dbo].[UserAccount] ([UserAccountId])
ALTER TABLE [dbo].[PasskeyRegistrationInvitation] CHECK CONSTRAINT [FK_PasskeyRegistrationInvitation_UserAccount]
ALTER TABLE [dbo].[DealerAssignmentHistory]  WITH CHECK ADD  CONSTRAINT [FK_DealerAssignmentHistory_CreatedByEmployee] FOREIGN KEY([CreatedByEmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[DealerAssignmentHistory] CHECK CONSTRAINT [FK_DealerAssignmentHistory_CreatedByEmployee]
ALTER TABLE [dbo].[DealerAssignmentHistory]  WITH CHECK ADD  CONSTRAINT [FK_DealerAssignmentHistory_Dealer] FOREIGN KEY([DealerId])
REFERENCES [dbo].[Dealer] ([DealerId])
ALTER TABLE [dbo].[DealerAssignmentHistory] CHECK CONSTRAINT [FK_DealerAssignmentHistory_Dealer]
ALTER TABLE [dbo].[DealerAssignmentHistory]  WITH CHECK ADD  CONSTRAINT [FK_DealerAssignmentHistory_Employee] FOREIGN KEY([EmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[DealerAssignmentHistory] CHECK CONSTRAINT [FK_DealerAssignmentHistory_Employee]
ALTER TABLE [dbo].[StoreVisitProductDetail]  WITH CHECK ADD  CONSTRAINT [FK_StoreVisitProductDetail_Product] FOREIGN KEY([ProductId])
REFERENCES [dbo].[Product] ([ProductId])
ALTER TABLE [dbo].[StoreVisitProductDetail] CHECK CONSTRAINT [FK_StoreVisitProductDetail_Product]
ALTER TABLE [dbo].[StoreVisitProductDetail]  WITH CHECK ADD  CONSTRAINT [FK_StoreVisitProductDetail_StoreVisit] FOREIGN KEY([StoreVisitId])
REFERENCES [dbo].[StoreVisit] ([StoreVisitId])
ALTER TABLE [dbo].[StoreVisitProductDetail] CHECK CONSTRAINT [FK_StoreVisitProductDetail_StoreVisit]
ALTER TABLE [dbo].[OpeningInventoryProductExclusion]  WITH CHECK ADD  CONSTRAINT [FK_OpeningInventoryProductExclusion_CreatedByEmployee] FOREIGN KEY([CreatedByEmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[OpeningInventoryProductExclusion] CHECK CONSTRAINT [FK_OpeningInventoryProductExclusion_CreatedByEmployee]
ALTER TABLE [dbo].[OpeningInventoryProductExclusion]  WITH CHECK ADD  CONSTRAINT [FK_OpeningInventoryProductExclusion_Dealer] FOREIGN KEY([DealerId])
REFERENCES [dbo].[Dealer] ([DealerId])
ALTER TABLE [dbo].[OpeningInventoryProductExclusion] CHECK CONSTRAINT [FK_OpeningInventoryProductExclusion_Dealer]
ALTER TABLE [dbo].[OpeningInventoryProductExclusion]  WITH CHECK ADD  CONSTRAINT [FK_OpeningInventoryProductExclusion_Product] FOREIGN KEY([ProductId])
REFERENCES [dbo].[Product] ([ProductId])
ALTER TABLE [dbo].[OpeningInventoryProductExclusion] CHECK CONSTRAINT [FK_OpeningInventoryProductExclusion_Product]
ALTER TABLE [dbo].[DealerProductDisplayPhoto]  WITH CHECK ADD  CONSTRAINT [FK_DealerProductDisplayPhoto_Dealer] FOREIGN KEY([DealerId])
REFERENCES [dbo].[Dealer] ([DealerId])
ALTER TABLE [dbo].[DealerProductDisplayPhoto] CHECK CONSTRAINT [FK_DealerProductDisplayPhoto_Dealer]
ALTER TABLE [dbo].[DealerProductDisplayPhoto]  WITH CHECK ADD  CONSTRAINT [FK_DealerProductDisplayPhoto_DealerLocation] FOREIGN KEY([DealerLocationId], [DealerId])
REFERENCES [dbo].[DealerLocation] ([DealerLocationId], [DealerId])
ALTER TABLE [dbo].[DealerProductDisplayPhoto] CHECK CONSTRAINT [FK_DealerProductDisplayPhoto_DealerLocation]
ALTER TABLE [dbo].[DealerProductDisplayPhoto]  WITH CHECK ADD  CONSTRAINT [FK_DealerProductDisplayPhoto_Product] FOREIGN KEY([ProductId])
REFERENCES [dbo].[Product] ([ProductId])
ALTER TABLE [dbo].[DealerProductDisplayPhoto] CHECK CONSTRAINT [FK_DealerProductDisplayPhoto_Product]
ALTER TABLE [dbo].[DealerProductDisplayPhoto]  WITH CHECK ADD  CONSTRAINT [FK_DealerProductDisplayPhoto_ReplacedPhoto] FOREIGN KEY([ReplacedPhotoId])
REFERENCES [dbo].[DealerProductDisplayPhoto] ([DisplayPhotoId])
ALTER TABLE [dbo].[DealerProductDisplayPhoto] CHECK CONSTRAINT [FK_DealerProductDisplayPhoto_ReplacedPhoto]
ALTER TABLE [dbo].[DealerProductDisplayPhoto]  WITH CHECK ADD  CONSTRAINT [FK_DealerProductDisplayPhoto_StoreVisit] FOREIGN KEY([SourceStoreVisitId])
REFERENCES [dbo].[StoreVisit] ([StoreVisitId])
ALTER TABLE [dbo].[DealerProductDisplayPhoto] CHECK CONSTRAINT [FK_DealerProductDisplayPhoto_StoreVisit]
ALTER TABLE [dbo].[DealerProductDisplayPhoto]  WITH CHECK ADD  CONSTRAINT [FK_DealerProductDisplayPhoto_UploadedBy] FOREIGN KEY([UploadedByUserAccountId])
REFERENCES [dbo].[UserAccount] ([UserAccountId])
ALTER TABLE [dbo].[DealerProductDisplayPhoto] CHECK CONSTRAINT [FK_DealerProductDisplayPhoto_UploadedBy]
ALTER TABLE [dbo].[VisitTask]  WITH CHECK ADD  CONSTRAINT [FK_VisitTask_CreatedByEmployee] FOREIGN KEY([CreatedByEmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[VisitTask] CHECK CONSTRAINT [FK_VisitTask_CreatedByEmployee]
ALTER TABLE [dbo].[VisitTask]  WITH CHECK ADD  CONSTRAINT [FK_VisitTask_SampleApprovedByEmployee] FOREIGN KEY([SampleApprovedByEmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[VisitTask] CHECK CONSTRAINT [FK_VisitTask_SampleApprovedByEmployee]
ALTER TABLE [dbo].[VisitTask]  WITH CHECK ADD  CONSTRAINT [FK_VisitTask_SampleExecution] FOREIGN KEY([VisitTaskId], [SampleTaskExecutionId])
REFERENCES [dbo].[VisitTaskExecution] ([VisitTaskId], [TaskExecutionId])
ALTER TABLE [dbo].[VisitTask] CHECK CONSTRAINT [FK_VisitTask_SampleExecution]
ALTER TABLE [dbo].[VisitTask]  WITH CHECK ADD  CONSTRAINT [FK_VisitTask_ScopeOrganization] FOREIGN KEY([ScopeOrgUnitId])
REFERENCES [dbo].[OrganizationUnit] ([OrgUnitId])
ALTER TABLE [dbo].[VisitTask] CHECK CONSTRAINT [FK_VisitTask_ScopeOrganization]
ALTER TABLE [dbo].[VisitTask]  WITH CHECK ADD  CONSTRAINT [FK_VisitTask_UpdatedByEmployee] FOREIGN KEY([UpdatedByEmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[VisitTask] CHECK CONSTRAINT [FK_VisitTask_UpdatedByEmployee]
ALTER TABLE [dbo].[DealerTransferReview]  WITH CHECK ADD  CONSTRAINT [FK_DealerTransferReview_Dealer] FOREIGN KEY([DealerId])
REFERENCES [dbo].[Dealer] ([DealerId])
ALTER TABLE [dbo].[DealerTransferReview] CHECK CONSTRAINT [FK_DealerTransferReview_Dealer]
ALTER TABLE [dbo].[DealerTransferReview]  WITH CHECK ADD  CONSTRAINT [FK_DealerTransferReview_FromOrg] FOREIGN KEY([FromOrgUnitId])
REFERENCES [dbo].[OrganizationUnit] ([OrgUnitId])
ALTER TABLE [dbo].[DealerTransferReview] CHECK CONSTRAINT [FK_DealerTransferReview_FromOrg]
ALTER TABLE [dbo].[DealerTransferReview]  WITH CHECK ADD  CONSTRAINT [FK_DealerTransferReview_ResolvedBy] FOREIGN KEY([ResolvedByEmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[DealerTransferReview] CHECK CONSTRAINT [FK_DealerTransferReview_ResolvedBy]
ALTER TABLE [dbo].[DealerTransferReview]  WITH CHECK ADD  CONSTRAINT [FK_DealerTransferReview_ResolvedEmployee] FOREIGN KEY([ResolvedEmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[DealerTransferReview] CHECK CONSTRAINT [FK_DealerTransferReview_ResolvedEmployee]
ALTER TABLE [dbo].[DealerTransferReview]  WITH CHECK ADD  CONSTRAINT [FK_DealerTransferReview_SourceAssignment] FOREIGN KEY([SourceDealerAssignmentId])
REFERENCES [dbo].[DealerAssignmentHistory] ([DealerAssignmentId])
ALTER TABLE [dbo].[DealerTransferReview] CHECK CONSTRAINT [FK_DealerTransferReview_SourceAssignment]
ALTER TABLE [dbo].[DealerTransferReview]  WITH CHECK ADD  CONSTRAINT [FK_DealerTransferReview_SourceEmployee] FOREIGN KEY([SourceEmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[DealerTransferReview] CHECK CONSTRAINT [FK_DealerTransferReview_SourceEmployee]
ALTER TABLE [dbo].[DealerTransferReview]  WITH CHECK ADD  CONSTRAINT [FK_DealerTransferReview_ToOrg] FOREIGN KEY([ToOrgUnitId])
REFERENCES [dbo].[OrganizationUnit] ([OrgUnitId])
ALTER TABLE [dbo].[DealerTransferReview] CHECK CONSTRAINT [FK_DealerTransferReview_ToOrg]
ALTER TABLE [dbo].[EmployeePositionHistory]  WITH CHECK ADD  CONSTRAINT [FK_EmployeePositionHistory_CreatedByEmployee] FOREIGN KEY([CreatedByEmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[EmployeePositionHistory] CHECK CONSTRAINT [FK_EmployeePositionHistory_CreatedByEmployee]
ALTER TABLE [dbo].[EmployeePositionHistory]  WITH CHECK ADD  CONSTRAINT [FK_EmployeePositionHistory_Employee] FOREIGN KEY([EmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[EmployeePositionHistory] CHECK CONSTRAINT [FK_EmployeePositionHistory_Employee]
ALTER TABLE [dbo].[EmployeeOrgAssignmentHistory]  WITH CHECK ADD  CONSTRAINT [FK_EmployeeOrgAssignmentHistory_CreatedByEmployee] FOREIGN KEY([CreatedByEmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[EmployeeOrgAssignmentHistory] CHECK CONSTRAINT [FK_EmployeeOrgAssignmentHistory_CreatedByEmployee]
ALTER TABLE [dbo].[EmployeeOrgAssignmentHistory]  WITH CHECK ADD  CONSTRAINT [FK_EmployeeOrgAssignmentHistory_Employee] FOREIGN KEY([EmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[EmployeeOrgAssignmentHistory] CHECK CONSTRAINT [FK_EmployeeOrgAssignmentHistory_Employee]
ALTER TABLE [dbo].[EmployeeOrgAssignmentHistory]  WITH CHECK ADD  CONSTRAINT [FK_EmployeeOrgAssignmentHistory_OrganizationUnit] FOREIGN KEY([OrgUnitId])
REFERENCES [dbo].[OrganizationUnit] ([OrgUnitId])
ALTER TABLE [dbo].[EmployeeOrgAssignmentHistory] CHECK CONSTRAINT [FK_EmployeeOrgAssignmentHistory_OrganizationUnit]
ALTER TABLE [dbo].[SellInTransaction]  WITH CHECK ADD  CONSTRAINT [FK_SellInTransaction_Dealer] FOREIGN KEY([DealerId])
REFERENCES [dbo].[Dealer] ([DealerId])
ALTER TABLE [dbo].[SellInTransaction] CHECK CONSTRAINT [FK_SellInTransaction_Dealer]
ALTER TABLE [dbo].[SellInTransaction]  WITH CHECK ADD  CONSTRAINT [FK_SellInTransaction_ImportBatch] FOREIGN KEY([ImportBatchId])
REFERENCES [dbo].[ImportBatch] ([ImportBatchId])
ALTER TABLE [dbo].[SellInTransaction] CHECK CONSTRAINT [FK_SellInTransaction_ImportBatch]
ALTER TABLE [dbo].[SellInTransaction]  WITH CHECK ADD  CONSTRAINT [FK_SellInTransaction_Product] FOREIGN KEY([ProductId])
REFERENCES [dbo].[Product] ([ProductId])
ALTER TABLE [dbo].[SellInTransaction] CHECK CONSTRAINT [FK_SellInTransaction_Product]
ALTER TABLE [dbo].[OpeningInventoryCorrection]  WITH CHECK ADD FOREIGN KEY([ImportBatchId])
REFERENCES [dbo].[ImportBatch] ([ImportBatchId])
ALTER TABLE [dbo].[OpeningInventoryCorrection]  WITH CHECK ADD FOREIGN KEY([OpeningInventoryDetailId])
REFERENCES [dbo].[MonthlyOpeningInventoryDetail] ([OpeningInventoryDetailId])
ALTER TABLE [dbo].[MonthlyOpeningInventoryDetail]  WITH CHECK ADD  CONSTRAINT [FK_MonthlyOpeningInventoryDetail_Dealer] FOREIGN KEY([DealerId])
REFERENCES [dbo].[Dealer] ([DealerId])
ALTER TABLE [dbo].[MonthlyOpeningInventoryDetail] CHECK CONSTRAINT [FK_MonthlyOpeningInventoryDetail_Dealer]
ALTER TABLE [dbo].[MonthlyOpeningInventoryDetail]  WITH CHECK ADD  CONSTRAINT [FK_MonthlyOpeningInventoryDetail_ImportBatch] FOREIGN KEY([ImportBatchId])
REFERENCES [dbo].[ImportBatch] ([ImportBatchId])
ALTER TABLE [dbo].[MonthlyOpeningInventoryDetail] CHECK CONSTRAINT [FK_MonthlyOpeningInventoryDetail_ImportBatch]
ALTER TABLE [dbo].[MonthlyOpeningInventoryDetail]  WITH CHECK ADD  CONSTRAINT [FK_MonthlyOpeningInventoryDetail_Product] FOREIGN KEY([ProductId])
REFERENCES [dbo].[Product] ([ProductId])
ALTER TABLE [dbo].[MonthlyOpeningInventoryDetail] CHECK CONSTRAINT [FK_MonthlyOpeningInventoryDetail_Product]
ALTER TABLE [dbo].[ImportBatch]  WITH CHECK ADD  CONSTRAINT [FK_ImportBatch_ImportedByEmployee] FOREIGN KEY([ImportedByEmployeeId])
REFERENCES [dbo].[Employee] ([EmployeeId])
ALTER TABLE [dbo].[ImportBatch] CHECK CONSTRAINT [FK_ImportBatch_ImportedByEmployee]
ALTER TABLE [dbo].[ImportBatch]  WITH CHECK ADD  CONSTRAINT [FK_ImportBatch_ReplacedBatch] FOREIGN KEY([ReplacedBatchId])
REFERENCES [dbo].[ImportBatch] ([ImportBatchId])
ALTER TABLE [dbo].[ImportBatch] CHECK CONSTRAINT [FK_ImportBatch_ReplacedBatch]
ALTER TABLE [dbo].[VisitTaskPhoto]  WITH CHECK ADD  CONSTRAINT [CK_VisitTaskPhoto_NotSelfReference] CHECK  (([SampleTaskPhotoId] IS NULL OR [SampleTaskPhotoId]<>[TaskPhotoId]))
ALTER TABLE [dbo].[VisitTaskPhoto] CHECK CONSTRAINT [CK_VisitTaskPhoto_NotSelfReference]
ALTER TABLE [dbo].[VisitTaskPhoto]  WITH CHECK ADD  CONSTRAINT [CK_VisitTaskPhoto_SortOrder] CHECK  (([SortOrder]>=(0)))
ALTER TABLE [dbo].[VisitTaskPhoto] CHECK CONSTRAINT [CK_VisitTaskPhoto_SortOrder]
ALTER TABLE [dbo].[PasskeyCredential]  WITH CHECK ADD  CONSTRAINT [CK_PasskeyCredential_SignCount] CHECK  (([SignCount]>=(0)))
ALTER TABLE [dbo].[PasskeyCredential] CHECK CONSTRAINT [CK_PasskeyCredential_SignCount]
ALTER TABLE [dbo].[StoreVisit]  WITH CHECK ADD  CONSTRAINT [CK_StoreVisit_EntrySourceType] CHECK  (([EntrySourceType]='DEALER' OR [EntrySourceType]='EMPLOYEE'))
ALTER TABLE [dbo].[StoreVisit] CHECK CONSTRAINT [CK_StoreVisit_EntrySourceType]
ALTER TABLE [dbo].[StoreVisit]  WITH CHECK ADD  CONSTRAINT [CK_StoreVisit_RecordStatus] CHECK  (([RecordStatus]='VOIDED' OR [RecordStatus]='ACTIVE'))
ALTER TABLE [dbo].[StoreVisit] CHECK CONSTRAINT [CK_StoreVisit_RecordStatus]
ALTER TABLE [dbo].[StoreVisit]  WITH CHECK ADD  CONSTRAINT [CK_StoreVisit_UpdateAudit] CHECK  (([UpdatedAt] IS NULL AND [UpdatedByUserAccountId] IS NULL OR [UpdatedAt] IS NOT NULL AND [UpdatedByUserAccountId] IS NOT NULL))
ALTER TABLE [dbo].[StoreVisit] CHECK CONSTRAINT [CK_StoreVisit_UpdateAudit]
ALTER TABLE [dbo].[DealerLevelHistory]  WITH CHECK ADD  CONSTRAINT [CK_DealerLevelHistory_Period] CHECK  (([EndDateTime] IS NULL OR [EndDateTime]>[StartDateTime]))
ALTER TABLE [dbo].[DealerLevelHistory] CHECK CONSTRAINT [CK_DealerLevelHistory_Period]
ALTER TABLE [dbo].[DealerLevelHistory]  WITH CHECK ADD  CONSTRAINT [CK_DealerLevelHistory_Status] CHECK  (([DealerStatus]=N'E' OR [DealerStatus]=N'D' OR [DealerStatus]=N'C' OR [DealerStatus]=N'B' OR [DealerStatus]=N'A' OR [DealerStatus]=N'失聯店' OR [DealerStatus]=N'批店' OR [DealerStatus]=N'AC店' OR [DealerStatus]=N'專售店' OR [DealerStatus]=N'DC店' OR [DealerStatus]=N'一般店'))
ALTER TABLE [dbo].[DealerLevelHistory] CHECK CONSTRAINT [CK_DealerLevelHistory_Status]
ALTER TABLE [dbo].[VisitTaskExecution]  WITH CHECK ADD  CONSTRAINT [CK_VisitTaskExecution_Submission] CHECK  (([SubmittedAt] IS NULL OR [CompletedByEmployeeId] IS NOT NULL))
ALTER TABLE [dbo].[VisitTaskExecution] CHECK CONSTRAINT [CK_VisitTaskExecution_Submission]
ALTER TABLE [dbo].[UserAccount]  WITH CHECK ADD  CONSTRAINT [CK_UserAccount_AccountType] CHECK  (([AccountType]='DEALER' OR [AccountType]='EMPLOYEE'))
ALTER TABLE [dbo].[UserAccount] CHECK CONSTRAINT [CK_UserAccount_AccountType]
ALTER TABLE [dbo].[UserAccount]  WITH CHECK ADD  CONSTRAINT [CK_UserAccount_Owner] CHECK  (([AccountType]='EMPLOYEE' AND [EmployeeId] IS NOT NULL AND [DealerId] IS NULL OR [AccountType]='DEALER' AND [DealerId] IS NOT NULL AND [EmployeeId] IS NULL))
ALTER TABLE [dbo].[UserAccount] CHECK CONSTRAINT [CK_UserAccount_Owner]
ALTER TABLE [dbo].[UserAccount]  WITH CHECK ADD  CONSTRAINT [CK_UserAccount_Status] CHECK  (([AccountStatus]='DISABLED' OR [AccountStatus]='LOCKED' OR [AccountStatus]='ACTIVE'))
ALTER TABLE [dbo].[UserAccount] CHECK CONSTRAINT [CK_UserAccount_Status]
ALTER TABLE [dbo].[PasskeyRegistrationInvitation]  WITH CHECK ADD  CONSTRAINT [CK_PasskeyRegistrationInvitation_Expiry] CHECK  (([ExpiresAt]>[CreatedAt]))
ALTER TABLE [dbo].[PasskeyRegistrationInvitation] CHECK CONSTRAINT [CK_PasskeyRegistrationInvitation_Expiry]
ALTER TABLE [dbo].[DealerAssignmentHistory]  WITH CHECK ADD  CONSTRAINT [CK_DealerAssignmentHistory_Period] CHECK  (([EndDateTime] IS NULL OR [EndDateTime]>[StartDateTime]))
ALTER TABLE [dbo].[DealerAssignmentHistory] CHECK CONSTRAINT [CK_DealerAssignmentHistory_Period]
ALTER TABLE [dbo].[Employee]  WITH CHECK ADD  CONSTRAINT [CK_Employee_EmploymentDate] CHECK  (([TerminationDate] IS NULL OR [TerminationDate]>=[HireDate]))
ALTER TABLE [dbo].[Employee] CHECK CONSTRAINT [CK_Employee_EmploymentDate]
ALTER TABLE [dbo].[Dealer]  WITH CHECK ADD  CONSTRAINT [CK_Dealer_Condition] CHECK  (([DealerCondition]='CLOSED' OR [DealerCondition]='PENDING' OR [DealerCondition]='ACTIVE'))
ALTER TABLE [dbo].[Dealer] CHECK CONSTRAINT [CK_Dealer_Condition]
ALTER TABLE [dbo].[StoreVisitProductDetail]  WITH CHECK ADD  CONSTRAINT [CK_StoreVisitProductDetail_DisplayQuantity] CHECK  (([DisplayQuantity] IS NULL OR [DisplayQuantity]>=(1) AND [DisplayQuantity]<=(10)))
ALTER TABLE [dbo].[StoreVisitProductDetail] CHECK CONSTRAINT [CK_StoreVisitProductDetail_DisplayQuantity]
ALTER TABLE [dbo].[StoreVisitProductDetail]  WITH CHECK ADD  CONSTRAINT [CK_StoreVisitProductDetail_HasValue] CHECK  (([SellOutQuantity] IS NOT NULL OR [DisplayQuantity] IS NOT NULL))
ALTER TABLE [dbo].[StoreVisitProductDetail] CHECK CONSTRAINT [CK_StoreVisitProductDetail_HasValue]
ALTER TABLE [dbo].[StoreVisitProductDetail]  WITH CHECK ADD  CONSTRAINT [CK_StoreVisitProductDetail_SellOutPair] CHECK  (([SellOutQuantity] IS NULL AND [SellOutDate] IS NULL OR [SellOutQuantity] IS NOT NULL AND [SellOutDate] IS NOT NULL))
ALTER TABLE [dbo].[StoreVisitProductDetail] CHECK CONSTRAINT [CK_StoreVisitProductDetail_SellOutPair]
ALTER TABLE [dbo].[StoreVisitProductDetail]  WITH CHECK ADD  CONSTRAINT [CK_StoreVisitProductDetail_SellOutQuantity] CHECK  (([SellOutQuantity] IS NULL OR [SellOutQuantity]>=(1) AND [SellOutQuantity]<=(10)))
ALTER TABLE [dbo].[StoreVisitProductDetail] CHECK CONSTRAINT [CK_StoreVisitProductDetail_SellOutQuantity]
ALTER TABLE [dbo].[OpeningInventoryProductExclusion]  WITH CHECK ADD  CONSTRAINT [CK_OpeningInventoryProductExclusion_FromMonth] CHECK  ((NOT [EffectiveFromMonth] like '%[^0-9]%' AND (substring([EffectiveFromMonth],(5),(2))>='01' AND substring([EffectiveFromMonth],(5),(2))<='12')))
ALTER TABLE [dbo].[OpeningInventoryProductExclusion] CHECK CONSTRAINT [CK_OpeningInventoryProductExclusion_FromMonth]
ALTER TABLE [dbo].[OpeningInventoryProductExclusion]  WITH CHECK ADD  CONSTRAINT [CK_OpeningInventoryProductExclusion_Scope] CHECK  (([ScopeType]='ALL' AND [DealerId] IS NULL OR [ScopeType]='DEALER' AND [DealerId] IS NOT NULL))
ALTER TABLE [dbo].[OpeningInventoryProductExclusion] CHECK CONSTRAINT [CK_OpeningInventoryProductExclusion_Scope]
ALTER TABLE [dbo].[OpeningInventoryProductExclusion]  WITH CHECK ADD  CONSTRAINT [CK_OpeningInventoryProductExclusion_ToMonth] CHECK  (([EffectiveToMonth] IS NULL OR NOT [EffectiveToMonth] like '%[^0-9]%' AND (substring([EffectiveToMonth],(5),(2))>='01' AND substring([EffectiveToMonth],(5),(2))<='12') AND [EffectiveToMonth]>=[EffectiveFromMonth]))
ALTER TABLE [dbo].[OpeningInventoryProductExclusion] CHECK CONSTRAINT [CK_OpeningInventoryProductExclusion_ToMonth]
ALTER TABLE [dbo].[DealerProductDisplayPhoto]  WITH CHECK ADD  CONSTRAINT [CK_DealerProductDisplayPhoto_Month] CHECK  (([DataMonth] like '[12][0-9][0-9][0-9][01][0-9]'))
ALTER TABLE [dbo].[DealerProductDisplayPhoto] CHECK CONSTRAINT [CK_DealerProductDisplayPhoto_Month]
ALTER TABLE [dbo].[DealerProductDisplayPhoto]  WITH CHECK ADD  CONSTRAINT [CK_DealerProductDisplayPhoto_NotSelf] CHECK  (([ReplacedPhotoId] IS NULL OR [ReplacedPhotoId]<>[DisplayPhotoId]))
ALTER TABLE [dbo].[DealerProductDisplayPhoto] CHECK CONSTRAINT [CK_DealerProductDisplayPhoto_NotSelf]
ALTER TABLE [dbo].[DealerProductDisplayPhoto]  WITH CHECK ADD  CONSTRAINT [CK_DealerProductDisplayPhoto_Size] CHECK  (([OriginalFileSize]>(0) AND [ThumbnailFileSize]>(0)))
ALTER TABLE [dbo].[DealerProductDisplayPhoto] CHECK CONSTRAINT [CK_DealerProductDisplayPhoto_Size]
ALTER TABLE [dbo].[DealerProductDisplayPhoto]  WITH CHECK ADD  CONSTRAINT [CK_DealerProductDisplayPhoto_Status] CHECK  (([RecordStatus]='SUPERSEDED' OR [RecordStatus]='ACTIVE'))
ALTER TABLE [dbo].[DealerProductDisplayPhoto] CHECK CONSTRAINT [CK_DealerProductDisplayPhoto_Status]
ALTER TABLE [dbo].[VisitTask]  WITH CHECK ADD  CONSTRAINT [CK_VisitTask_DateRange] CHECK  (([DueDate]>=[ValidFrom]))
ALTER TABLE [dbo].[VisitTask] CHECK CONSTRAINT [CK_VisitTask_DateRange]
ALTER TABLE [dbo].[VisitTask]  WITH CHECK ADD  CONSTRAINT [CK_VisitTask_RecordStatus] CHECK  (([RecordStatus]='VOIDED' OR [RecordStatus]='ACTIVE'))
ALTER TABLE [dbo].[VisitTask] CHECK CONSTRAINT [CK_VisitTask_RecordStatus]
ALTER TABLE [dbo].[VisitTask]  WITH CHECK ADD  CONSTRAINT [CK_VisitTask_SampleApprovalAudit] CHECK  (([SampleApprovedAt] IS NULL AND [SampleApprovedByEmployeeId] IS NULL OR [SampleApprovedAt] IS NOT NULL AND [SampleApprovedByEmployeeId] IS NOT NULL AND [SampleTaskExecutionId] IS NOT NULL))
ALTER TABLE [dbo].[VisitTask] CHECK CONSTRAINT [CK_VisitTask_SampleApprovalAudit]
ALTER TABLE [dbo].[VisitTask]  WITH CHECK ADD  CONSTRAINT [CK_VisitTask_ScopeCounts] CHECK  (([ScopeDealerCount]>=(0) AND [ScopeExecutionCount]>=[ScopeDealerCount]))
ALTER TABLE [dbo].[VisitTask] CHECK CONSTRAINT [CK_VisitTask_ScopeCounts]
ALTER TABLE [dbo].[VisitTask]  WITH CHECK ADD  CONSTRAINT [CK_VisitTask_UpdateAudit] CHECK  (([UpdatedAt] IS NULL AND [UpdatedByEmployeeId] IS NULL OR [UpdatedAt] IS NOT NULL AND [UpdatedByEmployeeId] IS NOT NULL))
ALTER TABLE [dbo].[VisitTask] CHECK CONSTRAINT [CK_VisitTask_UpdateAudit]
ALTER TABLE [dbo].[DealerTransferReview]  WITH CHECK ADD  CONSTRAINT [CK_DealerTransferReview_Status] CHECK  (([ReviewStatus]='TRANSFERRED' OR [ReviewStatus]='RETAINED' OR [ReviewStatus]='OPEN'))
ALTER TABLE [dbo].[DealerTransferReview] CHECK CONSTRAINT [CK_DealerTransferReview_Status]
ALTER TABLE [dbo].[DealerTransferReview]  WITH CHECK ADD  CONSTRAINT [CK_DealerTransferReview_Trigger] CHECK  (([TriggerType]='MANUAL_UNASSIGNED' OR [TriggerType]='TERMINATION' OR [TriggerType]='ORG_MOVE'))
ALTER TABLE [dbo].[DealerTransferReview] CHECK CONSTRAINT [CK_DealerTransferReview_Trigger]
ALTER TABLE [dbo].[EmployeePositionHistory]  WITH CHECK ADD  CONSTRAINT [CK_EmployeePositionHistory_Period] CHECK  (([EndDateTime] IS NULL OR [EndDateTime]>[StartDateTime]))
ALTER TABLE [dbo].[EmployeePositionHistory] CHECK CONSTRAINT [CK_EmployeePositionHistory_Period]
ALTER TABLE [dbo].[EmployeeOrgAssignmentHistory]  WITH CHECK ADD  CONSTRAINT [CK_EmployeeOrgAssignmentHistory_Period] CHECK  (([EndDateTime] IS NULL OR [EndDateTime]>[StartDateTime]))
ALTER TABLE [dbo].[EmployeeOrgAssignmentHistory] CHECK CONSTRAINT [CK_EmployeeOrgAssignmentHistory_Period]
ALTER TABLE [dbo].[SellInTransaction]  WITH CHECK ADD  CONSTRAINT [CK_SellInTransaction_Quantity] CHECK  (([Quantity]<>(0)))
ALTER TABLE [dbo].[SellInTransaction] CHECK CONSTRAINT [CK_SellInTransaction_Quantity]
ALTER TABLE [dbo].[SellInTransaction]  WITH CHECK ADD  CONSTRAINT [CK_SellInTransaction_SourceRow] CHECK  (([SourceRowNumber]>(0)))
ALTER TABLE [dbo].[SellInTransaction] CHECK CONSTRAINT [CK_SellInTransaction_SourceRow]
ALTER TABLE [dbo].[MonthlyOpeningInventoryDetail]  WITH CHECK ADD  CONSTRAINT [CK_MonthlyOpeningInventoryDetail_SourceRow] CHECK  (([SourceRowNumber]>(0)))
ALTER TABLE [dbo].[MonthlyOpeningInventoryDetail] CHECK CONSTRAINT [CK_MonthlyOpeningInventoryDetail_SourceRow]
ALTER TABLE [dbo].[ImportBatch]  WITH CHECK ADD  CONSTRAINT [CK_ImportBatch_DataMonth] CHECK  (([DataMonth] IS NULL OR NOT [DataMonth] like '%[^0-9]%' AND (substring([DataMonth],(5),(2))>='01' AND substring([DataMonth],(5),(2))<='12')))
ALTER TABLE [dbo].[ImportBatch] CHECK CONSTRAINT [CK_ImportBatch_DataMonth]
ALTER TABLE [dbo].[ImportBatch]  WITH CHECK ADD  CONSTRAINT [CK_ImportBatch_DataPeriod] CHECK  (([DataMonth] IS NOT NULL AND [DataDate] IS NULL OR [DataMonth] IS NULL AND [DataDate] IS NOT NULL))
ALTER TABLE [dbo].[ImportBatch] CHECK CONSTRAINT [CK_ImportBatch_DataPeriod]
ALTER TABLE [dbo].[ImportBatch]  WITH CHECK ADD  CONSTRAINT [CK_ImportBatch_FileSize] CHECK  (([FileSize]>=(0)))
ALTER TABLE [dbo].[ImportBatch] CHECK CONSTRAINT [CK_ImportBatch_FileSize]
ALTER TABLE [dbo].[ImportBatch]  WITH CHECK ADD  CONSTRAINT [CK_ImportBatch_NotSelfReplaced] CHECK  (([ReplacedBatchId] IS NULL OR [ReplacedBatchId]<>[ImportBatchId]))
ALTER TABLE [dbo].[ImportBatch] CHECK CONSTRAINT [CK_ImportBatch_NotSelfReplaced]
ALTER TABLE [dbo].[ImportBatch]  WITH CHECK ADD  CONSTRAINT [CK_ImportBatch_RowCounts] CHECK  (([TotalRowCount]>=(0) AND [SuccessRowCount]>=(0) AND [ErrorRowCount]>=(0) AND ([SuccessRowCount]+[ErrorRowCount])<=[TotalRowCount]))
ALTER TABLE [dbo].[ImportBatch] CHECK CONSTRAINT [CK_ImportBatch_RowCounts]
ALTER TABLE [dbo].[ImportBatch]  WITH CHECK ADD  CONSTRAINT [CK_ImportBatch_Status] CHECK  (([ImportStatus]='Voided' OR [ImportStatus]='Superseded' OR [ImportStatus]='Official' OR [ImportStatus]='Failed' OR [ImportStatus]='Processing'))
ALTER TABLE [dbo].[ImportBatch] CHECK CONSTRAINT [CK_ImportBatch_Status]
/****** Object:  Trigger [dbo].[TR_Dealer_CreatePrimaryLocation]    Script Date: 2026/10/6 下午 04:43:45 ******/
SET ANSI_NULLS ON
SET QUOTED_IDENTIFIER ON
CREATE TRIGGER [dbo].[TR_Dealer_CreatePrimaryLocation]
ON [dbo].[Dealer] AFTER INSERT AS
BEGIN
    SET NOCOUNT ON;
    INSERT dbo.DealerLocation(DealerId,LocationName,StreetAddress,ContactName,Phone,IsPrimary,IsActive)
    SELECT i.DealerId,i.DealerName,i.StreetAddress,i.ContactName,COALESCE(i.CompanyPhone,i.MobilePhone),1,1
    FROM inserted i
    WHERE NOT EXISTS (SELECT 1 FROM dbo.DealerLocation l WHERE l.DealerId=i.DealerId);
END
ALTER TABLE [dbo].[Dealer] ENABLE TRIGGER [TR_Dealer_CreatePrimaryLocation]

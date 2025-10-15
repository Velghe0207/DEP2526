CREATE TABLE [dbo].[DimUser]
(
    UserKey [int] NOT NULL PRIMARY KEY,
    UserName [varchar](50) NOT NULL
)

CREATE TABLE [dbo].[BridgeUserSubgroup]
(
    UserKey [int] NOT NULL FOREIGN KEY REFERENCES [dbo].[DimUser](UserKey),
    SubgroupKey [int] NOT NULL,
    CONSTRAINT PK_BridgeUserSubgroup PRIMARY KEY (UserKey, SubgroupKey)
)

CREATE TABLE [dbo].[FactWifiConnection]
(
    DateKey [int] NOT NULL,
    TimeKey [int] NOT NULL,
    UserKey [int] NOT NULL FOREIGN KEY REFERENCES [dbo].[DimUser](UserKey),
    CONSTRAINT PK_FactWifiConnection PRIMARY KEY (DateKey, TimeKey, UserKey)
)
USE DEP2_staging

CREATE TABLE [dbo].[DimUser]
(
    UserKey INT IDENTITY(1,1) PRIMARY KEY,
    UserName VARCHAR(70) NOT NULL UNIQUE
);

ALTER TABLE DimUser ADD CONSTRAINT UQ_DimUser_UserName UNIQUE (UserName);

CREATE TABLE [dbo].[BridgeUserSubgroup]
(
    UserKey INT NOT NULL FOREIGN KEY REFERENCES [dbo].[DimUser](UserKey),
    SubgroupKey INT NOT NULL,
    CONSTRAINT PK_BridgeUserSubgroup PRIMARY KEY (UserKey, SubgroupKey)
);

CREATE TABLE [dbo].[FactWifiConnection]
(
    DateKey INT NOT NULL,
    TimeKey INT NOT NULL,
    UserKey INT NOT NULL FOREIGN KEY REFERENCES [dbo].[DimUser](UserKey),
    CONSTRAINT PK_FactWifiConnection PRIMARY KEY (DateKey, TimeKey, UserKey)
);
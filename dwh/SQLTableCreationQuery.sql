CREATE TABLE [dbo].[DimDate](
[DateKey] [int] NOT NULL PRIMARY KEY,
[FullDate] [date] NOT NULL,
[NameDay] [nvarchar](50) NOT NULL,
[NameMonthDutch] [nvarchar](50) NOT NULL,
[NameMonthEN] [nvarchar](50) NOT NULL,
[NameDayDutch] [nvarchar](50) NOT NULL,
[NameDayEN] [nvarchar](50) NOT NULL,
[NameQuarter] [nvarchar](50) NOT NULL,
[NumberQuarter] [int] NOT NULL,
[NumberSemester] [int] NOT NULL,
[Month] [int] NOT NULL,
[Year] [int] NOT NULL,
[Weekday] [int] NOT NULL CHECK ([Weekday] BETWEEN 1 AND 7),
[DayOfYear] [int] NOT NULL CHECK ([DayOfYear] BETWEEN 1 AND 366),
[Season] [nvarchar](50)
)

CREATE TABLE [dbo].[DimTime](
[TimeKey] [int] NOT NULL PRIMARY KEY,
[Hour] [int] NOT NULL,
[Minutes] [int] NOT NULL,
[Seconds] [int] NOT NULL,
[FullTime] [nvarchar](50) NOT NULL,
[TimeAM_PM] [varchar](50) NOT NULL
)

CREATE TABLE [dbo].[DimRoom](
RoomKey [int] NOT NULL PRIMARY KEY,
Building [varchar](50) NOT NULL,
RoomFloor [int] NOT NULL,
Code [int] NOT NULL,
RoomName [varchar](50) NOT NULL,
Category [varchar](50) NOT NULL,
Capacity [int] NOT NULL,
Area [int] NOT NULL
)

CREATE TABLE [dbo].[DimUser](
UserKey [int] NOT NULL PRIMARY KEY,
UserName [varchar](50) NOT NULL,
)

CREATE TABLE [dbo].[DimSubgroup](
SubgroupKey [int] NOT NULL PRIMARY KEY,
Code [int] NOT NULL,
)

CREATE TABLE [dbo].[DimClass](
ClassKey [int] NOT NULL PRIMARY KEY,
ClassName [varchar](50) NOT NULL,
StudyProgramCode [int] NOT NULL,
StudyProgramName [varchar](50) NOT NULL
)

CREATE TABLE [dbo].[BridgeUserSubgroup](
UserKey [int] NOT NULL FOREIGN KEY REFERENCES DimUser(UserKey),
SubgroupKey [int] NOT NULL FOREIGN KEY REFERENCES DimSubgroup(SubgroupKey),
CONSTRAINT PK_BridgeUserSubgroup PRIMARY KEY (UserKey, SubgroupKey)
)

CREATE TABLE [dbo].[BridgeClassSubgroup](
ClassKey [int] NOT NULL FOREIGN KEY REFERENCES DimClass(ClassKey),
SubgroupKey [int] NOT NULL FOREIGN KEY REFERENCES DimSubgroup(SubgroupKey),
CONSTRAINT PK_BridgeClassSubgroup PRIMARY KEY (ClassKey, SubgroupKey)
)

CREATE TABLE [dbo].[FactWifiConnection](
DateKey [int] NOT NULL FOREIGN KEY REFERENCES DimDate(DateKey),
TimeKey [int] NOT NULL FOREIGN KEY REFERENCES DimTime(TimeKey),
UserKey [int] NOT NULL FOREIGN KEY REFERENCES DimUser(UserKey),
CONSTRAINT PK_FactWifiConnection PRIMARY KEY (DateKey, TimeKey, UserKey)
)

CREATE TABLE [dbo].[FactLecture](
DateKey [int] NOT NULL FOREIGN KEY REFERENCES DimDate(DateKey),
FromTimeKey [int] NOT NULL FOREIGN KEY REFERENCES DimTime(TimeKey),
UntilTimeKey [int] NOT NULL FOREIGN KEY REFERENCES DimTime(TimeKey),
ClassKey [int] NOT NULL FOREIGN KEY REFERENCES DimClass(ClassKey),
RoomKey [int] NOT NULL FOREIGN KEY REFERENCES DimRoom(RoomKey),
CONSTRAINT PK_FactLecture PRIMARY KEY (DateKey, FromTimeKey, UntilTimeKey, ClassKey, RoomKey)
)
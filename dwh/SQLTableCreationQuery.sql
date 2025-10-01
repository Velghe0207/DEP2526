-- ======================
-- Dimension Tables
-- ======================

CREATE TABLE [dbo].[DimDate](
    [DateKey] INT NOT NULL PRIMARY KEY,
    [FullDate] DATE NOT NULL,
    [NameDay] NVARCHAR(50) NOT NULL,
    [NameMonthDutch] NVARCHAR(50) NOT NULL,
    [NameMonthEN] NVARCHAR(50) NOT NULL,
    [NameDayDutch] NVARCHAR(50) NOT NULL,
    [NameDayEN] NVARCHAR(50) NOT NULL,
    [NameQuarter] NVARCHAR(50) NOT NULL,
    [NumberQuarter] INT NOT NULL,
    [NumberSemester] INT NOT NULL,
    [Month] INT NOT NULL,
    [Year] INT NOT NULL,
    [Weekday] INT NOT NULL CHECK ([Weekday] BETWEEN 1 AND 7),
    [DayOfYear] INT NOT NULL CHECK ([DayOfYear] BETWEEN 1 AND 366),
    [Season] NVARCHAR(50)
);

CREATE TABLE [dbo].[DimTime](
    [TimeKey] INT NOT NULL PRIMARY KEY,
    [Hour] INT NOT NULL,
    [Minutes] INT NOT NULL,
    [Seconds] INT NOT NULL,
    [FullTime] NVARCHAR(50) NOT NULL,
    [TimeAM_PM] VARCHAR(50) NOT NULL
);

CREATE TABLE [dbo].[DimRoom](
    [RoomKey] INT NOT NULL PRIMARY KEY,
    [Building] VARCHAR(50) NOT NULL,
    [RoomFloor] INT NOT NULL,
    [Code] INT NOT NULL,
    [RoomName] VARCHAR(50) NOT NULL,

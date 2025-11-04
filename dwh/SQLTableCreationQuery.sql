USE DEP2;

CREATE TABLE [dbo].[DimDate]
(
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
    [Season] [nvarchar](50),
);

CREATE TABLE [dbo].[DimTime]
(
    [TimeKey] [int] NOT NULL PRIMARY KEY,
    [Hour] [int] NOT NULL,
    [Minutes] [int] NOT NULL,
    [Seconds] [int] NOT NULL,
    [FullTime] [nvarchar](50) NOT NULL,
    [TimeAM_PM] [varchar](50) NOT NULL,
);

CREATE TABLE [dbo].[DimRoom]
(
    RoomKey [int] NOT NULL PRIMARY KEY,
    Building [varchar](50) NOT NULL,
    RoomFloor [int] NOT NULL,
    Code [int] NOT NULL,
    RoomName [varchar](50) NOT NULL,
    Category [varchar](50) NOT NULL,
    Capacity [int] NOT NULL,
    Area [int] NOT NULL,
);

CREATE TABLE [dbo].[DimSubgroup]
(
    SubgroupKey [int] NOT NULL PRIMARY KEY,
    SubgroupName [varchar](50) NOT NULL,
    SubgroupCode [int] NOT NULL,
);

CREATE TABLE [dbo].[DimProgram]
(
    ProgramKey [int] NOT NULL PRIMARY KEY,
    ProgramName [varchar](50) NOT NULL,
);

CREATE TABLE [dbo].[DimClass]
(
    ClassKey [int] NOT NULL PRIMARY KEY,
    ClassName [varchar](150) NOT NULL,
    ClassCode [int] NOT NULL,
    ClassCredits [int] NOT NULL,
    ClassSecondChance [bit] NOT NULL,
    ClassProgramStage [int],
);

CREATE TABLE [dbo].[FactLecture]
(
    DateKey [int] NOT NULL FOREIGN KEY REFERENCES DimDate(DateKey),
    FromTimeKey [int] NOT NULL FOREIGN KEY REFERENCES DimTime(TimeKey),
    UntilTimeKey [int] NOT NULL FOREIGN KEY REFERENCES DimTime(TimeKey),
    ProgramKey [int] NOT NULL FOREIGN KEY REFERENCES DimProgram(ProgramKey),
    ClassKey [int] NOT NULL FOREIGN KEY REFERENCES DimClass(ClassKey),
    SubgroupKey [int] NOT NULL FOREIGN KEY REFERENCES DimSubgroup(SubgroupKey),
    RoomKey [int] NOT NULL FOREIGN KEY REFERENCES DimRoom(RoomKey),
    ScheduleID [int] NOT NULL,
    UserCount [int],
    TotalStudents [int],
    AttendanceRate AS (CASE WHEN TotalStudents = 0 THEN 0 ELSE CAST(UserCount AS float) / TotalStudents END),
    CONSTRAINT PK_FactLecture PRIMARY KEY (DateKey, FromTimeKey, UntilTimeKey, ProgramKey, ClassKey, RoomKey, SubgroupKey)
);
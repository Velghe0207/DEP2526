USE DEP2;
GO

-- Update UserCount and TotalStudents in FactLecture
WITH LectureTimes AS (
    SELECT
        fl.LectureID,
        fl.SubgroupKey,
        fl.DateKey,
        -- Convert FromTimeKey and UntilTimeKey to TIME
        CAST(STUFF(STUFF(RIGHT('000000' + CAST(fl.FromTimeKey AS VARCHAR(6)), 6), 3, 0, ':'), 6, 0, ':') AS TIME) AS FromTime,
        CAST(STUFF(STUFF(RIGHT('000000' + CAST(fl.UntilTimeKey AS VARCHAR(6)), 6), 3, 0, ':'), 6, 0, ':') AS TIME) AS UntilTime
    FROM DEP2.dbo.FactLecture fl
),
LectureWifi AS (
    SELECT
        lt.LectureID,
        lt.SubgroupKey,
        COUNT(DISTINCT fwc.UserKey) AS UserCount
    FROM LectureTimes lt
    INNER JOIN DEP2.dbo.DimSubgroup ds
        ON lt.SubgroupKey = ds.SubgroupKey
    INNER JOIN DEP2_staging.dbo.BridgeUserSubgroup bus
        ON ds.SubgroupKey = bus.SubgroupKey
    INNER JOIN DEP2_staging.dbo.FactWifiConnection fwc
        ON bus.UserKey = fwc.UserKey
        AND fwc.DateKey = lt.DateKey
        AND CAST(STUFF(STUFF(RIGHT('000000' + CAST(fwc.TimeKey AS VARCHAR(6)), 6), 3, 0, ':'), 6, 0, ':') AS TIME)
            BETWEEN DATEADD(MINUTE, 15, lt.FromTime) AND lt.UntilTime
    GROUP BY lt.LectureID, lt.SubgroupKey
),
LectureTotal AS (
    -- Roster size stays anchored to the current-scheme ("enc_") identities.
    -- The week1_4 September backfill uses an older, incompatible pseudonymization
    -- scheme ("u_<sha256>") with no crosswalk to the current one, so those users
    -- get their own DimUser/BridgeUserSubgroup rows (needed so their wifi presence
    -- still counts toward UserCount) but must be excluded here, otherwise every
    -- subgroup's TotalStudents double-counts the same real students all year.
    SELECT
        ds.SubgroupKey,
        COUNT(DISTINCT bus.UserKey) AS TotalStudents
    FROM DEP2.dbo.DimSubgroup ds
    INNER JOIN DEP2_staging.dbo.BridgeUserSubgroup bus
        ON ds.SubgroupKey = bus.SubgroupKey
    INNER JOIN DEP2_staging.dbo.DimUser du
        ON bus.UserKey = du.UserKey
    WHERE du.UserName LIKE 'enc\_%' ESCAPE '\'
    GROUP BY ds.SubgroupKey
),
CurrentTime AS (
    SELECT 
        -- Automatically converts UTC → Brussels local time with DST handling
        CAST(SYSDATETIMEOFFSET() AT TIME ZONE 'UTC' AT TIME ZONE 'Central European Standard Time' AS DATETIME) AS BrusselsDateTime,
        CONVERT(INT, FORMAT(SYSDATETIMEOFFSET() AT TIME ZONE 'UTC' AT TIME ZONE 'Central European Standard Time', 'yyyyMMdd')) AS BrusselsDateKey,
        CAST(CONVERT(TIME(0), SYSDATETIMEOFFSET() AT TIME ZONE 'UTC' AT TIME ZONE 'Central European Standard Time') AS TIME) AS BrusselsTime
)
UPDATE fl
SET 
    fl.UserCount = 
        CASE 
            -- If lecture has ended (earlier date or current date with UntilTime < now)
            WHEN (fl.DateKey < ct.BrusselsDateKey)
                 OR (fl.DateKey = ct.BrusselsDateKey AND lt2.UntilTime <= ct.BrusselsTime)
                THEN ISNULL(lw.UserCount, 0)
            ELSE NULL
        END,
    fl.TotalStudents = ISNULL(lt.TotalStudents, 0)
FROM DEP2.dbo.FactLecture fl
LEFT JOIN LectureWifi lw
    ON fl.LectureID = lw.LectureID
    AND fl.SubgroupKey = lw.SubgroupKey
LEFT JOIN LectureTotal lt
    ON fl.SubgroupKey = lt.SubgroupKey
LEFT JOIN LectureTimes lt2
    ON fl.LectureID = lt2.LectureID
CROSS JOIN CurrentTime ct;

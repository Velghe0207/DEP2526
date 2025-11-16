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
    SELECT
        ds.SubgroupKey,
        COUNT(DISTINCT bus.UserKey) AS TotalStudents
    FROM DEP2.dbo.DimSubgroup ds
    INNER JOIN DEP2_staging.dbo.BridgeUserSubgroup bus
        ON ds.SubgroupKey = bus.SubgroupKey
    GROUP BY ds.SubgroupKey
)
UPDATE fl
SET 
    fl.UserCount = ISNULL(lw.UserCount, 0),
    fl.TotalStudents = ISNULL(lt.TotalStudents, 0)
FROM DEP2.dbo.FactLecture fl
LEFT JOIN LectureWifi lw
    ON fl.LectureID = lw.LectureID
    AND fl.SubgroupKey = lw.SubgroupKey
LEFT JOIN LectureTotal lt
    ON fl.SubgroupKey = lt.SubgroupKey;

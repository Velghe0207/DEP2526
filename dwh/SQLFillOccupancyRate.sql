USE DEP2;
GO

-- Update OccupancyRate based on DimRoom.Capacity
UPDATE fl
SET fl.OccupancyRate = 
    CASE 
        WHEN dr.Capacity > 0 THEN CAST(fl.UserCount AS FLOAT) / dr.Capacity
        ELSE NULL
    END
FROM FactLecture fl
JOIN DimRoom dr 
    ON fl.RoomKey = dr.RoomKey;
GO

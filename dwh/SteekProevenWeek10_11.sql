-- 1: 5
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251124
AND FromTimeKey = 81500
AND UntilTimeKey = 101500
AND RoomName = 'GSCHB.4.029'
AND ClassName = 'Relational Databases & Datawarehousing';

-- 2: GAARB = Aalst, geen data
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251124
AND FromTimeKey = 81500
AND UntilTimeKey = 101500
AND RoomName = 'GAARB.0.032'
AND ClassName = 'Mathematics for Machine Learning';

-- 3: Subgroep 1B krijgt nooit deze OLOD in onze data
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251124
AND FromTimeKey = 91500
AND UntilTimeKey = 123000
AND RoomName = 'GSCHB.3.037'
AND ClassName = 'Computer Systems';

-- 4: 16
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251124
AND FromTimeKey = 103000
AND UntilTimeKey = 123000
AND RoomName = 'GSCHB.4.029'
AND ClassName = 'Relational Databases & Datawarehousing';

-- 5: Subgroep 1A krijgt nooit deze OLOD in onze data
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251124
AND FromTimeKey = 133000
AND UntilTimeKey = 164500
AND RoomName = 'GSCHB.3.037'
AND ClassName = 'Computer Systems';

-- 6: 7
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251125
AND FromTimeKey = 81500
AND UntilTimeKey = 101500
AND RoomName = 'GSCHB.2.010'
AND ClassName = 'Machine Learning Operations';

-- 7: 9
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251125
AND FromTimeKey = 81500
AND UntilTimeKey = 101500
AND RoomName = 'GSCHB.3.029'
AND ClassName = 'Relational Databases & Datawarehousing';

-- 8: 3
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251125
AND FromTimeKey = 103000
AND UntilTimeKey = 123000
AND RoomName = 'GSCHB.2.010'
AND ClassName = 'Modern Data Architectures';

-- 9: 9, Deze lesmoment komt niet voor in de data, maar een eerder les aan dezelfde klasgroepen zorgt ervoor dat we toch weten wie in de les moet zitten, dus we hebben dit getal met een ander scriptje gevonden
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251125
AND FromTimeKey = 103000
AND UntilTimeKey = 123000
AND RoomName = 'GSCHB.3.026'
AND ClassName = 'Modern Data Architectures';

USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, FactLecture.SubgroupKey, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE ClassName = 'Modern Data Architectures';

USE DEP2_staging
SELECT FactWifiConnection.UserKey
FROM FactWifiConnection
JOIN DimUser ON FactWifiConnection.UserKey = DimUser.UserKey
JOIN BridgeUserSubgroup ON DimUser.UserKey = BridgeUserSubgroup.UserKey
WHERE DateKey = 20251125 AND TimeKey BETWEEN 103000 + 1500 AND 123000 AND SubgroupKey = 5889323
GROUP BY FactWifiConnection.UserKey;

USE DEP2_staging
SELECT FactWifiConnection.UserKey
FROM FactWifiConnection
JOIN DimUser ON FactWifiConnection.UserKey = DimUser.UserKey
JOIN BridgeUserSubgroup ON DimUser.UserKey = BridgeUserSubgroup.UserKey
WHERE DateKey = 20251125 AND TimeKey BETWEEN 103000 + 1500 AND 123000 AND SubgroupKey = 5995906
GROUP BY FactWifiConnection.UserKey;

-- 10: 12
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251126
AND FromTimeKey = 133000
AND UntilTimeKey = 153000
AND RoomName = 'GSCHB.3.032'
AND ClassName = 'Relational Databases & Datawarehousing';

-- 11: 13
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251127
AND FromTimeKey = 91500
AND UntilTimeKey = 101500
AND RoomName = 'GSCHB.3.027'
AND ClassName = 'Deep Learning';

-- 12: 15
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251127
AND FromTimeKey = 103000
AND UntilTimeKey = 123000
AND RoomName = 'GSCHB.3.027'
AND ClassName = 'Deep Learning';

-- 13: GSCHP = P-gebouw, geen data
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251127
AND FromTimeKey = 133000
AND UntilTimeKey = 153000
AND RoomName = 'GSCHP.0.115'
AND ClassName = 'Inleiding in de Geo-ICT';

-- 14: 3
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251128
AND FromTimeKey = 81500
AND UntilTimeKey = 101500
AND RoomName = 'GSCHB.3.026'
AND ClassName = 'Machine Learning Operations';

-- 15: 10, Deze lesmoment komt niet voor in de data, maar een eerder les aan dezelfde klasgroepen zorgt ervoor dat we toch weten wie in de les moet zitten, dus we hebben dit getal met een ander scriptje gevonden
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251128
AND FromTimeKey = 103000
AND UntilTimeKey = 123000
AND RoomName = 'GSCHB.3.027'
AND ClassName = 'Web Services';

USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, FactLecture.SubgroupKey, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE ClassName = 'Web Services';

USE DEP2_staging
SELECT FactWifiConnection.UserKey
FROM FactWifiConnection
JOIN DimUser ON FactWifiConnection.UserKey = DimUser.UserKey
JOIN BridgeUserSubgroup ON DimUser.UserKey = BridgeUserSubgroup.UserKey
WHERE DateKey = 20251128 AND TimeKey BETWEEN 103000 + 1500 AND 123000 AND SubgroupKey = 5796259
GROUP BY FactWifiConnection.UserKey;

USE DEP2_staging
SELECT FactWifiConnection.UserKey
FROM FactWifiConnection
JOIN DimUser ON FactWifiConnection.UserKey = DimUser.UserKey
JOIN BridgeUserSubgroup ON DimUser.UserKey = BridgeUserSubgroup.UserKey
WHERE DateKey = 20251128 AND TimeKey BETWEEN 103000 + 1500 AND 123000 AND SubgroupKey = 5937311
GROUP BY FactWifiConnection.UserKey;

-- 16: GAARB = Aalst, geen data
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251128
AND FromTimeKey = 103000
AND UntilTimeKey = 123000
AND RoomName = 'GAARB.0.029'
AND ClassName = 'Mathematics for Machine Learning';

-- 17: Subgroep 2E2 krijgt nooit deze OLOD in onze data
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251128
AND FromTimeKey = 133000
AND UntilTimeKey = 153000
AND RoomName = 'GSCHB.3.027'
AND ClassName = 'Web Services';

USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, FactLecture.SubgroupKey, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE ClassName = 'Web Services';

-- 18: GAARB = Aalst, geen data
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251128
AND FromTimeKey = 133000
AND UntilTimeKey = 153000
AND RoomName = 'GAARB.0.032'
AND ClassName = 'Modern Data Architectures';

-- 19: 8
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251201
AND FromTimeKey = 81500
AND UntilTimeKey = 101500
AND RoomName = 'GSCHB.4.029'
AND ClassName = 'Relational Databases & Datawarehousing';

-- 20: GAARB = Aalst, geen data
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251201
AND FromTimeKey = 81500
AND UntilTimeKey = 101500
AND RoomName = 'GAARB.0.032'
AND ClassName = 'Mathematics for Machine Learning';

-- 21: Subgroep 1B krijgt nooit deze OLOD in onze data
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251201
AND FromTimeKey = 91500
AND UntilTimeKey = 123000
AND RoomName = 'GSCHB.3.037'
AND ClassName = 'Computer Systems';

USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, FactLecture.SubgroupKey, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE ClassName = 'Computer Systems';

-- 22: 16
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251201
AND FromTimeKey = 103000
AND UntilTimeKey = 123000
AND RoomName = 'GSCHB.4.029'
AND ClassName = 'Relational Databases & Datawarehousing';

-- 23: Subgroep 1A krijgt nooit deze OLOD in onze data
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251201
AND FromTimeKey = 133000
AND UntilTimeKey = 164500
AND RoomName = 'GSCHB.3.037'
AND ClassName = 'Computer Systems';

USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE ClassName = 'Computer Systems';

-- 24: 14, Subgroep PBA-VG-LAM/VT/VG/2 krijgt nooit deze OLOD in onze data, dus dit getal kijkt enkel naar de andere 3 subgroepen
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251201
AND FromTimeKey = 133000
AND UntilTimeKey = 153000
AND RoomName = 'GSCHB.3.012'
AND ClassName = 'Inleiding in de Geo-ICT';

USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE ClassName = 'Inleiding in de Geo-ICT';

-- 25: 7
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251201
AND FromTimeKey = 154500
AND UntilTimeKey = 174500
AND RoomName = 'GSCHB.2.010'
AND ClassName = 'Inleiding in de Geo-ICT';

-- 26: 4
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251202
AND FromTimeKey = 81500
AND UntilTimeKey = 101500
AND RoomName = 'GSCHB.2.010'
AND ClassName = 'Machine Learning Operations';

-- 27: 6
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251202
AND FromTimeKey = 81500
AND UntilTimeKey = 101500
AND RoomName = 'GSCHB.3.036'
AND ClassName = 'Relational Databases & Datawarehousing';

-- 28: 3
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251202
AND FromTimeKey = 103000
AND UntilTimeKey = 123000
AND RoomName = 'GSCHB.2.010'
AND ClassName = 'Modern Data Architectures';

-- 29: 7, Deze lesmoment komt niet voor in de data, maar een eerder les aan dezelfde klasgroepen zorgt ervoor dat we toch weten wie in de les moet zitten, dus we hebben dit getal met een ander scriptje gevonden
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251202
AND FromTimeKey = 103000
AND UntilTimeKey = 123000
AND RoomName = 'GSCHB.3.026'
AND ClassName = 'Modern Data Architectures';

USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, FactLecture.SubgroupKey, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE ClassName = 'Modern Data Architectures';

USE DEP2_staging
SELECT FactWifiConnection.UserKey
FROM FactWifiConnection
JOIN DimUser ON FactWifiConnection.UserKey = DimUser.UserKey
JOIN BridgeUserSubgroup ON DimUser.UserKey = BridgeUserSubgroup.UserKey
WHERE DateKey = 20251202 AND TimeKey BETWEEN 103000 + 1500 AND 123000 AND SubgroupKey = 5889323
GROUP BY FactWifiConnection.UserKey;

USE DEP2_staging
SELECT FactWifiConnection.UserKey
FROM FactWifiConnection
JOIN DimUser ON FactWifiConnection.UserKey = DimUser.UserKey
JOIN BridgeUserSubgroup ON DimUser.UserKey = BridgeUserSubgroup.UserKey
WHERE DateKey = 20251202 AND TimeKey BETWEEN 103000 + 1500 AND 123000 AND SubgroupKey = 5995906
GROUP BY FactWifiConnection.UserKey;

-- 30: 6
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251203
AND FromTimeKey = 133000
AND UntilTimeKey = 153000
AND RoomName = 'GSCHB.3.032'
AND ClassName = 'Relational Databases & Datawarehousing';

-- 31: 11
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251204
AND FromTimeKey = 91500
AND UntilTimeKey = 101500
AND RoomName = 'GSCHB.3.027'
AND ClassName = 'Deep Learning';

-- 32: 14
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251204
AND FromTimeKey = 103000
AND UntilTimeKey = 123000
AND RoomName = 'GSCHB.3.027'
AND ClassName = 'Deep Learning';

-- 33: 3
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251205
AND FromTimeKey = 81500
AND UntilTimeKey = 101500
AND RoomName = 'GSCHB.3.026'
AND ClassName = 'Machine Learning Operations';

-- 34: 9, Deze lesmoment komt niet voor in de data, maar een eerder les aan dezelfde klasgroepen zorgt ervoor dat we toch weten wie in de les moet zitten, dus we hebben dit getal met een ander scriptje gevonden
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251205
AND FromTimeKey = 103000
AND UntilTimeKey = 123000
AND RoomName = 'GSCHB.3.027'
AND ClassName = 'Web Services';

USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, FactLecture.SubgroupKey, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE ClassName = 'Web Services';

USE DEP2_staging
SELECT FactWifiConnection.UserKey
FROM FactWifiConnection
JOIN DimUser ON FactWifiConnection.UserKey = DimUser.UserKey
JOIN BridgeUserSubgroup ON DimUser.UserKey = BridgeUserSubgroup.UserKey
WHERE DateKey = 20251205 AND TimeKey BETWEEN 103000 + 1500 AND 123000 AND SubgroupKey = 5796259
GROUP BY FactWifiConnection.UserKey;

USE DEP2_staging
SELECT FactWifiConnection.UserKey
FROM FactWifiConnection
JOIN DimUser ON FactWifiConnection.UserKey = DimUser.UserKey
JOIN BridgeUserSubgroup ON DimUser.UserKey = BridgeUserSubgroup.UserKey
WHERE DateKey = 20251205 AND TimeKey BETWEEN 103000 + 1500 AND 123000 AND SubgroupKey = 5937311
GROUP BY FactWifiConnection.UserKey;

-- 35: GAARB = Aalst, geen data
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251205
AND FromTimeKey = 103000
AND UntilTimeKey = 123000
AND RoomName = 'GAARB.0.029'
AND ClassName = 'Mathematics for Machine Learning';

-- 36: 89, Enkel 9 van de 13 subgroepen zitten in onze database, dus dit getal is niet volledig
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251205
AND FromTimeKey = 133000
AND UntilTimeKey = 153000
AND RoomName = 'GSCHB.0.010'
AND ClassName = 'Modern Data Architectures';

-- 37: Subgroep 2E2 krijgt nooit deze OLOD in onze data
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251205
AND FromTimeKey = 133000
AND UntilTimeKey = 153000
AND RoomName = 'GSCHB.3.027'
AND ClassName = 'Web Services';

USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE ClassName = 'Web Services';

-- 38: GAARB = Aalst, geen data
USE DEP2
SELECT LectureID, FromTimeKey, UntilTimeKey, FactLecture.ClassKey, RoomName, SubgroupCode, UserCount, TotalStudents, AttendanceRate, ClassCode
FROM FactLecture
JOIN DimClass ON FactLecture.ClassKey = DimClass.ClassKey
JOIN DimRoom ON FactLecture.RoomKey = DimRoom.RoomKey
JOIN DimSubgroup ON FactLecture.SubgroupKey = DimSubgroup.SubgroupKey
WHERE DateKey = 20251205
AND FromTimeKey = 133000
AND UntilTimeKey = 153000
AND RoomName = 'GAARB.0.032'
AND ClassName = 'Modern Data Architectures';

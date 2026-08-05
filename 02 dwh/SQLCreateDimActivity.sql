USE DEP2;
GO

/* ============================================================
   Dimension: DimActivity
   Purpose : Unified list of activity types that can appear in
             WorkFormCourse, WorkFormExam, WorkFormEvaluation,
             and EducationActivity.
   ============================================================ */

IF OBJECT_ID('dbo.DimActivity','U') IS NOT NULL
BEGIN
  DROP TABLE dbo.DimActivity;
END
GO

CREATE TABLE dbo.DimActivity (
  ActivityKey           INT IDENTITY(1,1) PRIMARY KEY,
  CanonicalActivity     NVARCHAR(120) NOT NULL,     -- standardized label to show in reports
  ActivityDomain        VARCHAR(20)   NOT NULL,     -- 'Course' | 'Exam' | 'AcademicEvent'
  ActivityGroup         NVARCHAR(40)  NULL,         -- optional roll-up (Lecture/Lab/Exam/Event)
  SourceColumn          VARCHAR(30)   NOT NULL,     -- WorkFormCourse/WorkFormExam/WorkFormEvaluation/EducationActivity/Unknown
  SourceValue           NVARCHAR(200) NOT NULL,     -- raw value as in CSV

  -- Flags for slicing
  IsCourse              BIT NOT NULL DEFAULT 0,
  IsExam                BIT NOT NULL DEFAULT 0,
  IsAcademicEvent       BIT NOT NULL DEFAULT 0,
  IsGuestLecture        BIT NOT NULL DEFAULT 0,
  IsMakeUp              BIT NOT NULL DEFAULT 0,
  IsPractical           BIT NOT NULL DEFAULT 0,
  IsPresentation        BIT NOT NULL DEFAULT 0,
  IsDigitalPossible     BIT NOT NULL DEFAULT 0,

  -- Simple SCD metadata (optional)
  ValidFrom             DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  ValidTo               DATETIME2 NULL,
  IsCurrent             BIT       NOT NULL DEFAULT 1,

  CONSTRAINT UQ_DimActivity UNIQUE (SourceColumn, SourceValue, IsCurrent)
);
GO

/* ------------------------------------------------------------
   Seed: Unknown (safety net)
   ------------------------------------------------------------ */
INSERT INTO dbo.DimActivity
  (CanonicalActivity, ActivityDomain, ActivityGroup, SourceColumn, SourceValue,
   IsCourse, IsExam, IsAcademicEvent, IsGuestLecture, IsMakeUp, IsPractical, IsPresentation, IsDigitalPossible,
   ValidFrom, IsCurrent)
VALUES
  (N'Unknown', 'AcademicEvent', NULL, 'Unknown', N'',
   0,0,1,0,0,0,0,0, SYSUTCDATETIME(), 1);

/* ------------------------------------------------------------
   Seed: WorkFormCourse (Domain = Course)
   ------------------------------------------------------------ */
INSERT INTO dbo.DimActivity
  (CanonicalActivity, ActivityDomain, ActivityGroup, SourceColumn, SourceValue,
   IsCourse, IsExam, IsAcademicEvent, IsGuestLecture, IsMakeUp, IsPractical, IsPresentation, IsDigitalPossible)
VALUES
  (N'Activerend hoorcollege', 'Course', N'Lecture', 'WorkFormCourse', N'Activerend hoorcollege', 1,0,0,0,0,0,0,0),
  (N'Begeleiding',            'Course', N'Workshop','WorkFormCourse', N'Begeleiding',             1,0,0,0,0,0,0,0),
  (N'Excursie',               'Course', N'Field',   'WorkFormCourse', N'Excursie',                1,0,0,0,0,0,0,0),
  (N'Leerpad vast',           'Course', N'Lecture', 'WorkFormCourse', N'Leerpad vast',            1,0,0,0,0,0,0,0),
  (N'Leerpad vrij',           'Course', N'Lecture', 'WorkFormCourse', N'Leerpad vrij',            1,0,0,0,0,0,0,0),
  (N'Oefensessie',            'Course', N'Practice','WorkFormCourse', N'Oefensessie',             1,0,0,0,0,0,0,0),
  (N'Onderwijsleergesprek',   'Course', N'Seminar', 'WorkFormCourse', N'Onderwijsleergesprek',    1,0,0,0,0,0,0,0),
  (N'Practicum',              'Course', N'Lab',     'WorkFormCourse', N'Practicum',               1,0,0,0,0,1,0,0),
  (N'Stage',                  'Course', N'Internship','WorkFormCourse', N'Stage',                 1,0,0,0,0,1,0,0),
  (N'Werken aan opdracht',    'Course', N'Project', 'WorkFormCourse', N'Werken aan opdracht',     1,0,0,0,0,0,0,0),
  (N'Werkplekleren',          'Course', N'Workplace','WorkFormCourse', N'Werkplekleren',          1,0,0,0,0,1,0,0);

/* ------------------------------------------------------------
   Seed: WorkFormExam (Domain = Exam)
   ------------------------------------------------------------ */
INSERT INTO dbo.DimActivity
  (CanonicalActivity, ActivityDomain, ActivityGroup, SourceColumn, SourceValue,
   IsCourse, IsExam, IsAcademicEvent, IsGuestLecture, IsMakeUp, IsPractical, IsPresentation, IsDigitalPossible)
VALUES
  (N'Examen (digitaal)',              'Exam', N'Exam', 'WorkFormExam', N'Digitaal examen',                 0,1,0,0,0,0,0,1),
  (N'Examenopdracht (indienen)',      'Exam', N'Exam', 'WorkFormExam', N'Indienen examenopdracht',         0,1,0,0,0,0,0,1),
  (N'Examen (mondeling + schriftelijk)','Exam',N'Exam','WorkFormExam', N'Mondeling - schriftelijk examen', 0,1,0,0,0,0,0,0),
  (N'Examen (mondeling)',             'Exam', N'Exam', 'WorkFormExam', N'Mondeling examen',                0,1,0,0,0,0,0,0),
  (N'Presentatie (examen)',           'Exam', N'Exam', 'WorkFormExam', N'Presentatie',                     0,1,0,0,0,0,1,0),
  (N'Examen (schriftelijk)',          'Exam', N'Exam', 'WorkFormExam', N'Schriftelijk examen',             0,1,0,0,0,0,0,0),
  (N'Examen (vaardigheidstest)',      'Exam', N'Exam', 'WorkFormExam', N'Vaardigheidstest',                0,1,0,0,0,1,0,0),
  (N'Verdediging bachelorproef',      'Exam', N'Exam', 'WorkFormExam', N'Verdediging bachelorproef',       0,1,0,0,0,0,1,0);

/* ------------------------------------------------------------
   Seed: WorkFormEvaluation (Domain = Exam; Make-up where applicable)
   ------------------------------------------------------------ */
INSERT INTO dbo.DimActivity
  (CanonicalActivity, ActivityDomain, ActivityGroup, SourceColumn, SourceValue,
   IsCourse, IsExam, IsAcademicEvent, IsGuestLecture, IsMakeUp, IsPractical, IsPresentation, IsDigitalPossible)
VALUES
  (N'Examenopdracht (indienen)',       'Exam', N'Exam', 'WorkFormEvaluation', N'Indienen examenopdracht',      0,1,0,0,0,0,0,1),
  (N'Inhaalexamen (digitaal)',         'Exam', N'Exam', 'WorkFormEvaluation', N'Inhaalexamen Digitaal',        0,1,0,0,1,0,0,1),
  (N'Inhaalexamen (mondeling)',        'Exam', N'Exam', 'WorkFormEvaluation', N'Inhaalexamen Mondeling',       0,1,0,0,1,0,0,0),
  (N'Inhaalexamen (schriftelijk)',     'Exam', N'Exam', 'WorkFormEvaluation', N'Inhaalexamen Schriftelijk',    0,1,0,0,1,0,0,0),
  (N'Inhaalexamen (vaardigheidstest)', 'Exam', N'Exam', 'WorkFormEvaluation', N'Inhaalexamen Vaardigheidstest',0,1,0,0,1,1,0,0),
  (N'Presentatie (examen)',            'Exam', N'Exam', 'WorkFormEvaluation', N'Presentatie',                  0,1,0,0,0,0,1,0),
  (N'Examen (schriftelijk)',           'Exam', N'Exam', 'WorkFormEvaluation', N'Schriftelijk examen',          0,1,0,0,0,0,0,0);

/* ------------------------------------------------------------
   Seed: EducationActivity (Domain = AcademicEvent)
   ------------------------------------------------------------ */
INSERT INTO dbo.DimActivity
  (CanonicalActivity, ActivityDomain, ActivityGroup, SourceColumn, SourceValue,
   IsCourse, IsExam, IsAcademicEvent, IsGuestLecture, IsMakeUp, IsPractical, IsPresentation, IsDigitalPossible)
VALUES
  (N'Andere',                       'AcademicEvent', N'Event',   'EducationActivity', N'Andere',                        0,0,1,0,0,0,0,0),
  (N'Feedback',                     'AcademicEvent', N'Event',   'EducationActivity', N'Feedback',                      0,0,1,0,0,0,0,0),
  (N'Gastcollege',                  'AcademicEvent', N'Lecture', 'EducationActivity', N'Gastcollege',                   0,0,1,1,0,0,0,0),
  (N'Infosessie',                   'AcademicEvent', N'Event',   'EducationActivity', N'Infosessie',                    0,0,1,0,0,0,0,0),
  (N'Intervisie studenten',         'AcademicEvent', N'Event',   'EducationActivity', N'Intervisie studenten',          0,0,1,0,0,0,0,0),
  (N'Lokaalreservering',            'AcademicEvent', N'Event',   'EducationActivity', N'Lokaalreservering',             0,0,1,0,0,0,0,0),
  (N'Onthaaldag nieuwe studenten',  'AcademicEvent', N'Event',   'EducationActivity', N'Onthaaldag nieuwe studenten',   0,0,1,0,0,0,0,0),
  (N'Onthaalmoment',                'AcademicEvent', N'Event',   'EducationActivity', N'Onthaalmoment',                 0,0,1,0,0,0,0,0),
  (N'Studiedag',                    'AcademicEvent', N'Event',   'EducationActivity', N'Studiedag',                     0,0,1,0,0,0,0,0),
  (N'Workshop',                     'AcademicEvent', N'Workshop','EducationActivity', N'Workshop',                      0,0,1,0,0,0,0,0);
GO

PRINT '✅ DimActivity created and fully seeded.';

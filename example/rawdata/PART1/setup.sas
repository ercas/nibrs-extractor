*-------------------------------------------------------------------------*
|                       MOCK SAS DEFINITION FILE                          |
*-------------------------------------------------------------------------;

DATA;
INFILE "file-specification" LRECL=8;
INPUT
   COLUMN001 $ 1        COLUMN002 2     COLUMN003 3-5       COLUMN004 6-8;

LABEL
   COLUMN001 = "FIRST COLUMN"
   COLUMN002 = "SECOND COLUMN"
   COLUMN003 = "THIRD COLUMN"
   COLUMN004 = "FOURTH COLUMN";

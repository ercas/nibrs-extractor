# nibrs-extractor

`nibrs-extractor` is a tool to convert older data series from the FBI's [National Incident-Based Reporting System](https://www.fbi.gov/services/cjis/ucr/nibrs) (NIBRS) that are available from the [Inter-university Consortium for Political and Social Research](https://www.icpsr.umich.edu/web/pages/) (ICPSR) [National Archive of Criminal Justice Data](https://www.icpsr.umich.edu/web/NACJD/series/128) (NACJD) archive into flat CSV files.

### Rationale

Older NIBRS data series from the ICPSR's NACJD archive, i.e. all data prior to 2016, are available only as wide-format text files with accompanying SAS or SPSS code. This makes it somewhat inconvenient to work with this data in other languages, such as R or Python.

`nibrs-extractor` extracts metadata and column information from the included SAS code and manifest files and uses this information to generate new CSV files that can be opened in other languages and programs.
# nibrs-extractor

`nibrs-extractor` is a tool to convert older data series from the FBI's [National Incident-Based Reporting System](https://www.fbi.gov/services/cjis/ucr/nibrs) (NIBRS) that are available from the [Inter-university Consortium for Political and Social Research](https://www.icpsr.umich.edu/web/pages/) (ICPSR) [National Archive of Criminal Justice Data](https://www.icpsr.umich.edu/web/NACJD/series/128) (NACJD) archive into flat CSV files.

### Rationale

Older NIBRS data series from the ICPSR's NACJD archive, i.e. all data prior to 2016, are available only as wide-format text files with accompanying SAS or SPSS code. This makes it somewhat inconvenient to work with this data in other languages, such as R or Python, especially on systems without access to SAS or SPSS.

`nibrs-extractor` extracts metadata and column information from the included SAS code and manifest files and uses this information to generate new CSV files that can be opened in other languages and programs.


### Usage

To use `nibrs-extractor`, you must download the **SAS versions** of NIBRS data series from NACJD. These versions include a `*.sas` file in along with the raw data in each data segment subdirectory, which `nibrs-extractor` looks for and parses to find column information.

Example usage, using synthetic data from the [example](example/) directory (output has been cleaned up as `tqdm` fights with the exporter):

```python
# load the data series
>>> nibrs = NibrsDataSet("example/rawdata")

# inspect a single segment
>>> segment = nibrs.segments[0]
>>> segment.schema
[SasInput(name='COLUMN001', start=1, end=1, label='FIRST COLUMN'),
 SasInput(name='COLUMN002', start=2, end=2, label='SECOND COLUMN'),
 SasInput(name='COLUMN003', start=3, end=5, label='THIRD COLUMN'),
 SasInput(name='COLUMN004', start=6, end=8, label='FOURTH COLUMN')]

# write data in CSV format to a file stream (stdout)
>>> import sys
>>> segment.write_csv(sys.stdout)
1,a,b c,111
2,d,e f,222
3,g,h i,333
4,k,l m,444
converting PART1: 100%|██████████| 4/4 [00:00<00:00, 5091.72it/s]

# write column labels in CSV format
>>> segment.write_labels(sys.stdout)
VARIABLE,LABEL
COLUMN001,FIRST COLUMN
COLUMN002,SECOND COLUMN
COLUMN003,THIRD COLUMN
COLUMN004,FOURTH COLUMN

# extract everything
>>> nibrs.extract_all("example/processed")
(1/1) Extracting PART1
converting PART1: 100%|██████████| 4/4 [00:00<00:00, 38926.26it/s]
```

An example [R script](example/read.R) has also been provided to show how the generated labels file might be applied to a data frame.

### Future directions

* Read directly from the zip archives provided by NACJD, without having to decompress to the file system first
* Also store variable level information from the SAS code
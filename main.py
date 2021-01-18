#!/usr/bin/env python3
# Convert NIBRS fixed with data into delimited format with the help of the
# included manifest files and SAS code (thanks to NACJD for keeping it so
# organized!)

import collections
import csv
import dataclasses
import functools
import glob
import gzip
import os
import re
import typing

import tqdm  # the progress bar

# used to find SAS input variable definitions, e.g. B2001 1-2 -> (B2001, 1, 2)
# note that the range could be a single number, e.g. V1006 34 -> (V1006, 34, 34)
RE_SAS_INPUT_CODE = re.compile(r"^INPUT.*?;", re.MULTILINE | re.DOTALL)
RE_SAS_VARIABLE_DEFINITION = re.compile(r"([A-Z]+[0-9]+)[^0-9]*?([0-9]+)[^\s]?([0-9]+)?")

# used to find SAS label variable definitions, e.g. B2001 = "..." -> (B2001, ...)
RE_SAS_LABEL_CODE = re.compile(r"^LABEL.*?;", re.MULTILINE | re.DOTALL)
RE_SAS_LABEL_DEFINITION = re.compile(r"([A-Z]+[0-9]+)[^0-9]*?[\"|'](.*?)[\"|']")


@dataclasses.dataclass
class SasInput:
    """ Class encompassing a SAS variable input declaration """

    name: str
    start: int
    end: typing.Optional[int]
    label: typing.Optional[str]


class NibrsSegment:
    """ Class encompassing a single NIBRS data segment

    Attributes:
        root: The root directory where all the data is located
        directory: The subdirectory where this segment is located
        data: The name of the data file
        sas: The name of the SAS code file
        records: The number of records in this segment

    Properties:
        schema: A list of SasInput objects describing the schema of this segment
    """

    def __init__(self, root: str, directory: str, data: str, sas: str,
                 records: int) -> None:
        """ Initialize NibrsSegment object

        Args:
            root: The root directory where all the data is located
            directory: The subdirectory where this segment is located
            data: The name of the data file
            sas: The name of the SAS code file
            records: The number of records in this segment
        """

        self.root = root
        self.directory = directory
        self.data = data
        self.sas = sas
        self.records = records

    def __repr__(self) -> str:
        return "NibrsSegment({})".format(", ".join([
            "{}={}".format(name, getattr(self, name))
            for name in ["root", "directory", "data", "sas", "records"]
        ]))

    @property
    @functools.lru_cache(1)
    def schema(self) -> typing.List[SasInput]:
        """ Generate, cache, and return a list of variables in the data set

        Returns: A list of SasInput objects
        """

        with open(os.path.join(self.root, self.directory, self.sas)) as f:
            sas_code = f.read()

            # build dict of labels
            labels = collections.defaultdict(
                None,
                RE_SAS_LABEL_DEFINITION.findall(
                    RE_SAS_LABEL_CODE.search(sas_code).group(0)
                )
            )

            # build dict of variables, pulling labels from the labels dict
            return [
                SasInput(*(name, int(start), int(end), labels[name]))
                if end
                else SasInput(*(name, int(start), int(start), labels[name]))
                for (name, start, end) in RE_SAS_VARIABLE_DEFINITION.findall(
                    RE_SAS_INPUT_CODE.search(sas_code).group(0)
                )
            ]

    def write_csv(self, text_stream: typing.TextIO) -> None:
        """ Write this segment out to a CSV file

        Args:
            text_stream: A TextIO stream, e.g. sys.stdout or a file pointer
        """

        with open(os.path.join(self.root, self.directory, self.data), "r") as f:
            writer = csv.writer(text_stream)
            writer.writerow(variable.name for variable in self.schema)
            for line in tqdm.tqdm(
                    f,
                    desc="converting {}".format(self.directory),
                    total=self.records
            ):
                writer.writerow(
                    line[variable.start - 1:variable.end].strip()
                    for variable in self.schema
                )

    def write_labels(self, text_stream: typing.TextIO) -> None:
        """ Write this segment's variable labels out to a CSV file

        Args:
            text_stream: A TextIO stream, e.g. sys.stdout or a file pointer
        """

        writer = csv.writer(text_stream)
        writer.writerow(("VARIABLE", "LABEL"))
        for variable in self.schema:
            writer.writerow((variable.name, variable.label))


class NibrsDataSet:
    """ Class encompassing a NIBRS data set

    Attributes:
        path: The path to the data set
        manifest_path: The path to the manifest file

    Properties:
        year: The year that this data set is from
        segments: A list of NibrsSegment objects
    """

    def __init__(self, path: str) -> None:
        """ Initialize NibrsDataSet object

        Args:
            path: The path to the data set
        """
        self.path = path
        self.manifest_path = glob.glob(os.path.join(path, "*manifest.txt"))[0]

    def __repr__(self) -> str:
        return "NibrsDataSet({})".format(self.path)

    @property
    @functools.lru_cache(1)
    def year(self) -> int:
        """ Read the manifest file and store information about the data set and
        objects pointing to its included segments

        Returns: The year that the data is from, as an integer
        """

        with open(self.manifest_path, "r") as f:
            # discard the first line
            _ = f.readline()

            for line in f:
                match = re.search("[0-9][0-9][0-9][0-9]", line)
                if match:
                    return int(match.group(0))

    @property
    @functools.lru_cache(1)
    def segments(self) -> typing.List[NibrsSegment]:
        all_segments = []

        with open(self.manifest_path, "r") as f:
            # skip to segment information
            for line in f:
                if line.startswith("Study-level"):
                    break

            # state machine to look for segment information
            current_segment: typing.Optional[dict] = None
            for line in f:

                # directory name, also signifies start of new segment metadata
                if len(line) > 0:

                    if line[0].isalpha():
                        # end of metadata
                        if line.startswith("Version"):
                            break

                        # end of last segment
                        if current_segment is not None:
                            all_segments.append(NibrsSegment(**current_segment))

                        current_segment = {
                            "root": self.path,
                            "directory": line.split()[0]
                        }

                    elif current_segment is not None:
                        # data file
                        if ".txt" in line:
                            current_segment["data"] = line.split()[0]
                            current_segment["records"] = \
                                int(line.split()[2].replace(",", ""))

                        # sas code
                        if ".sas" in line:
                            current_segment["sas"] = line.split()[0]

        all_segments.append(NibrsSegment(**current_segment))
        return all_segments

    def extract_all(self, output_directory: str, compress: bool = True) -> None:
        """ Extract all data segments to an output directory

        Args:
            output_directory: The directory to save all segments to
            compress: If True, output to GZIP-compressed CSV
        """

        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)

        for i, segment in enumerate(self.segments):
            print("({}/{}) Extracting {}".format(
                i + 1, len(self.segments), segment.directory
            ))

            output = os.path.join(output_directory, "{}.csv".format(segment.directory))
            labels = os.path.join(output_directory, "{}-labels.csv".format(segment.directory))

            if compress:
                with gzip.open(output + ".gz", "wt") as f:
                    segment.write_csv(f)
                with gzip.open(labels + ".gz", "wt") as f:
                    segment.write_labels(f)
            else:
                with open(output, "w") as f:
                    segment.write_csv(f)
                with open(labels, "w") as f:
                    segment.write_labels(f)

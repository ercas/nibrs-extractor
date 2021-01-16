#!/usr/bin/env python3
# Convert NIBRS fixed with data into delimited format with the help of the
# included manifest files and SAS code (thanks to NACJD for keeping it so
# organized!)

import csv
import dataclasses
import glob
import os
import re
import typing

import tqdm  # the progress bar

# used to find SAS input variable definitions, e.g. B2001 1-2 -> (B2001, 1, 2)
# note that the range could be a single number, e.g. V1006 34 -> (V1006, 34, 34)
REGEX_VARIABLE_DEFINITION = re.compile(r"([A-Z][0-9]+).*?([0-9]+)-?([0-9]+)?")


@dataclasses.dataclass
class SasInput:
    """ Class encompassing a SAS variable input declaration """

    name: str
    start: int
    end: typing.Optional[int]


class NibrsSegment:
    """ Class encompassing a single NIBRS data segment

    Attributes:
        root: The root directory where all the data is located
        directory: The subdirectory where this segment is located
        data: The name of the data file
        sas: The name of the SAS code file
        records: The number of records in this segment
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

        self.__schema_cache = None

    def __repr__(self) -> str:
        return "NibrsSegment({})".format(", ".join([
            "{}={}".format(name, getattr(self, name))
            for name in ["root", "directory", "data", "sas", "records"]
        ]))

    @property
    def schema(self) -> typing.List[SasInput]:
        """ Generate, cache, and return a list of variables in the data set

        Returns: A list of SasInput objects
        """

        if self.__schema_cache is None:
            with open(os.path.join(self.root, self.directory, self.sas)) as f:
                # skip to SAS input code
                for line in f:
                    if line.startswith("INPUT"):
                        break

                input_code = ""
                for line in f:
                    input_code += line

                    # end of input code
                    if ";" in line:
                        break

                self.__schema_cache = [
                    SasInput(name, int(start), int(end))
                    if len(end) > 0
                    else SasInput(name, int(start), int(start))
                    for (name, start, end) in REGEX_VARIABLE_DEFINITION.findall(input_code)
                ]

        return self.__schema_cache

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


class NibrsDataSet:
    """ Class encompassing a NIBRS data set

    Attributes:
        path: The path to the data set
        manifest_path: The path to the manifest file
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

        # self.year is lazily evaluated
        # noinspection PyTypeChecker
        self.year: int = None
        self.segments: typing.List[NibrsSegment] = []

        self.__read_manifest()

    def __repr__(self) -> str:
        return "NibrsDataSet({})".format(self.path)

    def __read_manifest(self) -> None:
        """ Read the manifest file and store information about the data set and
        objects pointing to its included segments """

        with open(self.manifest_path, "r") as f:
            # discard first line
            _ = f.readline()

            # detect the year
            for line in f:
                match = re.search("[0-9][0-9][0-9][0-9]", line)
                if match:
                    self.year = int(match.group(0))
                    break

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
                            self.segments.append(NibrsSegment(**current_segment))

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

            self.segments.append(NibrsSegment(**current_segment))

    def extract_all(self, output_directory: str) -> None:
        """ Extract all data segments to an output directory

        Args:
            output_directory: The directory to save all segments to
        """

        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)

        for i, segment in enumerate(self.segments):
            print("({}/{}) Extracting {}".format(
                i + 1, len(self.segments), segment.directory
            ))
            with open(
                    os.path.join(output_directory, "{}.csv".format(segment.directory)),
                    "w"
            ) as f:
                segment.write_csv(f)


# nibrs = NibrsDataSet("rawdata/ICPSR_36120/")
# with open("DS0001.csv", "w") as f:
#     data.segments[0].write_csv(f)
# nibrs.extract_all("nibrs")

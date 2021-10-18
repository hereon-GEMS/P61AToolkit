from .P61ANexusReader import P61ANexusReader
from .XSpressCSVReader import XSpressCSVReader
from .RawFileReader import RawFileReader
from .EDDIReader import EDDIReader
from .XYReader import XYReader
from .P61AFioReader import P61AFioReader
from .P61ACSVReader import P61ACSVReader

DatasetReaders = (
    P61ANexusReader,
    P61AFioReader,
    P61ACSVReader,
    # XSpressCSVReader,
    # EDDIReader,
    # XYReader,
    # RawFileReader,
)

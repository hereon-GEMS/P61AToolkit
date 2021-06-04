from .P61ANexusReader import P61ANexusReader
from .XSpressCSVReader import XSpressCSVReader
from .RawFileReader import RawFileReader
from .EDDIReader import EDDIReader
from .XYReader import XYReader
from .P61AFioReader import P61AFioReader

DatasetReaders = (
    P61ANexusReader,
    P61AFioReader,
    XSpressCSVReader,
    EDDIReader,
    XYReader,
    RawFileReader,
)

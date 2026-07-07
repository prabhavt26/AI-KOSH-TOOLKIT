import pandas as pd
from typing import BinaryIO
import io
import zipfile
# pyrefly: ignore [missing-import]
import pydicom


class DatasetParser:
    @staticmethod
    def parse_csv(file_bytes: bytes, delimiter: str = ",") -> pd.DataFrame:
        """Parses CSV bytes into a pandas DataFrame."""
        return pd.read_csv(io.BytesIO(file_bytes), sep=delimiter)

    @staticmethod
    def parse_parquet(file_bytes: bytes) -> pd.DataFrame:
        """Parses Parquet bytes into a pandas DataFrame."""
        return pd.read_parquet(io.BytesIO(file_bytes))

    @staticmethod
    def parse_xlsx(file_bytes: bytes) -> pd.DataFrame:
        """Parses the first sheet of Excel bytes into a pandas DataFrame."""
        return pd.read_excel(io.BytesIO(file_bytes))

    @staticmethod
    def parse_json(file_bytes: bytes) -> pd.DataFrame:
        """Parses JSON bytes into a pandas DataFrame."""
        return pd.read_json(io.BytesIO(file_bytes))
    
    @staticmethod
    def parse_dicom(file_bytes: bytes) -> pd.DataFrame:
        ds = pydicom.dcmread(io.BytesIO(file_bytes))
        data = {}
        excluded_vrs = {"OB", "OW", "OD", "OF", "OL", "UN", "SQ"}
        for elem in ds:
            if elem.VR in excluded_vrs:
                continue
            if elem.value is None:
                continue
            key = elem.keyword or elem.name
            if not key:
                key = str(elem.tag)
            val = elem.value
            if isinstance(val, pydicom.multival.MultiValue):
                val = ", ".join(str(v) for v in val)
            else:
                val = str(val)
            data[key] = val
        return pd.DataFrame([data])


    @staticmethod
    def parse_zip(file_bytes: bytes) -> pd.DataFrame:
        """Extracts ZIP bytes and parses the first data file found inside."""
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            for name in zf.namelist():
                if name.startswith('__MACOSX') or name.startswith('.') or '/' in name and name.split('/')[-1].startswith('.'):
                    continue
                if name.endswith('.csv'):
                    return pd.read_csv(io.BytesIO(zf.read(name)))
                elif name.endswith('.parquet'):
                    return pd.read_parquet(io.BytesIO(zf.read(name)))
                elif name.endswith('.xlsx') or name.endswith('.xls'):
                    return pd.read_excel(io.BytesIO(zf.read(name)))
                elif name.endswith('.json'):
                    return pd.read_json(io.BytesIO(zf.read(name)))
                elif name.endswith(".dcm"):
                    return DatasetParser.parse_dicom(zf.read(name))
                       
        raise ValueError("No parsable file (.csv, .parquet, .xlsx, .json) found inside ZIP archive.")

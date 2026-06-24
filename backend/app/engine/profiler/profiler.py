"""
=============================================================================
Dataset Profiler — backend/app/engine/profiler/profiler.py
=============================================================================
This module reads an uploaded dataset file (as a pandas DataFrame) and
calculates statistical facts about it. These facts are later given to the
15 domain scorers so they can make scoring decisions automatically.

Think of it as a "medical check-up" for the dataset — it measures everything
before the doctor (the scorers) gives a diagnosis.
=============================================================================
"""

import re
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from app.config import settings


class DatasetProfiler:
    """
    Takes a pandas DataFrame and generates a full profile dictionary.

    Usage:
        profiler = DatasetProfiler(df, file_format="csv", size_bytes=102400)
        profile  = profiler.profile_dataset()
    """

    NAME_PATTERNS = re.compile(
        r'\b(name|patient_name|full_name|fname|lname|first_name|last_name|surname)\b',
        re.IGNORECASE
    )

    PHONE_PATTERNS = re.compile(
        r'\b(phone|mobile|contact|tel|telephone|cell)\b',
        re.IGNORECASE
    )

    ID_PATTERNS = re.compile(
        r'\b(id|uid|uuid|national_id|aadhaar|ssn|passport|mrn|patient_id|subject_id)\b',
        re.IGNORECASE
    )

    GPS_PATTERNS = re.compile(
        r'\b(lat|latitude|lon|longitude|gps|coordinates|geo)\b',
        re.IGNORECASE
    )

    DOB_PATTERNS = re.compile(
        r'\b(dob|date_of_birth|birth_date|birthdate|birth_year)\b',
        re.IGNORECASE
    )

    ICD_CODE_PATTERN = re.compile(r'^[A-Z]\d{2}(\.\d{1,4})?$')

    SNOMED_CODE_PATTERN = re.compile(r'^\d{6,18}$')

    LOINC_CODE_PATTERN = re.compile(r'^\d{1,5}-\d$')

    def __init__(self, df: pd.DataFrame, file_format: str = "csv", size_bytes: int = 0):
        """
        df          -> the dataset loaded as a DataFrame
        file_format -> "csv", "xlsx", "parquet", or "json"
        size_bytes  -> how big the file was on disk (in bytes)
        """
        self.raw_len = len(df)
        self.sampled = False
        self.sample_rows = None

        sample_rows_limit = getattr(settings, "PROFILING_SAMPLE_ROWS", 100000)
        if self.raw_len > sample_rows_limit:
            self.df = df.sample(n=sample_rows_limit, random_state=42)
            self.sampled = True
            self.sample_rows = sample_rows_limit
        else:
            self.df = df

        self.file_format = file_format
        self.size_bytes = size_bytes

    def profile_dataset(self) -> Dict[str, Any]:
        """
        Runs all the sub-checks and assembles them into one big dictionary.
        This dictionary is later stored in the database and passed to scorers.
        """
        result = {
            "file":                self._profile_file_info(),
            "shape":               self._profile_shape(),
            "columns":             self._profile_columns(),
            "pii_scan":            self._scan_pii(),
            "completeness":        self._profile_completeness(),
            "duplicates":          self._profile_duplicates(),
            "standards_detected":  self._detect_standards(),
            "split_columns":       self._detect_split_columns(),
            "label_columns":       self._detect_label_columns(),
            "age_distribution":    self._profile_age_distribution(),
            "schema_consistency":  self._profile_schema_consistency(),
        }
        if self.sampled:
            result["sampled"] = True
            result["sample_rows"] = self.sample_rows
        return result

    def _profile_file_info(self) -> Dict[str, Any]:
        """Returns basic facts about the file itself."""
        return {
            "format":     self.file_format,
            "size_bytes": self.size_bytes,
            "encoding":   "UTF-8",
        }

    def _profile_shape(self) -> Dict[str, Any]:
        """Counts how many rows and columns are in the dataset."""
        return {
            "rows":    self.raw_len,
            "columns": len(self.df.columns) if not self.df.empty else 0,
        }

    def _profile_columns(self) -> List[Dict[str, Any]]:
        """
        For every column, figures out its data type (numeric, text, date)
        and calculates basic statistics like average, min, max, missing %.
        """
        column_profiles = []

        for col in self.df.columns:
            series = self.df[col]

            missing_count = int(series.isna().sum())
            total_count   = len(series)

            completeness_pct = round(
                ((total_count - missing_count) / total_count * 100) if total_count > 0 else 0.0,
                2
            )

            col_profile: Dict[str, Any] = {
                "name":             col,
                "completeness_pct": completeness_pct,
                "missing_count":    missing_count,
            }

            if pd.api.types.is_numeric_dtype(series):
                col_profile["dtype"] = "numeric"
                non_null = series.dropna()

                if len(non_null) > 0:
                    col_profile["min"]    = float(non_null.min())
                    col_profile["max"]    = float(non_null.max())
                    col_profile["mean"]   = round(float(non_null.mean()), 4)
                    col_profile["median"] = round(float(non_null.median()), 4)
                    col_profile["std"]    = round(float(non_null.std()), 4)

                    q1  = non_null.quantile(0.25)
                    q3  = non_null.quantile(0.75)
                    iqr = q3 - q1
                    outlier_count = int(((non_null < q1 - 1.5 * iqr) | (non_null > q3 + 1.5 * iqr)).sum())
                    col_profile["outlier_pct"] = round(outlier_count / len(non_null) * 100, 2)

                    col_profile["range_violation"] = self._check_range_violation(col, non_null)

            elif pd.api.types.is_object_dtype(series) or pd.api.types.is_categorical_dtype(series):
                non_null = series.dropna()
                unique_vals = non_null.unique()

                if len(unique_vals) <= 50:
                    col_profile["dtype"]        = "categorical"
                    col_profile["unique_values"] = len(unique_vals)
                    col_profile["value_counts"]  = non_null.value_counts().to_dict()
                else:
                    col_profile["dtype"] = "string"

                pii_flag = self._get_pii_flag(col)
                if pii_flag:
                    col_profile["pii_flag"]       = pii_flag
                    col_profile["pii_confidence"] = "High"

            elif pd.api.types.is_datetime64_any_dtype(series):
                col_profile["dtype"] = "datetime"

            else:
                col_profile["dtype"] = "unknown"

            column_profiles.append(col_profile)

        return column_profiles

    def _scan_pii(self) -> Dict[str, Any]:
        """
        Scans EVERY column name and checks if it looks like it might hold
        personal/private information.
        """
        name_cols  = []
        phone_cols = []
        id_cols    = []
        gps_cols   = []
        dob_cols   = []

        for col in self.df.columns:
            if self.NAME_PATTERNS.search(col):
                name_cols.append(col)
            if self.PHONE_PATTERNS.search(col):
                phone_cols.append(col)
            if self.ID_PATTERNS.search(col):
                id_cols.append(col)
            if self.GPS_PATTERNS.search(col):
                gps_cols.append(col)
            if self.DOB_PATTERNS.search(col):
                dob_cols.append(col)

        direct_ids_detected = bool(name_cols or phone_cols or gps_cols or dob_cols)

        return {
            "direct_identifiers_detected": direct_ids_detected,
            "name_columns":  name_cols,
            "phone_columns": phone_cols,
            "id_columns":    id_cols,
            "gps_columns":   gps_cols,
            "dob_columns":   dob_cols,
        }

    def _profile_completeness(self) -> Dict[str, Any]:
        """
        Calculates how complete the overall dataset is.
        """
        if self.df.empty:
            return {"overall_pct": 0.0, "columns_below_90pct": [], "columns_below_50pct": []}

        total_cells   = self.df.size
        missing_cells = int(self.df.isna().sum().sum())

        overall_pct = round((total_cells - missing_cells) / total_cells * 100, 2)

        col_completeness = (1 - self.df.isnull().mean()) * 100
        cols_below_90 = list(col_completeness[col_completeness < 90].index)
        cols_below_50 = list(col_completeness[col_completeness < 50].index)

        return {
            "overall_pct":          overall_pct,
            "columns_below_90pct":  cols_below_90,
            "columns_below_50pct":  cols_below_50,
        }

    def _profile_duplicates(self) -> Dict[str, Any]:
        """Counts how many rows are exact duplicates of another row."""
        total = len(self.df)
        if total == 0:
            return {"exact_duplicate_rows": 0, "exact_duplicate_pct": 0.0}

        dup_count = int(self.df.duplicated().sum())
        dup_pct   = round(dup_count / total * 100, 2)

        return {
            "exact_duplicate_rows": dup_count,
            "exact_duplicate_pct":  dup_pct,
        }

    def _detect_standards(self) -> Dict[str, Any]:
        """
        Checks if any categorical columns contain medical standard codes
        like ICD-10, SNOMED-CT, or LOINC.
        """
        icd_cols    = []
        snomed_cols = []
        loinc_cols  = []

        for col in self.df.select_dtypes(include=["object"]).columns:
            sample = self.df[col].dropna().astype(str).head(500)

            icd_matches    = sample.apply(lambda v: bool(self.ICD_CODE_PATTERN.match(v.strip()))).mean()
            snomed_matches = sample.apply(lambda v: bool(self.SNOMED_CODE_PATTERN.match(v.strip()))).mean()
            loinc_matches  = sample.apply(lambda v: bool(self.LOINC_CODE_PATTERN.match(v.strip()))).mean()

            if icd_matches > 0.5:
                icd_cols.append(col)
            if snomed_matches > 0.5:
                snomed_cols.append(col)
            if loinc_matches > 0.5:
                loinc_cols.append(col)

        return {
            "icd_codes_present":    bool(icd_cols),
            "icd_columns":          icd_cols,
            "snomed_codes_present": bool(snomed_cols),
            "snomed_columns":       snomed_cols,
            "loinc_codes_present":  bool(loinc_cols),
            "loinc_columns":        loinc_cols,
            "fhir_structure":       False,
        }

    def _detect_split_columns(self) -> Dict[str, Any]:
        """
        Checks if the dataset already has a "split" column (train/test/validation)
        or a "fold" column (for cross-validation).
        """
        split_keywords = {"split", "partition", "set", "subset", "train_test", "data_split"}
        fold_keywords  = {"fold", "cv_fold", "kfold", "cross_val"}

        lower_cols = {c.lower() for c in self.df.columns}

        split_detected = bool(lower_cols & split_keywords)
        fold_detected  = bool(lower_cols & fold_keywords)

        return {
            "split_column_detected": split_detected,
            "fold_column_detected":  fold_detected,
        }

    def _detect_label_columns(self) -> Dict[str, Any]:
        """
        Tries to automatically detect which column is the ML "target" or "label".
        """
        label_keywords = {"label", "target", "outcome", "diagnosis", "class", "y",
                          "result", "treatment_outcome", "prediction"}
        lower_cols = {c.lower(): c for c in self.df.columns}

        detected_col = None
        for kw in label_keywords:
            if kw in lower_cols:
                detected_col = lower_cols[kw]
                break

        if detected_col is None:
            return {"binary_label_detected": False, "label_column": None,
                    "class_distribution": {}, "imbalance_ratio": None}

        col_series    = self.df[detected_col].dropna()
        unique_count  = col_series.nunique()
        is_binary     = unique_count == 2

        value_counts = col_series.value_counts().to_dict()

        if len(value_counts) >= 2:
            counts  = sorted(value_counts.values(), reverse=True)
            ratio   = round(counts[0] / counts[-1], 2) if counts[-1] > 0 else None
        else:
            ratio = None

        return {
            "binary_label_detected": is_binary,
            "label_column":          detected_col,
            "class_distribution":    {str(k): int(v) for k, v in value_counts.items()},
            "imbalance_ratio":       ratio,
        }

    def _profile_age_distribution(self) -> Dict[str, Any]:
        """
        Finds age columns and breaks patients into age groups:
        under 18 (children), 18-60 (adults), over 60 (elderly).
        """
        age_keywords = {"age", "age_years", "patient_age", "age_at_enrollment"}
        lower_cols   = {c.lower(): c for c in self.df.columns}

        age_col = None
        for kw in age_keywords:
            if kw in lower_cols:
                age_col = lower_cols[kw]
                break

        if age_col is None:
            return {}

        ages = self.df[age_col].dropna()

        if not pd.api.types.is_numeric_dtype(ages):
            return {}

        total      = len(ages)
        under_18   = int((ages < 18).sum())
        btw_18_60  = int(((ages >= 18) & (ages <= 60)).sum())
        over_60    = int((ages > 60).sum())

        def pct(n): return round(n / total * 100, 2) if total > 0 else 0.0

        return {
            "min":          float(ages.min()),
            "max":          float(ages.max()),
            "under_18_pct": pct(under_18),
            "18_to_60_pct": pct(btw_18_60),
            "over_60_pct":  pct(over_60),
        }

    def _profile_schema_consistency(self) -> Dict[str, Any]:
        """
        Counts how many rows have 'impossible' values — like negative age or
        BMI values over 100.
        """
        total_rows = len(self.df)
        if total_rows == 0:
            return {"conformant_rows_pct": 100.0, "schema_violations": 0}

        violations = 0

        for col in self.df.columns:
            if re.search(r'\bage\b', col, re.IGNORECASE):
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    violations += int(((self.df[col] < 0) | (self.df[col] > 150)).sum())

            if re.search(r'\bbmi\b', col, re.IGNORECASE):
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    violations += int(((self.df[col] < 5) | (self.df[col] > 100)).sum())

        conformant_pct = round((total_rows - violations) / total_rows * 100, 2)

        return {
            "conformant_rows_pct": conformant_pct,
            "schema_violations":   violations,
        }

    def _check_range_violation(self, col_name: str, series: pd.Series) -> bool:
        """
        Returns True if a numeric column has physically impossible values.
        """
        col_lower = col_name.lower()
        if "age" in col_lower:
            return bool((series < 0).any() or (series > 150).any())
        if "bmi" in col_lower:
            return bool((series < 5).any() or (series > 100).any())
        return False

    def _get_pii_flag(self, col_name: str) -> str:
        """
        Returns a label describing what type of PII this column might contain.
        """
        if self.NAME_PATTERNS.search(col_name):
            return "name_pattern"
        if self.PHONE_PATTERNS.search(col_name):
            return "phone_pattern"
        if self.ID_PATTERNS.search(col_name):
            return "id_pattern"
        if self.GPS_PATTERNS.search(col_name):
            return "gps_pattern"
        if self.DOB_PATTERNS.search(col_name):
            return "dob_pattern"
        return ""

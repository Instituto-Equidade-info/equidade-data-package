"""
Equidade Data Package
=====================

Data processing utilities for Equidade.info projects.

Modules:
    - aws: AWS S3 Parquet file loaders
    - gcp: Google Cloud Platform utilities (Storage, BigQuery)
    - utils: Common utilities

Example usage:
    >>> from equidade_data_package.aws.parquet_loader import load_treated_data
    >>> from equidade_data_package.gcp.storage import StorageService, DataFromStorage
    >>> from equidade_data_package.gcp.bigquery import BigQueryWaveLoader
"""

try:
    # Read from the installed distribution so this can never drift from pyproject.toml.
    # A hardcoded literal here was reporting 0.2.6 while the package was at 0.3.x, which
    # made "which version is actually deployed?" unanswerable from inside the function.
    from importlib.metadata import version as _pkg_version

    __version__ = _pkg_version("equidade-data-package")
except Exception:  # not installed as a distribution (e.g. running from a source tree)
    __version__ = "unknown"
__author__ = "Equidade Team"

# Import main classes for convenience
from equidade_data_package.aws import parquet_loader
from equidade_data_package.gcp import storage, bigquery

__all__ = [
    "parquet_loader",
    "storage",
    "bigquery",
]

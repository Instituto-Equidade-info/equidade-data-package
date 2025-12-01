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

__version__ = "0.1.0"
__author__ = "Equidade Team"

# Import main classes for convenience
from equidade_data_package.aws import parquet_loader
from equidade_data_package.gcp import storage, bigquery

__all__ = [
    "parquet_loader",
    "storage",
    "bigquery",
]

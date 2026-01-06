# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-06

### Added
- **Environment Configuration Module** (`equidade_data_package.config`)
  - `EnvLoader`: Centralized environment variable management
  - `EnvConfig`: Configuration dataclass for EnvLoader
  - `load_env()`: Convenience function for quick setup
  - Support for loading variables from:
    - YAML configuration files (`env-shared.yaml`)
    - GCP Secret Manager (automatic authentication)
    - Runtime environment variables
  - Function-specific variable mapping for 18+ Cloud Functions
  - Secret name mapping with shared and function-specific secrets
  - Type-safe getters: `get_json()`, `get_int()`, `get_bool()`
  - Variable validation with `validate()`
  - Secret caching for improved performance
  - Graceful fallbacks for missing secrets or YAML files

- **Dependencies**
  - `google-cloud-secret-manager>=2.0.0`
  - `pyyaml>=6.0.0`

- **Documentation**
  - [QUICKSTART.md](QUICKSTART.md) - Quick start guide for EnvLoader
  - [TECHNICAL_REFERENCE.md](TECHNICAL_REFERENCE.md) - Detailed technical documentation
  - [SETUP_SECRETS.md](SETUP_SECRETS.md) - Guide for setting up GCP Secret Manager
  - [examples/cloud_function_example.py](examples/cloud_function_example.py) - Production usage examples
  - [examples/local_development.py](examples/local_development.py) - Local development examples
  - [examples/migration_guide.md](examples/migration_guide.md) - Migration guide from manual env vars
  - [examples/README.md](examples/README.md) - Examples directory index

- **Configuration**
  - `env-files/env-shared.yaml` - Shared environment variables template
  - Pre-configured mappings for 18 Cloud Functions:
    - `equidade-download-data`
    - `access-processor`, `access-manager`, `access-revocation`
    - `etl-surveycto-function`
    - `check-s3-files`
    - `iu-process-dataset-updates`
    - `consistency_checker_function`
    - `gf_raw_data_function`, `gf_treatment_data_function`
    - `pi_raw_data_function`, `pi_treatment_data_function`
    - `process-dataset-updates`
    - `check-and-trigger-deploy`, `process-table-update`
    - `slack-notifier`, `docusign-webhook`

### Changed
- Updated repository URL from personal account to organization:
  - From: `github.com/spacejao/equidade-data-package`
  - To: `github.com/Instituto-Equidade-info/equidade-data-package`
- Updated all documentation with new repository URL
- Enhanced package description to include environment configuration

### Fixed
- N/A

## [0.1.0] - 2026-01-05

### Added
- Initial release
- **AWS S3 Parquet Loader**
  - `load_treated_data()` function for loading parquet files from S3
  - Support for filtering by agent name
  - Recent files filtering
  - Automatic schema handling

- **GCP Storage Module**
  - `StorageService` for Google Cloud Storage operations
  - `DataFromStorage` for loading various file formats (Parquet, CSV, Excel, JSON)
  - Support for saving data back to GCS

- **Google Drive Module**
  - `DriveService` for Google Drive operations
  - `DataFromDrive` for reading files, Google Sheets, and Excel files
  - Support for downloading files to buffer

- **BigQuery Module**
  - `query_bigquery()` with automatic result caching
  - `BigQueryWaveLoader` for loading DataFrames to BigQuery
  - Automatic type inference and schema handling
  - Safe loading for complex data with nulls

- **Dependencies**
  - pandas, pyarrow, numpy
  - google-cloud-storage, google-cloud-bigquery
  - google-api-python-client, google-auth
  - boto3, botocore

---

## Legend

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes

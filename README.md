# Equidade Data Package

Data processing utilities for Equidade.info projects - AWS S3, GCP Storage, Google Drive, and BigQuery loaders.

## 🚀 Automated Deployments

This package now supports **automatic deployments** to all Cloud Functions when a new version is released!

- ✅ One release triggers deploys in all dependent repos
- ✅ No manual updates needed
- ✅ Works with your existing workflows - just add 3 lines!
- ✅ Easy setup with automated scripts

```bash
# Setup (one time)
./scripts/patch-workflows.sh  # Adds trigger to all repos

# Daily use
./scripts/release.sh          # Creates release → all functions deploy automatically
```

**Quick Start**: [QUICKSTART.md](QUICKSTART.md) | **Full Guide**: [DEPLOY_AUTOMATION.md](DEPLOY_AUTOMATION.md) | **Patch Guide**: [PATCH_EXISTING_WORKFLOWS.md](PATCH_EXISTING_WORKFLOWS.md)

## Features

- **Environment Configuration**: Centralized environment variable management with YAML and Secret Manager support
- **AWS S3 Parquet Loader**: Robust parquet file loading from S3 with automatic schema handling
- **GCP Storage**: Read/write various file formats (Parquet, CSV, Excel, JSON) from Google Cloud Storage
- **Google Drive**: Download and read files, Google Sheets, and Excel files from Google Drive
- **BigQuery Query with Cache**: Execute BigQuery queries with automatic result caching for faster repeated queries
- **BigQuery Loader**: Load DataFrames into BigQuery with automatic type inference and schema handling

## Installation

### Install a specific version (recommended)

```bash
# uv (recommended)
uv pip install "equidade-data-package @ git+https://github.com/Instituto-Equidade-info/equidade-data-package.git@v0.3.2"

# pip
pip install "equidade-data-package @ git+https://github.com/Instituto-Equidade-info/equidade-data-package.git@v0.3.2"
```

**Always pin a tag.** Installing from `@main` — or with no ref at all, which means the
default branch — gives you an install whose URL is identical every time. pip caches by
URL, so the next install can quietly reuse what it already has, and you end up running a
version you did not expect with nothing to tell you so. This is the single most common
source of "but I updated it" confusion in this project, in CI and on laptops alike.

### Check which version you actually have

```bash
python -c "import equidade_data_package as p; print(p.__version__)"
```

Since 0.3.2 this reads from the installed distribution metadata, so it cannot disagree
with what is installed. Earlier versions hardcoded the number and were wrong.

Deployed functions report it too, once per cold start:

```
WARNING:root:equidade-data-package 0.3.2 loaded for function 'stf-etl-qualtrics'
```

### If you do track `main`

```bash
uv pip install --no-cache --reinstall \
  "equidade-data-package @ git+https://github.com/Instituto-Equidade-info/equidade-data-package.git@main"
```

`--no-cache` and `--reinstall` are both needed: the first stops pip reusing a cached
build, the second stops it deciding the requirement is already satisfied.

### Developing the package itself

```bash
git clone https://github.com/Instituto-Equidade-info/equidade-data-package.git
cd equidade-data-package
uv pip install -e .
```

An editable install always reflects your working tree, so no cache is involved.

### Upgrading

```bash
uv pip install --reinstall \
  "equidade-data-package @ git+https://github.com/Instituto-Equidade-info/equidade-data-package.git@v0.3.2"
python -c "import equidade_data_package as p; print(p.__version__)"   # confirm
```

Releases: https://github.com/Instituto-Equidade-info/equidade-data-package/releases

For CI and Cloud Functions, see [DEPLOY_PINNING.md](DEPLOY_PINNING.md).

## Usage

### Environment Configuration

Centralized environment variable management for Cloud Functions, eliminating duplication across repositories:

```python
from equidade_data_package.config import load_env

# Quick setup - loads env vars from YAML and Secret Manager
env = load_env("equidade-download-data")

# Get individual variables
slack_token = env.get("SLACK_BOT_TOKEN")
credentials = env.get_json("CREDENTIALS")  # Parses JSON automatically
max_retries = env.get_int("MAX_RETRIES", default=3)
debug_mode = env.get_bool("DEBUG", default=False)

# Or use advanced configuration
from equidade_data_package.config import EnvLoader, EnvConfig

config = EnvConfig(
    function_name="etl-surveycto-function",
    project_id="equidade",
    region="southamerica-east1",
    yaml_path="/custom/path/env-shared.yaml",  # Optional
    use_secret_manager=True,
    cache_secrets=True
)
env = EnvLoader(config)

# Set all vars to os.environ for the entire application
env.set_environment()

# Validate required variables
is_valid, missing = env.validate()
if not is_valid:
    raise ValueError(f"Missing required env vars: {missing}")

# Get all loaded variables
all_vars = env.get_all()
```

**How it works:**

1. **YAML Configuration** (`env-files/env-shared.yaml`): Non-sensitive shared values (URLs, IDs, etc.)
2. **Secret Manager**: Sensitive data (tokens, credentials, passwords)
3. **Runtime Environment**: Highest priority (Cloud Function env vars)

**Function-specific variable mapping:**

The loader automatically knows which variables each Cloud Function needs. Currently supports:
- `equidade-download-data`
- `access-processor`, `access-manager`, `access-revocation`
- `etl-surveycto-function`
- `check-s3-files`
- `consistency_checker_function`
- `gf_raw_data_function`, `gf_treatment_data_function`
- `pi_raw_data_function`, `pi_treatment_data_function`
- And 10+ other functions

**Secret Manager naming:**

Secrets are automatically mapped using a consistent naming convention:
- `SLACK_BOT_TOKEN` → `slack-bot-token-{function-name}` (function-specific)
- `AWS_ACCESS_KEY_ID` → `aws-access-key-id` (shared)
- `CREDENTIALS` → `credentials-{function-name}` (function-specific)

### AWS S3 Parquet Loader

Load treated data from S3 with automatic file discovery and schema handling:

```python
from equidade_data_package.aws.parquet_loader import load_treated_data

# Load recent data for a specific agent
df = load_treated_data(
    agente="alunos",
    aws_access_key="your-access-key",
    aws_secret_key="your-secret-key",
    only_recent=True,  # Load only the most recent files
    max_files=10       # Limit to 10 files
)

print(f"Loaded {len(df)} rows")
```

### Google Cloud Storage

Read and write various file formats from/to GCS:

```python
from equidade_data_package.gcp.storage import StorageService, DataFromStorage

# Initialize storage service
credentials = {...}  # Your GCP credentials dict
storage_service = StorageService(credentials)
data_loader = DataFromStorage(storage_service)

# Load a parquet file
df = data_loader.load_data(
    bucket_name="my-bucket",
    blob_path="path/to/file.parquet"
)

# Load a CSV file with custom parameters
df = data_loader.load_data(
    bucket_name="my-bucket",
    blob_path="path/to/file.csv",
    sep=";",
    encoding="utf-8"
)

# Save a DataFrame as parquet
data_loader.save_data(
    data=df,
    bucket_name="my-bucket",
    blob_path="output/data.parquet",
    compression="snappy"
)

# Close the connection when done
storage_service.close()
```

### Google Drive

Read files, Google Sheets, and Excel files directly from Google Drive:

```python
from equidade_data_package.gcp.drive import DriveService, DataFromDrive

# Initialize Drive service
credentials = {...}  # Your GCP credentials dict
drive_service = DriveService(credentials)
data_loader = DataFromDrive(drive_service)

# Read a CSV file from Drive
df = data_loader.read_csv(
    file_id="your-file-id-here"
)

# Read a Google Sheet as CSV
df = data_loader.read_csv(
    file_id="your-sheet-id-here",
    is_sheet=True  # Uses comma separator for Google Sheets
)

# Read multiple tabs from an Excel file
df = data_loader.read_excel_tabs(
    file_id="your-file-id-here",
    sheet_names=["Sheet1", "Sheet2", "Internet"],
    column_names=["col1", "col2", "col3"],
    skiprows=4  # Skip header rows
)

# Download any file to a buffer
file_buffer = data_loader.download_file(
    file_id="your-file-id-here",
    force_csv=True  # Export Google Sheets as CSV
)
```

### BigQuery

#### Query with Caching

Execute BigQuery queries with automatic result caching:

```python
from equidade_data_package.gcp.bigquery import query_bigquery

# Execute a query with credentials
credentials = {...}  # Your GCP credentials dict
df = query_bigquery(
    sql_query="SELECT * FROM `project.dataset.table` WHERE date > '2024-01-01'",
    credentials_json=credentials
)

# Or use environment variable for credentials
# Set GCP_CREDENTIALS env var with your credentials JSON
df = query_bigquery(
    sql_query="SELECT COUNT(*) as total FROM `project.dataset.table`"
)

# Subsequent calls with the same query return cached results instantly
df_cached = query_bigquery(
    sql_query="SELECT COUNT(*) as total FROM `project.dataset.table`"
)  # Returns immediately from cache
```

#### Load DataFrames to BigQuery

Load DataFrames into BigQuery with automatic type inference:

```python
from equidade_data_package.gcp.bigquery import BigQueryWaveLoader
import pandas as pd

# Initialize BigQuery loader
credentials = {...}  # Your GCP credentials dict
loader = BigQueryWaveLoader(
    project_id="my-project",
    credentials_json=credentials
)

# Load a DataFrame into BigQuery
df = pd.read_csv("data.csv")
success = loader.load_table(
    df=df,
    dataset_id="my_dataset",
    table_name="my_table"
)

# Use safe loading for complex data with nulls
success = loader.safe_load_to_bigquery(
    df=df,
    dataset_id="my_dataset",
    table_name="my_table"
)

# Process wave data
results = loader.process_wave(
    wave_number=1,
    base_path="/path/to/data",
    file_mappings={
        "students": "students_table",
        "teachers": "teachers_table"
    }
)
```

## Package Structure

```
equidade-data-package/
├── equidade_data_package/
│   ├── __init__.py
│   ├── config/              # Environment configuration
│   │   ├── __init__.py
│   │   └── env_loader.py
│   ├── aws/
│   │   ├── __init__.py
│   │   └── parquet_loader.py
│   ├── gcp/
│   │   ├── __init__.py
│   │   ├── storage.py
│   │   ├── bigquery.py
│   │   └── drive.py
│   └── utils/
│       └── __init__.py
├── env-files/
│   └── env-shared.yaml      # Shared environment variables
├── pyproject.toml
├── README.md
├── .gitignore
└── LICENSE
```

## Dependencies

The package requires:

- pandas >= 2.0.0
- pyarrow >= 19.0.0
- numpy >= 2.0.0
- google-cloud-storage >= 3.0.0
- google-cloud-bigquery >= 3.0.0
- google-cloud-secret-manager >= 2.0.0
- google-api-python-client >= 2.0.0
- google-auth >= 2.0.0
- boto3 >= 1.0.0
- botocore >= 1.0.0
- pyyaml >= 6.0.0

All dependencies are managed flexibly to ensure compatibility across different projects.

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/Instituto-Equidade-info/equidade-data-package.git
cd equidade-data-package

# Install with dev dependencies using uv
uv pip install -e ".[dev]"

# Run tests (when available)
pytest

# Format code
black equidade_data_package/
ruff check equidade_data_package/
```

## Adding to Your Project

### Using pyproject.toml (recommended with uv)

```toml
[project]
dependencies = [
    "equidade-data-package @ git+https://github.com/Instituto-Equidade-info/equidade-data-package.git",
    # ... other dependencies
]
```

### Using requirements.txt

```txt
git+https://github.com/Instituto-Equidade-info/equidade-data-package.git
```

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Ensure code follows the project style (use black and ruff)
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions, please contact the Equidade team.

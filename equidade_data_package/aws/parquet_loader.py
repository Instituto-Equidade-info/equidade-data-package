"""AWS S3 Parquet file loader with robust schema handling."""

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import logging
import re
from typing import Optional, List
from datetime import datetime


def load_treated_data(
    agente: str,
    aws_access_key: str,
    aws_secret_key: str,
    only_recent: bool = True,
    max_files: int = None,
) -> Optional[pd.DataFrame]:
    """
    Carrega arquivo de dados tratados do S3 com detecção automática de arquivos
    e tratamento robusto de schemas problemáticos

    Args:
        agente: Nome do agente (alunos, professores, etc.)
        aws_access_key: Chave de acesso AWS
        aws_secret_key: Chave secreta AWS
        only_recent: Se True, carrega apenas os arquivos mais recentes
        max_files: Número máximo de arquivos para carregar (None = todos)
    """
    agente_formatted = agente.lower()

    # Construct S3 path pattern
    s3_base_path = "landing-zone-iu-prod/saida/equidade.info/saida/transform/equidade.info/tratados"
    s3_agent_path = f"{s3_base_path}/{agente_formatted}/"

    # Create S3 filesystem
    fs = pa.fs.S3FileSystem(access_key=aws_access_key, secret_key=aws_secret_key)

    try:
        # Try to find files for this agent
        parquet_files = discover_parquet_files(fs, s3_agent_path, agente_formatted)

        if not parquet_files:
            logging.warning(
                f"No parquet files found for agent '{agente}' in path: {s3_agent_path}"
            )
            return None

        # Filter to recent files if requested
        if only_recent or max_files:
            parquet_files = filter_recent_files(fs, parquet_files, max_files)

        logging.info(
            f"Found {len(parquet_files)} files for agent '{agente}' (filtered: {only_recent or max_files is not None})"
        )

        # Read the data with robust error handling
        df = read_parquet_robust(fs, s3_agent_path, parquet_files)

        if df is not None:
            logging.info(
                f"Successfully loaded {df.shape[0]} rows, {df.shape[1]} columns for agent '{agente}'"
            )
            df = df.drop_duplicates(subset="KEY")

        return df

    except Exception as e:
        logging.error(f"Error loading treated data for agent '{agente}': {str(e)}")
        return None


def filter_recent_files(
    fs: pa.fs.S3FileSystem, parquet_files: List[str], max_files: int = None
) -> List[str]:
    """
    Filtra arquivos para manter apenas os da hora mais recente
    """
    if not parquet_files:
        return []

    try:
        # Get file info with modification times
        files_with_info = []
        for file_path in parquet_files:
            try:
                file_info = fs.get_file_info(file_path)
                # Get modification time, fallback to filename if not available
                mod_time = getattr(file_info, "mtime", None)

                # Convert mod_time to timestamp if it's a datetime
                if isinstance(mod_time, datetime):
                    mod_time = mod_time.timestamp()

                # If no modification time, try to extract date from filename
                if mod_time is None:
                    mod_time = extract_date_from_filename(file_path)

                files_with_info.append((file_path, mod_time))

            except Exception as e:
                logging.warning(f"Could not get info for file {file_path}: {e}")
                # Include file with timestamp 0 as fallback
                files_with_info.append((file_path, 0))

        # Group files by hour (truncate to hour precision)
        hour_groups = {}
        for file_path, mod_time in files_with_info:
            if mod_time and mod_time > 0:
                # Convert timestamp to datetime and truncate to hour
                dt = datetime.fromtimestamp(mod_time)
                hour_key = dt.replace(minute=0, second=0, microsecond=0)

                if hour_key not in hour_groups:
                    hour_groups[hour_key] = []
                hour_groups[hour_key].append((file_path, mod_time))
            else:
                # Handle files without valid timestamps
                fallback_key = datetime.fromtimestamp(0)
                if fallback_key not in hour_groups:
                    hour_groups[fallback_key] = []
                hour_groups[fallback_key].append((file_path, mod_time))

        if not hour_groups:
            logging.warning("No valid timestamps found in files")
            return parquet_files

        # Get the most recent hour
        most_recent_hour = max(hour_groups.keys())
        recent_hour_files = hour_groups[most_recent_hour]

        # Sort files within the most recent hour by exact timestamp
        recent_hour_files.sort(key=lambda x: x[1] if x[1] is not None else 0, reverse=True)

        # Apply max_files limit if specified (within the most recent hour)
        if max_files and max_files > 0:
            recent_hour_files = recent_hour_files[:max_files]

        recent_files = [file_path for file_path, _ in recent_hour_files]

        logging.info(
            f"Filtered to {len(recent_files)} files from most recent hour: {most_recent_hour}"
        )
        logging.info(
            f"Total hours found: {len(hour_groups)}, using hour: {most_recent_hour}"
        )

        # Log the selected files for debugging
        for i, (file_path, mod_time) in enumerate(recent_hour_files[:5]):  # Show first 5
            dt_str = (
                datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
                if mod_time and mod_time > 0
                else "unknown"
            )
            logging.debug(
                f"Selected file {i+1}: {file_path.split('/')[-1]} (time: {dt_str})"
            )

        return recent_files

    except Exception as e:
        logging.warning(f"Error filtering recent files: {e}. Using all files.")
        return parquet_files


def extract_date_from_filename(filename: str) -> int:
    """
    Tenta extrair uma data/timestamp do nome do arquivo para ordenação
    """
    # Common patterns in parquet filenames
    patterns = [
        r"(\d{4}-\d{2}-\d{2})",  # YYYY-MM-DD
        r"(\d{8})",  # YYYYMMDD
        r"(\d{4}\d{2}\d{2})",  # YYYYMMDD
        r"(\d{13})",  # Unix timestamp with milliseconds
        r"(\d{10})",  # Unix timestamp
    ]

    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            date_str = match.group(1)
            try:
                if len(date_str) == 10 and date_str.count("-") == 2:  # YYYY-MM-DD
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    return int(dt.timestamp())
                elif len(date_str) == 8:  # YYYYMMDD
                    dt = datetime.strptime(date_str, "%Y%m%d")
                    return int(dt.timestamp())
                elif len(date_str) in [10, 13]:  # Unix timestamp
                    return int(date_str[:10])  # Convert to seconds if needed
            except ValueError:
                continue

    # Fallback: use hash of filename for consistent ordering
    return hash(filename) % (10**10)


def discover_parquet_files(
    fs: pa.fs.S3FileSystem, base_path: str, agente: str
) -> List[str]:
    """
    Descobre arquivos parquet para um agente específico com múltiplas estratégias
    """
    possible_paths = [
        base_path,  # Direct path
        f"{base_path}/",  # With trailing slash
        base_path.replace(f"/{agente}/", f"/{agente}s/"),  # Plural form
        f'{base_path.rstrip("/")}/{agente}_tratados/',  # With suffix
        f'{base_path.rstrip("/")}_{agente}/',  # Underscore format
    ]

    parquet_files = []

    for path in possible_paths:
        try:
            # List files in the directory
            file_info = fs.get_file_info(pa.fs.FileSelector(path, recursive=True))
            found_files = [
                info.path
                for info in file_info
                if info.path.endswith(".parquet") and info.type == pa.fs.FileType.File
            ]

            if found_files:
                logging.info(f"Found {len(found_files)} parquet files in path: {path}")
                parquet_files.extend(found_files)
                break  # Use first successful path

        except Exception as e:
            logging.debug(f"Path {path} not accessible: {str(e)}")
            continue

    return list(set(parquet_files))  # Remove duplicates


def read_parquet_robust(
    fs: pa.fs.S3FileSystem, base_path: str, parquet_files: List[str]
) -> Optional[pd.DataFrame]:
    """
    Lê arquivos parquet com tratamento robusto de problemas de schema
    """
    if not parquet_files:
        return None

    # Strategy 1: Try reading all files together with schema handling
    try:
        return read_with_unified_schema(fs, base_path, parquet_files)
    except Exception as e:
        logging.warning(f"Unified schema read failed: {str(e)}")

    # Strategy 2: Try reading files individually and concatenating
    try:
        return read_files_individually(fs, parquet_files)
    except Exception as e:
        logging.warning(f"Individual file read failed: {str(e)}")

    # Strategy 3: Try reading all as strings
    try:
        return read_as_strings(fs, base_path, parquet_files)
    except Exception as e:
        logging.error(f"String read fallback failed: {str(e)}")

    return None


def read_with_unified_schema(
    fs: pa.fs.S3FileSystem, base_path: str, parquet_files: List[str]
) -> pd.DataFrame:
    """
    Tenta ler com schema unificado, convertendo tipos problemáticos
    """
    # Get schema from first file
    first_file = parquet_files[0]
    parquet_file = pq.ParquetFile(first_file, filesystem=fs)
    original_schema = parquet_file.schema_arrow

    # Create safe schema
    safe_schema = create_safe_schema(original_schema)

    # Read only the filtered files with safe schema
    table = pq.read_table(
        parquet_files, filesystem=fs, schema=safe_schema, use_pandas_metadata=False
    )

    return table.to_pandas(safe=False)


def read_files_individually(
    fs: pa.fs.S3FileSystem, parquet_files: List[str]
) -> pd.DataFrame:
    """
    Lê arquivos individualmente e concatena
    """
    dfs = []
    failed_files = []

    for file_path in parquet_files:
        try:
            # Try reading individual file
            table = pq.read_table(
                f"s3://{file_path}", filesystem=fs, use_pandas_metadata=False
            )
            df = table.to_pandas(safe=False)
            dfs.append(df)

        except Exception as e:
            logging.warning(f"Failed to read file {file_path}: {str(e)}")
            failed_files.append(file_path)
            continue

    if not dfs:
        raise Exception(
            f"No files could be read successfully. Failed files: {failed_files}"
        )

    if failed_files:
        logging.warning(
            f"Successfully read {len(dfs)} files, failed on {len(failed_files)} files"
        )

    # Concatenate all successful reads
    return pd.concat(dfs, ignore_index=True, sort=False)


def read_as_strings(
    fs: pa.fs.S3FileSystem, base_path: str, parquet_files: List[str]
) -> pd.DataFrame:
    """
    Fallback: lê todos os campos como strings
    """
    # Get schema from first file
    first_file = parquet_files[0]
    parquet_file = pq.ParquetFile(first_file, filesystem=fs)
    original_schema = parquet_file.schema_arrow

    # Create string-only schema
    string_fields = [pa.field(field.name, pa.string()) for field in original_schema]
    string_schema = pa.schema(string_fields)

    # Read only the filtered files with string schema
    table = pq.read_table(
        parquet_files, filesystem=fs, schema=string_schema, use_pandas_metadata=False
    )

    df = table.to_pandas(safe=False)

    # Try to convert obvious numeric columns back
    df = convert_numeric_columns(df)

    return df


def create_safe_schema(original_schema: pa.Schema) -> pa.Schema:
    """
    Cria schema seguro convertendo tipos problemáticos
    """
    new_fields = []
    for field in original_schema:
        if field.type == pa.null():
            # Convert null columns to string
            new_fields.append(pa.field(field.name, pa.string()))
        elif field.type == pa.int64():
            # Keep int64 columns but make them nullable
            new_fields.append(pa.field(field.name, pa.int64(), nullable=True))
        else:
            # Keep other types as they are
            new_fields.append(field)
    return pa.schema(new_fields)


def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tenta converter colunas obviamente numéricas de volta para números
    """
    for col in df.columns:
        if df[col].dtype == "object":
            # Try to convert to numeric if all non-null values look numeric
            try:
                # Check if all non-null values are numeric strings
                non_null_values = df[col].dropna()
                if len(non_null_values) > 0:
                    # Simple check for numeric strings
                    sample_values = non_null_values.head(100)
                    numeric_count = 0

                    for val in sample_values:
                        try:
                            float(str(val))
                            numeric_count += 1
                        except (ValueError, TypeError):
                            pass

                    # If most values look numeric, try conversion
                    if numeric_count / len(sample_values) > 0.8:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
            except Exception:
                # If conversion fails, keep as string
                pass

    return df

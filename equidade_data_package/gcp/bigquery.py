"""BigQuery loader with automatic type inference and schema handling."""

import pandas as pd
import os
import logging
import numpy as np
import hashlib
import time
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from google.oauth2 import service_account
from google.cloud import bigquery


# Global cache for query results
_query_cache = {}


def query_bigquery(
    sql_query: str, credentials_json: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Execute a BigQuery query with manual caching implementation.

    This function caches query results to avoid redundant API calls for identical queries.
    The cache key is an MD5 hash of the SQL query string.

    Args:
        sql_query: The SQL query to execute
        credentials_json: GCP credentials as dictionary. If None, loads from GCP_CREDENTIALS
                         environment variable

    Returns:
        pd.DataFrame: Query results as a DataFrame

    Raises:
        Exception: If query execution fails or credentials are missing

    Example:
        >>> credentials = {...}  # Your GCP credentials dict
        >>> df = query_bigquery("SELECT * FROM dataset.table", credentials)
        >>> # Second call with same query returns cached result
        >>> df2 = query_bigquery("SELECT * FROM dataset.table", credentials)
    """
    # Create hash of query for cache key
    query_hash = hashlib.md5(sql_query.encode("utf-8")).hexdigest()

    # Check if we have this query in cache
    if query_hash in _query_cache:
        logging.info(f"Cache hit for query: {query_hash[:8]}...")
        return _query_cache[query_hash].copy()  # Return copy to avoid modifications

    # If not in cache, execute the query
    start_time = time.time()

    try:
        # If credentials_json is None, load from environment
        if credentials_json is None:
            credentials_json = json.loads(os.getenv("GCP_CREDENTIALS"))

        # Create credentials
        credentials = service_account.Credentials.from_service_account_info(
            credentials_json, scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )

        # Create client
        client = bigquery.Client(
            credentials=credentials, project=credentials.project_id
        )

        # Configure job (without timeout_ms)
        job_config = bigquery.QueryJobConfig(
            use_query_cache=True  # Use BigQuery internal cache
        )

        # Execute the query
        query_job = client.query(sql_query, job_config=job_config)

        # Get the DataFrame
        df = query_job.to_dataframe()

        logging.info(f"BigQuery query took {time.time() - start_time:.2f} seconds")

        # Add to cache
        _query_cache[query_hash] = df.copy()

        return df

    except Exception as e:
        logging.error(f"BigQuery query error: {str(e)}")
        raise  # Re-raise the exception to maintain original behavior


@dataclass
class ColumnTypes:
    """Data class to store column type configurations."""

    STRING_COLUMNS = {
        "ID_ONDA",
        "ID_ESCOLA",
        "CO_ENTIDADE",
        "ID_AGENTE",
        "CO_REGIAO",
        "CO_UF",
        "CO_MUNICIPIO",
        "KEY",
        "id_aluno",
        "subjectId",
        "assessmentUid",
        "id",
        "guest_grade",
    }
    DATE_COLUMNS = {
        "DATA",
        "SubmissionDate",
        "DATA_HORA",
        "timeFinished",
        "timeStarted",
        "created",
        "lastUpdated",
    }
    ID_INDICATORS = {
        "id",
        "cod",
        "code",
        "codigo",
        "number",
        "num",
        "identificador",
        "CO",
        "ID",
        "COD",
    }


class BigQueryWaveLoader:
    """Loads educational wave data into BigQuery with proper type inference and handling."""

    def __init__(self, project_id: str, credentials_json: Dict):
        """
        Initialize the BigQuery loader with project credentials.

        Args:
            project_id: The GCP project ID
            credentials_json: Service account credentials as dictionary
        """
        self.credentials = service_account.Credentials.from_service_account_info(
            credentials_json, scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        self.client = bigquery.Client(
            credentials=self.credentials, project=self.credentials.project_id
        )
        self.project_id = project_id
        self.column_types = ColumnTypes()
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for the class."""
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    def _is_potential_id(self, column_name: str, values: pd.Series) -> bool:
        """
        Check if a column is potentially an ID based on name and content.

        Args:
            column_name: Name of the column
            values: Series containing the column values

        Returns:
            bool: True if column appears to be an ID field
        """
        name_lower = column_name.lower()
        has_id_name = any(
            indicator in name_lower for indicator in self.column_types.ID_INDICATORS
        )

        if not has_id_name:
            return False

        non_null_values = values.dropna()
        if len(non_null_values) == 0:
            return False

        try:
            # Check if values are numeric strings of sufficient length
            numeric_values = [str(val).replace(".0", "") for val in non_null_values]
            return all(val.isdigit() and len(val) >= 5 for val in numeric_values)
        except:
            return False

    def _clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean column names to be BigQuery compatible.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with cleaned column names
        """
        df = df.copy()
        df.columns = (
            df.columns.str.strip()
            .str.replace("[^0-9a-zA-Z_]", "_", regex=True)
            .str.replace("__+", "_", regex=True)
            .str.rstrip("_")
        )
        return df

    def _convert_to_numeric(self, series: pd.Series) -> Tuple[pd.Series, str]:
        """
        Convert a series to numeric, safely handling empty values.
        """
        try:
            # First, replace empty strings with NaN
            series = series.replace("", np.nan)

            # Skip processing if all values are NaN
            if series.isna().all():
                return series, "STRING"

            # Try to convert to numeric
            numeric_series = pd.to_numeric(
                series.astype(str)
                .str.replace("R$", None)
                .str.replace(",", ".")
                .str.strip(),
                errors="coerce",  # Convert problematic values to NaN
            )

            # If all non-null values are integers
            if numeric_series.dropna().equals(numeric_series.dropna().astype(int)):
                # Use Int64 which supports null values
                return numeric_series.astype("Int64"), "INTEGER"

            # For floats, ensure NaN is handled correctly
            return numeric_series.astype("float64"), "FLOAT"
        except Exception as e:
            # If failed, convert to string
            self.logger.warning(f"Failed to convert to numeric: {str(e)}")
            return series.fillna("").astype(str), "STRING"

    def infer_and_convert_types(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, List[bigquery.SchemaField]]:
        """
        Improved type inference that better handles null values for numeric columns
        """
        df = df.copy()
        # First standardize all null-like values
        df = df.replace(["", " ", "None", "null", "nan", np.nan], np.nan)
        schema = []

        for column in df.columns:
            # Skip special case columns (string and ID columns)
            if column in self.column_types.STRING_COLUMNS or self._is_potential_id(
                column, df[column]
            ):
                df[column] = df[column].fillna("").astype(str)
                schema.append(bigquery.SchemaField(column, "STRING"))
                continue

            # Handle date columns
            if column in self.column_types.DATE_COLUMNS:
                try:
                    df[column] = pd.to_datetime(df[column], errors="coerce")
                    schema.append(bigquery.SchemaField(column, "DATETIME"))
                    continue
                except:
                    df[column] = df[column].fillna("").astype(str)
                    schema.append(bigquery.SchemaField(column, "STRING"))
                    continue

            # For numeric columns, be more aggressive in numeric conversion
            # First check if there are non-null values
            non_null_values = df[column].dropna()
            if len(non_null_values) == 0:
                # Empty column - default to STRING
                df[column] = df[column].fillna("").astype(str)
                schema.append(bigquery.SchemaField(column, "STRING"))
                continue

            # Try numeric conversion with preprocessing
            try:
                # Clean the values for numeric conversion
                cleaned_values = (
                    df[column]
                    .astype(str)
                    .str.replace("R$", "", regex=False)
                    .str.replace(",", ".", regex=False)
                    .str.strip()
                )

                # Convert to numeric
                numeric_series = pd.to_numeric(cleaned_values, errors="coerce")

                # If over 90% of non-null values converted successfully, consider it numeric
                valid_numeric_count = numeric_series.notna().sum()
                if valid_numeric_count / len(non_null_values) >= 0.99:
                    # Check if all valid values are integers
                    valid_values = numeric_series.dropna()
                    if len(valid_values) > 0 and valid_values.equals(
                        valid_values.astype(int)
                    ):
                        df[column] = numeric_series.astype(
                            "Int64"
                        )  # Use nullable integer type
                        schema.append(bigquery.SchemaField(column, "INTEGER"))
                    else:
                        df[column] = numeric_series
                        schema.append(bigquery.SchemaField(column, "FLOAT"))
                else:
                    # Not enough valid numeric values - treat as string
                    df[column] = df[column].fillna("").astype(str)
                    schema.append(bigquery.SchemaField(column, "STRING"))
            except Exception as e:
                # Fallback to string
                self.logger.warning(f"Failed to convert {column} to numeric: {str(e)}")
                df[column] = df[column].fillna("").astype(str)
                schema.append(bigquery.SchemaField(column, "STRING"))

        return df, schema

    def load_table(self, df: pd.DataFrame, dataset_id: str, table_name: str) -> bool:
        """
        Load dataframe into BigQuery with enhanced empty string handling
        """
        try:
            # Make a copy to avoid modifying the original DataFrame
            df = df.copy()

            # Clean empty values and whitespace in all columns
            df = df.map(
                lambda x: np.nan if isinstance(x, str) and x.strip() == "" else x
            )
            df = df.replace(["", "nan", "None", "null"], np.nan)

            # Clean column names
            df = self._clean_column_names(df)

            # Do type inference and conversion
            df, schema = self.infer_and_convert_types(df)

            # Additional safety check after type inference
            # Ensure no empty strings in any numeric columns
            for col, field in zip(df.columns, schema):
                if field.field_type in ["INTEGER", "FLOAT"]:
                    # Convert numeric types with coercion to handle any remaining issues
                    df[col] = pd.to_numeric(df[col], errors="coerce")

                    # For INTEGER fields, use pandas nullable integer type
                    if field.field_type == "INTEGER":
                        df[col] = df[col].astype("Int64")

                elif field.field_type == "STRING":
                    # Ensure strings don't have any empty values
                    df[col] = df[col].fillna("").astype(str)

            # Log columns and their types before upload for debugging
            column_types = {col: str(df[col].dtype) for col in df.columns}
            self.logger.info(f"Column types before upload: {column_types}")

            table_id = f"{self.project_id}.{dataset_id}.{table_name}"

            job_config = bigquery.LoadJobConfig(
                schema=schema,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            )

            job = self.client.load_table_from_dataframe(
                df, table_id, job_config=job_config
            )
            job.result()

            self.logger.info(
                f"Tabela {table_name} carregada com sucesso no dataset {dataset_id}!"
            )
            return True

        except Exception as e:
            self.logger.error(
                f"Erro ao carregar {table_name} no dataset {dataset_id}: {str(e)}"
            )
            # Log more details about the error
            if "Invalid value" in str(e):
                # Try to identify the problematic columns
                try:
                    problematic_cols = []
                    for col in df.columns:
                        if df[col].dtype.name.startswith(("float", "Float")):
                            # Check for any strings in this column
                            has_strings = (
                                df[col].astype(str).str.contains("[a-zA-Z]").any()
                            )
                            if has_strings:
                                problematic_cols.append(col)

                    if problematic_cols:
                        self.logger.error(
                            f"Potential problematic columns: {problematic_cols}"
                        )

                    # Sample the problematic values
                    self.logger.error("Sampling some values that might cause issues:")
                    for col in df.columns:
                        if df[col].dtype.name.startswith(("float", "Float")):
                            # Get some sample non-numeric values
                            samples = df[
                                df[col].astype(str).str.contains("[^0-9\.\-]", na=False)
                            ][col].head(5)
                            if not samples.empty:
                                self.logger.error(
                                    f"Column {col} has problematic values: {samples.tolist()}"
                                )

                except Exception as debug_e:
                    self.logger.error(f"Error during debug: {str(debug_e)}")

            return False

    def safe_load_to_bigquery(
        self, df: pd.DataFrame, dataset_id: str, table_name: str
    ) -> bool:
        """
        Enhanced safe loading with improved type detection for columns with nulls
        """
        try:
            # Step 1: Make a copy and clean column names
            df = df.copy()
            df = self._clean_column_names(df)

            # Step 2: Standardize null values
            df = df.replace(["", " ", "None", "null", "nan"], np.nan)

            # Step 3: Create a schema with better type detection
            schema = []
            clean_df = pd.DataFrame()

            # Log columns with many NaN values to help debugging

            for column in df.columns:
                # Check for special string columns first
                if column in self.column_types.STRING_COLUMNS or self._is_potential_id(
                    column, df[column]
                ):
                    clean_df[column] = df[column].fillna("").astype(str)
                    schema.append(bigquery.SchemaField(column, "STRING"))
                    continue

                # Check for date columns
                if column in self.column_types.DATE_COLUMNS:
                    try:
                        clean_df[column] = pd.to_datetime(df[column], errors="coerce")
                        schema.append(bigquery.SchemaField(column, "DATETIME"))
                        continue
                    except:
                        pass  # Try other type checks

                # For remaining columns, check numeric conversion
                non_null_values = df[column].dropna()
                if len(non_null_values) == 0:
                    # Empty column - default to STRING
                    clean_df[column] = df[column].fillna("").astype(str)

                    schema.append(bigquery.SchemaField(column, "STRING"))
                    continue

                # Try aggressive numeric conversion
                try:
                    # For 'object' type columns, clean the values
                    if df[column].dtype == "object":
                        cleaned_values = (
                            df[column]
                            .astype(str)
                            .str.replace("R$", "", regex=False)
                            .str.replace(",", ".", regex=False)
                            .str.strip()
                        )
                        numeric_series = pd.to_numeric(cleaned_values, errors="coerce")
                    else:
                        # Already numeric column
                        numeric_series = df[column]

                    # Check if most non-null values could be converted successfully
                    valid_numeric_count = numeric_series.notna().sum()
                    original_non_null_count = df[column].notna().sum()

                    # If we lost less than 10% of values, consider it numeric
                    if valid_numeric_count >= original_non_null_count * 0.99:
                        # Check if all valid values are integers
                        valid_values = numeric_series.dropna()
                        if len(valid_values) > 0 and valid_values.equals(
                            valid_values.astype(int)
                        ):
                            # Integer column with proper null handling
                            clean_df[column] = numeric_series.astype("Int64")
                            schema.append(bigquery.SchemaField(column, "INTEGER"))
                        else:
                            # Float column
                            clean_df[column] = numeric_series
                            schema.append(bigquery.SchemaField(column, "FLOAT"))
                    else:
                        # Too many non-numeric values - treat as string
                        clean_df[column] = df[column].fillna("").astype(str)
                        schema.append(bigquery.SchemaField(column, "STRING"))
                except Exception as e:
                    self.logger.warning(
                        f"Failed to convert {column} to numeric: {str(e)}"
                    )
                    clean_df[column] = df[column].fillna("").astype(str)
                    schema.append(bigquery.SchemaField(column, "STRING"))

            # Step 4: Double-check numeric columns for any remaining issues
            for col, field in zip(clean_df.columns, schema):
                if field.field_type in ["FLOAT", "INTEGER"]:
                    # Ensure there are no string values
                    clean_df[col] = pd.to_numeric(
                        clean_df[col].replace(["", "nan", "<NA>"], np.nan),
                        errors="coerce",
                    )

            # Step 5: Log information for debugging
            self.logger.info(f"Prepared {len(clean_df.columns)} columns for BigQuery")
            self.logger.info(f"Schema types: {[f.field_type for f in schema]}")

            # Step 6: Upload to BigQuery
            table_id = f"{self.project_id}.{dataset_id}.{table_name}"
            job_config = bigquery.LoadJobConfig(
                schema=schema,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            )

            job = self.client.load_table_from_dataframe(
                clean_df, table_id, job_config=job_config
            )
            job.result()

            self.logger.info(
                f"Successfully loaded {table_name} to dataset {dataset_id}"
            )
            return True

        except Exception as e:
            self.logger.error(
                f"Error loading {table_name} to dataset {dataset_id}: {str(e)}"
            )
            return False

    def process_wave(
        self, wave_number: int, base_path: str, file_mappings: Dict[str, str]
    ) -> Dict[str, bool]:
        """
        Process all files for a specific wave.

        Args:
            wave_number: Wave number to process
            base_path: Base path containing the files
            file_mappings: Dictionary mapping file prefixes to table names

        Returns:
            Dictionary of load results by table
        """
        dataset_id = f"efm_microdados_onda_{wave_number}"
        wave_path = os.path.join(base_path, str(wave_number))
        results = {}

        for file_prefix, table_name in file_mappings.items():
            for ext in [".csv", ".CSV"]:
                file_path = os.path.join(wave_path, f"{file_prefix}{ext}")
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    results[table_name] = self.load_table(df, dataset_id, table_name)
                    break
            else:
                self.logger.warning(f"File not found: {file_prefix}[.csv/.CSV]")
                results[table_name] = False

        return results

    def process_with_schools(self, base_path: str) -> Dict[str, bool]:
        """
        Process files from the with_schools folder.

        Args:
            base_path: Base path containing the files

        Returns:
            Dictionary of load results by table
        """
        dataset_id = "efm_treated"
        file_mappings = {
            "alunos": "alunos",
            "docentes": "docentes",
            "gestores": "gestores",
            "internet": "internet",
        }

        results = {}

        for file_prefix, table_name in file_mappings.items():
            file_path = os.path.join(base_path, file_prefix)
            self.logger.info(f"Attempting to read file: {file_path}")

            for ext in ["", ".csv", ".CSV"]:
                full_path = f"{file_path}{ext}"
                if os.path.exists(full_path):
                    self.logger.info(f"File found: {full_path}")
                    df = pd.read_csv(full_path)
                    results[table_name] = self.load_table(df, dataset_id, table_name)
                    break
            else:
                self.logger.warning(f"File not found: {file_path}[.csv/.CSV]")
                results[table_name] = False

        return results
    
    def load_incremental(self, df: pd.DataFrame, dataset_id: str, table_name: str) -> bool:
        """
        Carrega dados de forma incremental (append) para uma tabela do BigQuery.
        Mesma assinatura do load_table, mas faz append em vez de sobrescrever.
        
        Args:
            df: DataFrame com os dados a serem carregados
            dataset_id: ID do dataset no BigQuery
            table_name: Nome da tabela
        
        Returns:
            bool: True se o carregamento foi bem-sucedido, False caso contrário
        """
        try:
            df = df.copy()
            
            # Limpar nomes das colunas (mesmo processo do load_table)
            df.columns = df.columns.str.strip()
            df.columns = df.columns.str.replace('[^0-9a-zA-Z_]', '_', regex=True)
            df.columns = df.columns.str.replace('__+', '_', regex=True)
            df.columns = df.columns.str.rstrip('_')

            self.logger.info(f"Colunas após limpeza: {list(df.columns)}")
            
            # Configurar a tabela de destino
            table_id = f"{self.project_id}.{dataset_id}.{table_name}"
            
            # Verificar se a tabela existe para decidir o schema
            try:
                table = self.client.get_table(table_id)
                # Tabela existe - usar schema existente
                existing_schema = table.schema
                df = self._align_dataframe_to_existing_schema(df, existing_schema)
                schema = existing_schema
                self.logger.info(f"Tabela {table_name} já existe. Fazendo append dos dados.")
                
            except Exception:
                # Tabela não existe - inferir schema como no load_table
                df, schema = self.infer_and_convert_types(df)
                self.logger.info(f"Tabela {table_name} não existe. Criando nova tabela.")
            
            # Configurar job de carregamento para APPEND
            job_config = bigquery.LoadJobConfig(
                schema=schema,
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND
            )
            
            # Carregar dados para o BigQuery
            job = self.client.load_table_from_dataframe(
                df, table_id, job_config=job_config
            )
            job.result()
            
            self.logger.info(f"Dados carregados incrementalmente na tabela {table_name} "
                            f"no dataset {dataset_id}! {len(df)} registros adicionados.")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar incrementalmente {table_name} "
                            f"no dataset {dataset_id}: {str(e)}")
            return False

    def _align_dataframe_to_existing_schema(self, df: pd.DataFrame, schema: List[bigquery.SchemaField]) -> pd.DataFrame:
        """
        Alinha o DataFrame ao schema existente da tabela para garantir compatibilidade.
        """
        for field in schema:
            column_name = field.name
            field_type = field.field_type
            
            if column_name in df.columns:
                # Converter coluna existente para o tipo correto baseado no schema
                if field_type == 'STRING' or column_name in self.string_columns:
                    df[column_name] = df[column_name].fillna('').astype(str)
                elif field_type in ['INTEGER', 'INT64']:
                    df[column_name] = pd.to_numeric(df[column_name], errors='coerce').astype('Int64')
                elif field_type in ['FLOAT', 'FLOAT64']:
                    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
                elif field_type in ['DATETIME', 'TIMESTAMP'] or column_name in self.date_columns:
                    try:
                        df[column_name] = pd.to_datetime(df[column_name], errors='coerce')
                    except:
                        df[column_name] = df[column_name].fillna('').astype(str)
        
        return df
    
    def close(self):
        """Fecha a conexão com o Storage"""
        if self.client:
            try:
                self.client.close()
                self.client = None
                logging.info("Cliente Storage fechado com sucesso")
            except Exception as e:
                logging.error(f"Erro ao fechar cliente Storage: {str(e)}")
                raise
# Exemplo de uso:
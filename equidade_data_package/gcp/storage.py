"""Google Cloud Storage utilities for reading and writing data files."""

import pandas as pd
import io
import logging
from typing import Dict, List, Optional, Union, Any
from google.oauth2 import service_account
from google.cloud import storage
from pathlib import Path


class StorageService:
    """Service for managing Google Cloud Storage client connections."""

    def __init__(self, credentials_dict: Dict):
        """
        Initialize the Storage Service.

        Args:
            credentials_dict: GCP service account credentials as dictionary
        """
        self.credentials_dict = credentials_dict
        self._client = None

    def get_client(self) -> storage.Client:
        """
        Get or create a Storage client.

        Returns:
            storage.Client: Authenticated Google Cloud Storage client
        """
        if not self._client:
            try:
                logging.info("Iniciando criação do cliente Storage...")
                credentials = service_account.Credentials.from_service_account_info(
                    self.credentials_dict
                )
                self._client = storage.Client(credentials=credentials)
                logging.info("Cliente Storage construído com sucesso")
            except Exception as e:
                logging.error(f"Erro ao criar cliente Storage: {str(e)}")
                raise
        return self._client

    def close(self) -> None:
        """Close the Storage client connection."""
        if self._client:
            try:
                self._client.close()
                self._client = None
                logging.info("Cliente Storage fechado com sucesso")
            except Exception as e:
                logging.error(f"Erro ao fechar cliente Storage: {str(e)}")
                raise


class DataFromStorage:
    """Class for reading and writing data files to/from Google Cloud Storage."""

    def __init__(self, storage_service: StorageService):
        """
        Initialize DataFromStorage.

        Args:
            storage_service: StorageService instance for client management
        """
        self.storage_service = storage_service

    def download_file(self, bucket_name: str, blob_path: str) -> io.BytesIO:
        """
        Download a file from Google Cloud Storage into memory.

        Args:
            bucket_name: Name of the bucket
            blob_path: Path to the file within the bucket

        Returns:
            io.BytesIO: File contents as a bytes buffer

        Raises:
            Exception: If download fails
        """
        try:
            client = self.storage_service.get_client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_path)

            file_buffer = io.BytesIO()
            blob.download_to_file(file_buffer)
            file_buffer.seek(0)

            return file_buffer

        except Exception as e:
            raise Exception(f"Erro ao baixar arquivo: {str(e)}")

    def read_parquet(self, bucket_name: str, blob_path: str) -> pd.DataFrame:
        """
        Read a Parquet file from Google Cloud Storage.

        Args:
            bucket_name: Name of the bucket
            blob_path: Path to the file within the bucket

        Returns:
            pd.DataFrame: DataFrame with the Parquet file data

        Raises:
            Exception: If reading fails
        """
        try:
            file_buffer = self.download_file(bucket_name, blob_path)
            return pd.read_parquet(file_buffer)

        except Exception as e:
            raise Exception(f"Erro ao ler arquivo Parquet: {str(e)}")

    def load_data(
        self,
        bucket_name: str,
        blob_path: str,
        file_type: Optional[str] = None,
        **kwargs,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Load data from various file types in Google Cloud Storage.

        Args:
            bucket_name: Name of the bucket
            blob_path: Path to the file within the bucket
            file_type: Type of file ('parquet', 'csv', 'excel', 'json')
                      If None, will be inferred from extension
            **kwargs: Additional arguments to pass to specific reader functions

        Returns:
            Union[pd.DataFrame, Dict]: DataFrame or dictionary with loaded data

        Raises:
            ValueError: If file type is not supported
            Exception: If loading fails
        """
        try:
            # If file_type not specified, infer from extension
            if file_type is None:
                file_type = Path(blob_path).suffix.lower().replace(".", "")

            file_type = file_type.lower()
            file_buffer = self.download_file(bucket_name, blob_path)

            # Dictionary of read functions for each file type
            readers = {
                "parquet": lambda buf, **kw: pd.read_parquet(buf, **kw),
                "csv": lambda buf, **kw: pd.read_csv(
                    buf, encoding="utf-8", on_bad_lines="skip", **kw
                ),
                "excel": lambda buf, **kw: pd.read_excel(buf, **kw),
                "xlsx": lambda buf, **kw: pd.read_excel(buf, **kw),
                "xls": lambda buf, **kw: pd.read_excel(buf, **kw),
                "json": lambda buf, **kw: pd.read_json(buf, **kw),
            }

            if file_type not in readers:
                raise ValueError(
                    f"Tipo de arquivo não suportado: {file_type}. "
                    f"Tipos suportados: {', '.join(readers.keys())}"
                )

            logging.info(f"Carregando arquivo {blob_path} do tipo {file_type}")
            return readers[file_type](file_buffer, **kwargs)

        except Exception as e:
            logging.error(f"Erro ao carregar dados: {str(e)}")
            raise

    def upload_file(
        self, bucket_name: str, blob_path: str, file_buffer: io.BytesIO
    ) -> None:
        """
        Upload a file buffer to Google Cloud Storage.

        Args:
            bucket_name: Name of the bucket
            blob_path: Path to the file within the bucket
            file_buffer: Buffer containing the file data

        Raises:
            Exception: If upload fails
        """
        try:
            client = self.storage_service.get_client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_path)

            file_buffer.seek(0)
            blob.upload_from_file(file_buffer)
            logging.info(f"Arquivo salvo com sucesso em gs://{bucket_name}/{blob_path}")

        except Exception as e:
            raise Exception(f"Erro ao fazer upload do arquivo: {str(e)}")

    def save_data(
        self,
        data: Union[pd.DataFrame, dict],
        bucket_name: str,
        blob_path: str,
        file_type: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Save data in various formats to Google Cloud Storage.

        Args:
            data: DataFrame or dictionary to save
            bucket_name: Name of the bucket
            blob_path: Path to the file within the bucket
            file_type: Type of file ('parquet', 'csv', 'excel', 'json')
                      If None, will be inferred from extension
            **kwargs: Additional arguments to pass to specific writer functions

        Raises:
            ValueError: If file type is not supported
            Exception: If saving fails
        """
        try:
            # If file_type not specified, infer from extension
            if file_type is None:
                file_type = Path(blob_path).suffix.lower().replace(".", "")

            file_type = file_type.lower()
            file_buffer = io.BytesIO()

            # Convert dict to DataFrame if necessary
            if isinstance(data, dict):
                data = pd.DataFrame.from_dict(data)

            # Dictionary of write functions for each file type
            writers = {
                "parquet": lambda df, buf, **kw: df.to_parquet(buf, **kw),
                "csv": lambda df, buf, **kw: df.to_csv(
                    buf, index=False, encoding="utf-8", **kw
                ),
                "excel": lambda df, buf, **kw: df.to_excel(buf, index=False, **kw),
                "xlsx": lambda df, buf, **kw: df.to_excel(buf, index=False, **kw),
                "json": lambda df, buf, **kw: df.to_json(buf, **kw),
            }

            if file_type not in writers:
                raise ValueError(
                    f"Tipo de arquivo não suportado: {file_type}. "
                    f"Tipos suportados: {', '.join(writers.keys())}"
                )

            logging.info(f"Salvando arquivo {blob_path} do tipo {file_type}")
            writers[file_type](data, file_buffer, **kwargs)

            # Upload file to bucket
            self.upload_file(bucket_name, blob_path, file_buffer)

        except Exception as e:
            logging.error(f"Erro ao salvar dados: {str(e)}")
            raise

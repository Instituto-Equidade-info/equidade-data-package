"""Google Drive utilities for reading files and spreadsheets."""

import pandas as pd
import io
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


class DriveService:
    """Service for managing Google Drive API connections."""

    def __init__(self, credentials_dict: Dict):
        """
        Initialize the Drive Service.

        Args:
            credentials_dict: GCP service account credentials as dictionary
        """
        self.SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
        self.credentials_dict = credentials_dict
        self._service = None

    def get_service(self):
        """
        Get or create a Drive service instance.

        Returns:
            googleapiclient.discovery.Resource: Authenticated Google Drive service
        """
        if not self._service:
            try:
                logging.info("Iniciando criação do serviço Drive...")
                credentials = service_account.Credentials.from_service_account_info(
                    self.credentials_dict, scopes=self.SCOPES
                )
                self._service = build("drive", "v3", credentials=credentials)
                logging.info("Serviço Drive construído com sucesso")
            except Exception as e:
                logging.error(f"Erro ao criar serviço Drive: {str(e)}")
                raise
        return self._service


class DataFromDrive:
    """Class for reading and processing files from Google Drive."""

    def __init__(self, drive_service: DriveService):
        """
        Initialize DataFromDrive.

        Args:
            drive_service: DriveService instance for API management
        """
        self.drive_service = drive_service

    def download_file(self, file_id: str, force_csv: bool = False) -> io.BytesIO:
        """
        Download a file from Google Drive into memory.

        Args:
            file_id: ID of the file in Google Drive
            force_csv: If True, export Google Sheets as CSV instead of Excel

        Returns:
            io.BytesIO: File contents as a bytes buffer

        Raises:
            Exception: If download fails
        """
        try:
            service = self.drive_service.get_service()

            # Get file metadata to check type
            file = service.files().get(fileId=file_id, fields="mimeType").execute()
            mime_type = file["mimeType"]

            # Special handling for Google Sheets when force_csv is True
            if force_csv and "spreadsheet" in mime_type:
                request = service.files().export_media(
                    fileId=file_id, mimeType="text/csv"
                )
            # Regular handling for other cases
            elif "google-apps" in mime_type:
                if "spreadsheet" in mime_type:
                    request = service.files().export_media(
                        fileId=file_id,
                        mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                elif "document" in mime_type:
                    request = service.files().export_media(
                        fileId=file_id, mimeType="application/pdf"
                    )
            else:
                request = service.files().get_media(fileId=file_id)

            file_buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(file_buffer, request)

            done = False
            while not done:
                _, done = downloader.next_chunk()

            file_buffer.seek(0)
            logging.info(f"Arquivo {file_id} baixado com sucesso")
            return file_buffer

        except Exception as e:
            raise Exception(f"Erro ao baixar arquivo: {str(e)}")

    def read_csv(self, file_id: str, is_sheet: bool = False) -> pd.DataFrame:
        """
        Read a CSV file from Google Drive.

        Args:
            file_id: ID of the file in Google Drive
            is_sheet: If True, treats the file as a Google Sheet

        Returns:
            pd.DataFrame: DataFrame with the CSV file data

        Raises:
            Exception: If reading fails or no supported encoding works
        """
        try:
            file_buffer = self.download_file(file_id, force_csv=is_sheet)

            # Try different encodings
            encodings = ["ISO-8859-1", "utf-8", "latin1"]
            for encoding in encodings:
                try:
                    df = pd.read_csv(
                        file_buffer,
                        sep=(
                            ";" if not is_sheet else ","
                        ),  # Google Sheets exports use comma as separator
                        encoding=encoding,
                        dtype="string",
                        on_bad_lines="skip",
                    )
                    logging.info(
                        f"Arquivo {file_id} lido com sucesso usando encoding {encoding}"
                    )
                    return df
                except UnicodeDecodeError:
                    file_buffer.seek(0)
                    continue

            raise Exception("Could not read file with any supported encoding")

        except Exception as e:
            logging.error(f"Erro ao ler CSV: {str(e)}")
            raise

    def read_excel_tabs(
        self,
        file_id: str,
        sheet_names: List[str],
        column_names: List[str],
        skiprows: int = 4,
    ) -> pd.DataFrame:
        """
        Read multiple tabs from an Excel file and concatenate results.

        Args:
            file_id: ID of the file in Google Drive
            sheet_names: List of sheet names to process
            column_names: List of column names for the DataFrame
            skiprows: Number of rows to skip at the beginning (default: 4)

        Returns:
            pd.DataFrame: Concatenated DataFrame with data from all sheets

        Raises:
            Exception: If reading fails
        """
        try:
            file_buffer = self.download_file(file_id)
            df_concatenado = pd.DataFrame()

            for aba in sheet_names:
                df_aba = pd.read_excel(
                    file_buffer,
                    sheet_name=aba,
                    skiprows=skiprows,
                    names=column_names,
                    dtype="string",
                )

                df_aba["panel"] = aba
                if aba == "Internet":
                    df_aba = df_aba.iloc[:-3]

                df_concatenado = pd.concat([df_concatenado, df_aba])

            df_concatenado = df_concatenado.reset_index(drop=True)
            df_concatenado["panel"] = df_concatenado["panel"].str.lower()

            logging.info(
                f"Lidas {len(sheet_names)} abas do arquivo {file_id} com sucesso"
            )
            return df_concatenado

        except Exception as e:
            logging.error(f"Erro ao ler abas do Excel: {str(e)}")
            raise

    def list_files_in_folder(
        self,
        folder_id: str,
        fields: Optional[List[str]] = None,
        page_size: int = 100,
        include_trashed: bool = False,
    ) -> List[Dict]:
        """
        List all files in a Google Drive folder.

        Args:
            folder_id: ID of the folder in Google Drive
            fields: List of fields to return for each file.
                    Default: ["id", "name", "mimeType"]
                    Available: id, name, mimeType, size, createdTime, modifiedTime,
                              owners, parents, webViewLink, etc.
            page_size: Number of files per page (max 1000)
            include_trashed: Whether to include trashed files

        Returns:
            List[Dict]: List of file metadata dictionaries

        Raises:
            Exception: If listing fails
        """
        try:
            service = self.drive_service.get_service()

            if fields is None:
                fields = ["id", "name", "mimeType"]

            fields_str = f"nextPageToken, files({', '.join(fields)})"

            query = f"'{folder_id}' in parents"
            if not include_trashed:
                query += " and trashed = false"

            all_files = []
            page_token = None

            while True:
                response = (
                    service.files()
                    .list(
                        q=query,
                        pageSize=page_size,
                        fields=fields_str,
                        pageToken=page_token,
                    )
                    .execute()
                )

                files = response.get("files", [])
                all_files.extend(files)

                page_token = response.get("nextPageToken")
                if not page_token:
                    break

            logging.info(
                f"Listados {len(all_files)} arquivos da pasta {folder_id}"
            )
            return all_files

        except Exception as e:
            logging.error(f"Erro ao listar arquivos da pasta: {str(e)}")
            raise

    def get_file_by_id(self, file_id: str, fields: Optional[List[str]] = None) -> Dict:
        """
        Get file metadata by its ID.

        Args:
            file_id: ID of the file in Google Drive
            fields: List of fields to return.
                    Default: ["id", "name", "mimeType", "size", "modifiedTime"]

        Returns:
            Dict: File metadata dictionary

        Raises:
            Exception: If fetching fails
        """
        try:
            service = self.drive_service.get_service()

            if fields is None:
                fields = ["id", "name", "mimeType", "size", "modifiedTime"]

            fields_str = ", ".join(fields)

            file_metadata = (
                service.files().get(fileId=file_id, fields=fields_str).execute()
            )

            logging.info(f"Metadados do arquivo {file_id} obtidos com sucesso")
            return file_metadata

        except Exception as e:
            logging.error(f"Erro ao obter metadados do arquivo: {str(e)}")
            raise

    def list_files_modified_after(
        self,
        folder_id: str,
        modified_after: Union[str, datetime],
        fields: Optional[List[str]] = None,
        page_size: int = 100,
    ) -> List[Dict]:
        """
        List files in a folder modified after a specific date.

        Args:
            folder_id: ID of the folder in Google Drive
            modified_after: Date threshold. Can be:
                           - datetime object
                           - ISO format string (e.g., "2024-01-15T00:00:00")
                           - Simple date string (e.g., "2024-01-15")
            fields: List of fields to return for each file.
                    Default: ["id", "name", "mimeType", "modifiedTime"]
            page_size: Number of files per page (max 1000)

        Returns:
            List[Dict]: List of file metadata dictionaries sorted by modifiedTime

        Raises:
            Exception: If listing fails
        """
        try:
            service = self.drive_service.get_service()

            # Convert datetime to RFC 3339 format
            if isinstance(modified_after, datetime):
                date_str = modified_after.strftime("%Y-%m-%dT%H:%M:%S")
            elif isinstance(modified_after, str):
                # Handle simple date format
                if "T" not in modified_after:
                    date_str = f"{modified_after}T00:00:00"
                else:
                    date_str = modified_after
            else:
                raise ValueError(
                    "modified_after deve ser datetime ou string no formato ISO"
                )

            if fields is None:
                fields = ["id", "name", "mimeType", "modifiedTime"]

            # Ensure modifiedTime is in fields for sorting
            if "modifiedTime" not in fields:
                fields = fields + ["modifiedTime"]

            fields_str = f"nextPageToken, files({', '.join(fields)})"

            query = (
                f"'{folder_id}' in parents "
                f"and modifiedTime > '{date_str}' "
                f"and trashed = false"
            )

            all_files = []
            page_token = None

            while True:
                response = (
                    service.files()
                    .list(
                        q=query,
                        pageSize=page_size,
                        fields=fields_str,
                        orderBy="modifiedTime desc",
                        pageToken=page_token,
                    )
                    .execute()
                )

                files = response.get("files", [])
                all_files.extend(files)

                page_token = response.get("nextPageToken")
                if not page_token:
                    break

            logging.info(
                f"Encontrados {len(all_files)} arquivos modificados após {date_str}"
            )
            return all_files

        except Exception as e:
            logging.error(f"Erro ao listar arquivos por data: {str(e)}")
            raise

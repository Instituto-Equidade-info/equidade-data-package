"""Google Drive utilities for reading files and spreadsheets."""

import pandas as pd
import io
import logging
from typing import Dict, List, Optional
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

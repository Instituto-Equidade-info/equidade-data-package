"""
Environment variable loader for Equidade projects.

Loads environment variables from:
1. YAML configuration file (env-shared.yaml)
2. GCP Secret Manager (for sensitive data)
3. Runtime environment variables (highest priority)

Usage:
    from equidade_data_package.config import EnvLoader

    # Initialize loader
    env = EnvLoader(
        function_name="equidade-download-data",
        project_id="equidade"
    )

    # Get environment variables
    slack_token = env.get("SLACK_BOT_TOKEN")
    credentials = env.get_json("CREDENTIALS")

    # Set all env vars for current process
    env.set_environment()
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


@dataclass
class EnvConfig:
    """Configuration for environment loader."""

    function_name: str
    project_id: str = "equidade"
    region: str = "southamerica-east1"
    yaml_path: Optional[str] = None
    use_secret_manager: bool = True
    cache_secrets: bool = True


class EnvLoader:
    """
    Load environment variables from YAML and GCP Secret Manager.

    This class provides a centralized way to manage environment variables
    across multiple Cloud Functions, reducing duplication and ensuring
    consistency.

    Attributes:
        config: EnvConfig with loader configuration
        _env_vars: Cached environment variables
        _secrets_cache: Cached secrets from Secret Manager
    """

    # Mapeamento de variáveis de ambiente por Cloud Function
    # Baseado na análise das variáveis usadas em cada função
    FUNCTION_ENV_MAP = {
        "equidade-download-data": [
            "CREDENTIALS",
            "LOG_EXECUTION_ID",
            "SLACK_BOT_TOKEN",
        ],
        "access-processor": [
            "BIGQUERY_DATASET_ACCESS",
            "BIGQUERY_TABLE_LOGS",
            "BIGQUERY_TABLE_REQUESTS",
            "DOCUSIGN_ACCOUNT_ID",
            "DOCUSIGN_API_BASE_URL",
            "DOCUSIGN_BASE_URL",
            "DOCUSIGN_CLIENT_SECRET",
            "DOCUSIGN_ENVIRONMENT",
            "DOCUSIGN_INTEGRATION_KEY",
            "DOCUSIGN_TEMPLATE_DASH",
            "DOCUSIGN_TEMPLATE_DATA",
            "DOCUSIGN_TEMPLATE_TEMP",
            "ENVIRONMENT",
            "GCP_PROJECT_ID",
            "GCP_REGION",
            "GCP_WEBHOOK_URL",
            "GMAIL_IMPERSONATE_USER",
            "GMAIL_TOKEN_DATA",
            "GOOGLE_DRIVE_FOLDER_EDITAIS",
            "GOOGLE_SERVICE_ACCOUNT_KEY",
            "SLACK_BOT_TOKEN_ACCESS",
            "SLACK_CHANNEL_ACCESS_LOGS",
            "STRAPI_BASE_URL",
            "STRAPI_TOKEN",
        ],
        "etl-surveycto-function": [
            "AWS_ACCESS_KEY_ID",
            "AWS_REGION",
            "AWS_SECRET_ACCESS_KEY",
            "CREDENTIALS",
            "SURVEYCTO_PASSWORD",
            "SURVEYCTO_SERVER",
            "SURVEYCTO_USERNAME",
        ],
        "check-s3-files": [
            "AWS_ACCESS_KEY_ID",
            "AWS_REGION",
            "AWS_SECRET_ACCESS_KEY",
            "CREDENTIALS",
            "DATA_PROCESSING_TOPIC",
            "GCP_PROJECT",
            "SLACK_BOT_TOKEN",
            "SLACK_CHANNEL",
        ],
        "iu-process-dataset-updates": [
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "CREDENTIALS",
            "SLACK_BOT_TOKEN",
        ],
        "consistency_checker_function": [
            "AUTORIZATION_BLIP",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "CREDENTIALS",
            "SLACK_BOT_TOKEN",
        ],
        "access-manager": [
            "BIGQUERY_DATASET_ACCESS",
            "BIGQUERY_TABLE_LOGS",
            "BIGQUERY_TABLE_REQUESTS",
            "DOCUSIGN_ACCOUNT_ID",
            "DOCUSIGN_API_BASE_URL",
            "DOCUSIGN_BASE_URL",
            "DOCUSIGN_CLIENT_SECRET",
            "DOCUSIGN_ENVIRONMENT",
            "DOCUSIGN_INTEGRATION_KEY",
            "DOCUSIGN_TEMPLATE_DASH",
            "DOCUSIGN_TEMPLATE_DATA",
            "DOCUSIGN_TEMPLATE_TEMP",
            "ENVIRONMENT",
            "GCP_PROJECT_ID",
            "GCP_REGION",
            "GCP_WEBHOOK_URL",
            "GMAIL_IMPERSONATE_USER",
            "GMAIL_TOKEN_DATA",
            "GOOGLE_DRIVE_FOLDER_EDITAIS",
            "GOOGLE_SERVICE_ACCOUNT_KEY",
            "SLACK_BOT_TOKEN_ACCESS",
            "SLACK_CHANNEL_ACCESS_LOGS",
            "STRAPI_BASE_URL",
            "STRAPI_TOKEN",
        ],
        "access-revocation": [
            "BIGQUERY_DATASET_ACCESS",
            "BIGQUERY_TABLE_LOGS",
            "BIGQUERY_TABLE_REQUESTS",
            "DOCUSIGN_ACCOUNT_ID",
            "DOCUSIGN_API_BASE_URL",
            "DOCUSIGN_BASE_URL",
            "DOCUSIGN_CLIENT_SECRET",
            "DOCUSIGN_ENVIRONMENT",
            "DOCUSIGN_INTEGRATION_KEY",
            "DOCUSIGN_TEMPLATE_DASH",
            "DOCUSIGN_TEMPLATE_DATA",
            "DOCUSIGN_TEMPLATE_TEMP",
            "ENVIRONMENT",
            "GCP_PROJECT_ID",
            "GCP_REGION",
            "GCP_WEBHOOK_URL",
            "GMAIL_IMPERSONATE_USER",
            "GMAIL_TOKEN_DATA",
            "GOOGLE_DRIVE_FOLDER_EDITAIS",
            "GOOGLE_SERVICE_ACCOUNT_KEY",
            "SLACK_BOT_TOKEN_ACCESS",
            "SLACK_CHANNEL_ACCESS_LOGS",
            "STRAPI_BASE_URL",
            "STRAPI_TOKEN",
        ],
        "check-and-trigger-deploy": [
            "MAX_WAITING_TIME",
            "MIN_UPDATES_TO_TRIGGER",
            "PROJECT_ID",
            "SLACK_BOT_TOKEN",
            "TOKEN_GITHUB",
        ],
        "process-table-update": [
            "MAX_WAITING_TIME",
            "MIN_UPDATES_TO_TRIGGER",
            "PROJECT_ID",
            "SLACK_BOT_TOKEN",
            "TOKEN_GITHUB",
        ],
        "gf_raw_data_function": [
            "AUTHORIZATION_KEY_BLIP",
            "CREDENTIALS",
            "SLACK_BOT_TOKEN",
            "SURVEYCTO_PASSWORD",
            "SURVEYCTO_SERVER",
            "SURVEYCTO_USERNAME",
        ],
        "gf_treatment_data_function": [
            "CREDENTIALS",
            "SLACK_BOT_TOKEN",
        ],
        "process-dataset-updates": [
            "CREDENTIALS",
            "CSV_FILE_ID",
            "DICT_ESCOLA",
            "EXCEL_FILE_ID",
            "SLACK_BOT_TOKEN",
        ],
        "slack-notifier": [
            "BIGQUERY_DATASET_ACCESS",
            "BIGQUERY_TABLE_LOGS",
            "BIGQUERY_TABLE_REQUESTS",
            "DOCUSIGN_ACCOUNT_ID",
            "DOCUSIGN_API_BASE_URL",
            "DOCUSIGN_BASE_URL",
            "DOCUSIGN_CLIENT_SECRET",
            "DOCUSIGN_ENVIRONMENT",
            "DOCUSIGN_INTEGRATION_KEY",
            "DOCUSIGN_TEMPLATE_DASH",
            "DOCUSIGN_TEMPLATE_DATA",
            "DOCUSIGN_TEMPLATE_TEMP",
            "ENVIRONMENT",
            "GCP_PROJECT_ID",
            "GCP_REGION",
            "GCP_WEBHOOK_URL",
            "GMAIL_IMPERSONATE_USER",
            "GMAIL_TOKEN_DATA",
            "GOOGLE_DRIVE_FOLDER_EDITAIS",
            "GOOGLE_SERVICE_ACCOUNT_KEY",
            "SLACK_BOT_TOKEN_ACCESS",
            "SLACK_CHANNEL_ACCESS_LOGS",
            "STRAPI_BASE_URL",
            "STRAPI_TOKEN",
        ],
        "docusign-webhook": [
            "BIGQUERY_DATASET_ACCESS",
            "BIGQUERY_TABLE_LOGS",
            "BIGQUERY_TABLE_REQUESTS",
            "DOCUSIGN_ACCOUNT_ID",
            "DOCUSIGN_API_BASE_URL",
            "DOCUSIGN_BASE_URL",
            "DOCUSIGN_CLIENT_SECRET",
            "DOCUSIGN_ENVIRONMENT",
            "DOCUSIGN_INTEGRATION_KEY",
            "DOCUSIGN_TEMPLATE_DASH",
            "DOCUSIGN_TEMPLATE_DATA",
            "DOCUSIGN_TEMPLATE_TEMP",
            "ENVIRONMENT",
            "GCP_PROJECT_ID",
            "GCP_REGION",
            "GCP_WEBHOOK_URL",
            "GMAIL_IMPERSONATE_USER",
            "GMAIL_TOKEN_DATA",
            "GOOGLE_DRIVE_FOLDER_EDITAIS",
            "GOOGLE_SERVICE_ACCOUNT_KEY",
            "SLACK_BOT_TOKEN_ACCESS",
            "SLACK_CHANNEL_ACCESS_LOGS",
            "STRAPI_BASE_URL",
            "STRAPI_TOKEN",
        ],
        "pi_treatment_data_function": [
            "CREDENTIALS",
            "SLACK_BOT_TOKEN",
        ],
        "pi_raw_data_function": [
            "AUTHORIZATION_KEY_BLIP",
            "CREDENTIALS",
            "SLACK_BOT_TOKEN",
            "SURVEYCTO_PASSWORD",
            "SURVEYCTO_SERVER",
            "SURVEYCTO_USERNAME",
        ],
        "stf-etl-qualtrics": ["SURVEY_ID",
                                "API_URL_BASE",
                                "QUALTRICS_API_TOKEN",
                                "NOME_ARQUIVO_CSV_NO_ZIP",
                                "CAMINHO_DADOS",
                                "NOME_ARQUIVO_FINAL",
                                "CAMINHO_ARQUIVO_FINAL",
                                "CREDENTIALS",
                            ],
    }

    # Mapeamento de variáveis de ambiente para nomes de secrets no Secret Manager
    # Secrets com sufixos específicos por função para evitar conflitos
    SECRET_NAME_MAP = {
        # Secrets compartilhados (sem sufixo) 
        "DOCUSIGN_CLIENT_SECRET": "docusign-client-secret",
        "DOCUSIGN_INTEGRATION_KEY": "docusign-integration-key",
        "GMAIL_TOKEN_DATA": "gmail-token-data",
        "GOOGLE_SERVICE_ACCOUNT_KEY": "google-service-account-key",
        "SLACK_BOT_TOKEN_ACCESS": "slack-bot-token-access",
        "STRAPI_TOKEN": "strapi-token",
        "QUALTRICS_API_TOKEN": "qualtrics-api-token",
        "AWS_ACCESS_KEY_ID": "aws-access-key-id",
        "AWS_SECRET_ACCESS_KEY": "aws-secret-access-key",
        "SURVEYCTO_PASSWORD": "surveycto-password",
        "TOKEN_GITHUB": "token-github",
        "CREDENTIALS": "credentials-pi-raw-data-function",
        "SLACK_BOT_TOKEN" : "slack-bot-token-consistency-checker-function",
        # Secrets específicos por função (com sufixo)
        "CREDENTIALS_equidade-download-data": "credentials-equidade-download-data",
        "CREDENTIALS_pi_raw_data_function": "credentials-pi-raw-data-function",
        "SLACK_BOT_TOKEN_equidade-download-data": "slack-bot-token-equidade-download-data",
        "SLACK_BOT_TOKEN_consistency_checker_function": "slack-bot-token-consistency-checker-function",
        "AUTHORIZATION_KEY_BLIP": "authorization-key-blip",
        "AUTORIZATION_BLIP": "authorization-key-blip",  # Typo no nome original
    }

    def __init__(self, config: EnvConfig):
        """
        Initialize EnvLoader.

        Args:
            config: EnvConfig with loader configuration
        """
        self.config = config
        self._env_vars: Dict[str, str] = {}
        self._secrets_cache: Dict[str, str] = {}
        self._secret_client = None

        # Determinar caminho do YAML
        if config.yaml_path:
            self._yaml_path = Path(config.yaml_path)
        else:
            # Tentar encontrar o YAML no pacote
            # __file__ = .../equidade_data_package/config/env_loader.py
            # parent = .../equidade_data_package/config/
            # parent.parent = .../equidade_data_package/
            package_dir = Path(__file__).parent.parent
            self._yaml_path = package_dir / "env-files" / "env-shared.yaml"

        # Carregar variáveis
        self._load_all()

    def _load_all(self):
        """Load all environment variables from YAML and Secret Manager."""
        # 1. Carregar do YAML (valores não sensíveis)
        self._load_from_yaml()

        # 2. Carregar do Secret Manager (valores sensíveis)
        if self.config.use_secret_manager:
            self._load_from_secrets()

        # 3. Runtime environment variables têm prioridade máxima
        # (já estão em os.environ, vamos respeitar isso no get())

    def _load_from_yaml(self):
        """Load environment variables from YAML file."""
        if not self._yaml_path.exists():
            print(f"⚠️  YAML file not found: {self._yaml_path}")
            print("   Continuing with Secret Manager only...")
            return

        try:
            with open(self._yaml_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f) or {}

            # Obter lista de variáveis necessárias para esta função
            required_vars = self.FUNCTION_ENV_MAP.get(self.config.function_name, [])

            for var_name in required_vars:
                # Pular secrets (serão carregados do Secret Manager)
                if self._is_secret_var(var_name):
                    continue

                # Verificar se está no YAML
                if var_name in yaml_data:
                    value = yaml_data[var_name]
                    # Converter para string se necessário
                    self._env_vars[var_name] = str(value) if not isinstance(value, str) else value

        except Exception as e:
            print(f"⚠️  Error loading YAML: {e}")
            print("   Continuing with Secret Manager only...")

    def _load_from_secrets(self):
        """Load secrets from GCP Secret Manager."""
        try:
            from google.cloud import secretmanager
        except ImportError:
            print("⚠️  google-cloud-secret-manager not installed")
            print("   Install with: pip install google-cloud-secret-manager")
            return

        try:
            if self._secret_client is None:
                self._secret_client = secretmanager.SecretManagerServiceClient()

            required_vars = self.FUNCTION_ENV_MAP.get(self.config.function_name, [])

            for var_name in required_vars:
                if not self._is_secret_var(var_name):
                    continue

                # Determinar nome do secret
                secret_name = self._get_secret_name(var_name)
                if not secret_name:
                    continue

                # Buscar do cache ou Secret Manager
                if self.config.cache_secrets and secret_name in self._secrets_cache:
                    secret_value = self._secrets_cache[secret_name]
                else:
                    secret_value = self._fetch_secret(secret_name)
                    if secret_value and self.config.cache_secrets:
                        self._secrets_cache[secret_name] = secret_value

                if secret_value:
                    self._env_vars[var_name] = secret_value

        except Exception as e:
            print(f"⚠️  Error loading secrets: {e}")

    def _is_secret_var(self, var_name: str) -> bool:
        """
        Check if variable should be loaded from Secret Manager.

        Args:
            var_name: Variable name

        Returns:
            True if variable should come from Secret Manager
        """
        # Lista de palavras-chave de variáveis sensíveis
        # Verificamos se CONTÉM (não apenas startswith) para pegar casos como:
        # - DOCUSIGN_INTEGRATION_KEY (contém "KEY")
        # - DOCUSIGN_CLIENT_SECRET (contém "SECRET")
        secret_keywords = [
            "CREDENTIALS",
            "TOKEN",
            "KEY",
            "SECRET",
            "PASSWORD",
            "AUTHORIZATION",
            "AUTORIZATION",  # Typo no nome original
        ]

        return any(keyword in var_name for keyword in secret_keywords)

    def _get_secret_name(self, var_name: str) -> Optional[str]:
        """
        Get Secret Manager secret name for environment variable.

        Args:
            var_name: Environment variable name

        Returns:
            Secret name or None if not mapped
        """
        # Tentar com sufixo específico da função primeiro
        key_with_suffix = f"{var_name}_{self.config.function_name}"
        if key_with_suffix in self.SECRET_NAME_MAP:
            return self.SECRET_NAME_MAP[key_with_suffix]

        # Tentar sem sufixo (secret compartilhado)
        if var_name in self.SECRET_NAME_MAP:
            return self.SECRET_NAME_MAP[var_name]

        # Fallback: converter para kebab-case
        return var_name.lower().replace("_", "-")

    def _fetch_secret(self, secret_name: str) -> Optional[str]:
        """
        Fetch secret from GCP Secret Manager.

        Args:
            secret_name: Secret name in Secret Manager

        Returns:
            Secret value or None if not found
        """
        try:
            name = f"projects/{self.config.project_id}/secrets/{secret_name}/versions/latest"
            response = self._secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            print(f"⚠️  Failed to fetch secret '{secret_name}': {e}")
            return None

    def get(self, var_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable value.

        Priority (highest to lowest):
        1. Runtime environment variable (os.environ)
        2. Secret Manager
        3. YAML file
        4. Default value

        Args:
            var_name: Variable name
            default: Default value if not found

        Returns:
            Variable value or default
        """
        # 1. Runtime environment (highest priority)
        if var_name in os.environ:
            return os.environ[var_name]

        # 2. Loaded values (Secret Manager or YAML)
        if var_name in self._env_vars:
            return self._env_vars[var_name]

        # 3. Default
        return default

    def get_json(self, var_name: str, default: Optional[Dict] = None) -> Optional[Dict]:
        """
        Get environment variable as JSON.

        Useful for CREDENTIALS, GMAIL_TOKEN_DATA, etc.

        Args:
            var_name: Variable name
            default: Default value if not found

        Returns:
            Parsed JSON dict or default
        """
        value = self.get(var_name)
        if value is None:
            return default

        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse JSON for '{var_name}': {e}")
            return default

    def get_int(self, var_name: str, default: Optional[int] = None) -> Optional[int]:
        """
        Get environment variable as integer.

        Args:
            var_name: Variable name
            default: Default value if not found

        Returns:
            Integer value or default
        """
        value = self.get(var_name)
        if value is None:
            return default

        try:
            return int(value)
        except ValueError as e:
            print(f"⚠️  Failed to parse int for '{var_name}': {e}")
            return default

    def get_bool(self, var_name: str, default: bool = False) -> bool:
        """
        Get environment variable as boolean.

        Accepts: true, false, 1, 0, yes, no (case-insensitive)

        Args:
            var_name: Variable name
            default: Default value if not found

        Returns:
            Boolean value or default
        """
        value = self.get(var_name)
        if value is None:
            return default

        return value.lower() in ("true", "1", "yes", "on")

    def set_environment(self):
        """
        Set all loaded variables to os.environ.

        This makes them available to the entire application.
        Call this at the start of your Cloud Function.
        """
        for var_name, value in self._env_vars.items():
            # Não sobrescrever variáveis já definidas no runtime
            if var_name not in os.environ:
                os.environ[var_name] = value

    def get_all(self) -> Dict[str, str]:
        """
        Get all loaded environment variables.

        Returns:
            Dictionary of all loaded variables
        """
        # Combinar loaded vars com os.environ (runtime tem prioridade)
        result = self._env_vars.copy()
        required_vars = self.FUNCTION_ENV_MAP.get(self.config.function_name, [])

        for var_name in required_vars:
            if var_name in os.environ:
                result[var_name] = os.environ[var_name]

        return result

    def validate(self, required_vars: Optional[list] = None) -> tuple[bool, list]:
        """
        Validate that all required variables are set.

        Args:
            required_vars: List of required variable names.
                          If None, uses FUNCTION_ENV_MAP for this function.

        Returns:
            Tuple of (is_valid, missing_vars)
        """
        if required_vars is None:
            required_vars = self.FUNCTION_ENV_MAP.get(self.config.function_name, [])

        missing = []
        for var_name in required_vars:
            if self.get(var_name) is None:
                missing.append(var_name)

        return len(missing) == 0, missing

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"EnvLoader("
            f"function={self.config.function_name}, "
            f"vars_loaded={len(self._env_vars)}, "
            f"secrets_cached={len(self._secrets_cache)}"
            f")"
        )


# Convenience function for quick setup
def load_env(
    function_name: str,
    project_id: str = "equidade",
    auto_set: bool = True,
    **kwargs,
) -> EnvLoader:
    """
    Quick setup for environment loading.

    Args:
        function_name: Name of the Cloud Function
        project_id: GCP project ID
        auto_set: Automatically set variables to os.environ
        **kwargs: Additional arguments for EnvConfig

    Returns:
        Configured EnvLoader

    Example:
        from equidade_data_package.config import load_env

        env = load_env("equidade-download-data")
        slack_token = env.get("SLACK_BOT_TOKEN")
    """
    config = EnvConfig(function_name=function_name, project_id=project_id, **kwargs)
    loader = EnvLoader(config)

    if auto_set:
        loader.set_environment()

    return loader

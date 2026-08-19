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
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


# Configuration shared by every function in the school-register flow. Defined once and
# referenced from FUNCTION_ENV_MAP, so adding a function to that flow cannot silently omit a
# variable — which is what happened to school-register-processor while these were two
# hand-copied lists.
#
# These variables live in env-files/env-shared.yaml inside this package, not in any
# repository's env-shared.yaml, so they are never deployed environment variables and cannot be
# found by inspecting a deployed function. EnvLoader._load_from_yaml is what resolves them, and
# only for the names listed here.
SCHOOL_REGISTER_VARS = [
    "GCP_PROJECT_ID",
    "GCP_REGION",
    "DOCUSIGN_TEMPLATE_SCHOOL_REGISTER",
    "DOCUSIGN_ACCOUNT_ID",
    "DOCUSIGN_API_BASE_URL",
    "DOCUSIGN_BASE_URL",
    "DOCUSIGN_CLIENT_SECRET",
    "DOCUSIGN_INTEGRATION_KEY",
    "DOCUSIGN_SIGNING_RETURN_URL",
    "SIGNING_PROXY_URL",
    "BIGQUERY_DATASET_SCHOOL_REGISTER",
    "SLACK_CHANNEL_SCHOOL_REGISTER_LOGS",
    # Deliberately absent, and do not add them back:
    #
    #   CREDENTIALS           maps to no secret on purpose, so the function falls through to
    #                         Application Default Credentials. Listing it only produces a 404
    #                         fetch and a warning on every cold start.
    #   DOCUSIGN_ACCESS_TOKEN the access token is obtained at runtime by DocuSignOAuthClient,
    #                         which reads docusign-refresh-token from Secret Manager directly.
    #                         Listed here it resolved by kebab-case guess to
    #                         "docusign-access-token", which does not exist — the real secret is
    #                         docusign-access-token-data, and nothing reads it from the env.
    #   DOCUSIGN_USER_ID      referenced by no runtime code in any function repository.
]


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
            "SURVEYCTO_PASSWORD",
            "SURVEYCTO_SERVER",
            "SURVEYCTO_USERNAME",
        ],
        "check-s3-files": [
            "AWS_ACCESS_KEY_ID",
            "AWS_REGION",
            "AWS_SECRET_ACCESS_KEY",
            "DATA_PROCESSING_TOPIC",
            "GCP_PROJECT",
            "SLACK_BOT_TOKEN",
            "SLACK_CHANNEL",
        ],
        "iu-process-dataset-updates": [
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "SLACK_BOT_TOKEN",
        ],
        "consistency_checker_function": [
            "AUTORIZATION_BLIP",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
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
            "STRAPI_TOKEN",'DOCUSIGN_SIGNING_RETURN_URL','SIGNING_PROXY_URL'
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
            "SLACK_BOT_TOKEN",
            "SURVEYCTO_PASSWORD",
            "SURVEYCTO_SERVER",
            "SURVEYCTO_USERNAME",
        ],
        "gf_treatment_data_function": [
            "SLACK_BOT_TOKEN",
        ],
        "process-dataset-updates": [
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
            # It imports SchoolRegisterLogger lazily (main.py:271), which reads this. Its
            # absence here was the second half of the same defect.
            "BIGQUERY_DATASET_SCHOOL_REGISTER",
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
            "SLACK_BOT_TOKEN",
        ],
        "pi_raw_data_function": [
            "AUTHORIZATION_KEY_BLIP",
            "SLACK_BOT_TOKEN",
            "SURVEYCTO_PASSWORD",
            "SURVEYCTO_SERVER",
            "SURVEYCTO_USERNAME",
        ],

        "stf-etl-qualtrics": ["SURVEY_ID",
                                "API_URL_BASE",
                                "QUALTRICS_API_TOKEN",
                                "SURVEYCTO_PASSWORD",
                                "SURVEYCTO_SERVER",
                                "SURVEYCTO_USERNAME",
                                "NOME_ARQUIVO_CSV_NO_ZIP",
                                "SLACK_BOT_TOKEN",
                                "SLACK_CHANNEL_FLUENCY",
                                "FORM_ID","PAVLOVIA_GITLAB_TOKEN"
                            ],


        "stf-treatment-function" : [ "SLACK_BOT_TOKEN"  ,"SURVEYCTO_SERVER",
                                "SURVEYCTO_USERNAME","SURVEYCTO_PASSWORD"],

        "twilio-functions" : [ "TWILIO_ACCOUNT_SID", "TWILIO_WHATSAPP_NUMBER", "CONTENT_SID",'TWILIO_AUTH_TOKEN' ],

    
        # The school-register functions share one configuration, defined once in
        # SCHOOL_REGISTER_VARS at the top of this module.
        #
        # It used to be two hand-copied lists, and that is exactly how
        # `school-register-processor` came to have no entry at all: the deployed function's
        # name was never one of the two anybody wrote out. It worked anyway, because
        # shared/school_register_logger.py called load_env("school-register") at import time
        # and every function importing it inherited the set. When that import-time call was
        # removed (equidade-access-cloud-functions#7), the function started failing with
        # "DOCUSIGN_TEMPLATE_SCHOOL_REGISTER não configurado" on its next invocation, acking
        # and dropping every school registration until it was found.
        #
        # "school-register" is not a deployed function. It is kept because it is the name that
        # module passed, so any caller still using it resolves the same set.
        "school-register": SCHOOL_REGISTER_VARS,
        "school-register-processor": SCHOOL_REGISTER_VARS,
        "school-register-manager": SCHOOL_REGISTER_VARS,
    }


    # Mapeamento de variáveis de ambiente para nomes de secrets no Secret Manager
    # Secrets com sufixos específicos por função para evitar conflitos
    SECRET_NAME_MAP = {
        # Secrets compartilhados (sem sufixo) 
        'TWILIO_ACCOUNT_SID': "twilio_account_sid",
        "TWILIO_AUTH_TOKEN" : "twilio_auth_token",
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
        # "CREDENTIALS" deliberately has NO shared entry. It used to map to
        # credentials-pi-raw-data-function — one function's service account key,
        # registered as the default for every function — so any function without its own
        # suffixed entry silently authenticated as bigquery-loader@ using a key we are
        # trying to retire. A function needing it must declare "CREDENTIALS_<function>".
        #
        # SLACK_BOT_TOKEN keeps its shared entry, for now. Removing it broke Slack
        # notifications for stf-etl-qualtrics and stf-treatment-function, which had been
        # relying on this fallback. The two cases are not equivalent: a shared bot token
        # is untidy, a shared service account key with admin roles is a security incident.
        # TODO: give each function its own slack-bot-token-<function> secret, then remove
        # this line too.
        "SLACK_BOT_TOKEN": "slack-bot-token-consistency-checker-function",
        # Secrets específicos por função (com sufixo).
        #
        # The CREDENTIALS_* entries were removed: they pointed at secrets holding a
        # bigquery-loader@ service account key, so a function that lost its CREDENTIALS
        # environment variable silently fetched the same key from Secret Manager instead
        # of falling back to ADC. The function kept working, which is why it went
        # unnoticed. Functions now authenticate as their own runtime identity.
        "SLACK_BOT_TOKEN_equidade-download-data": "slack-bot-token-equidade-download-data",
        "SLACK_BOT_TOKEN_consistency_checker_function": "slack-bot-token-consistency-checker-function",
        "AUTHORIZATION_KEY_BLIP": "authorization-key-blip",
        "AUTORIZATION_BLIP": "authorization-key-blip",
        "PAVLOVIA_GITLAB_TOKEN": "pavlovia-gitlab-token"  # Typo no nome original
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

        # Tentar sem sufixo (secret compartilhado).
        # Only genuinely shared secrets belong here — ones every function is meant to
        # use, like aws-access-key-id. A per-function secret registered as a shared
        # default hands one pipeline's credentials to every other pipeline.
        if var_name in self.SECRET_NAME_MAP:
            return self.SECRET_NAME_MAP[var_name]

        # Unmapped. Fall back to kebab-case, which usually resolves to a secret that does
        # not exist — the variable then comes back missing and the function fails with a
        # clear error. That is the intended outcome: borrowing another function's
        # credentials is worse than not starting.
        guess = var_name.lower().replace("_", "-")
        logging.warning(
            "No secret mapping for %r in function %r; trying %r. If this is a credential, "
            "add an explicit '%s_%s' entry to SECRET_NAME_MAP rather than relying on this "
            "guess.",
            var_name, self.config.function_name, guess, var_name, self.config.function_name,
        )
        return guess

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

    # Log the package version once per cold start. Every function calls load_env, so this
    # is the one place that can answer "which version is actually running in production?"
    # without editing 13 repositories. WARNING level because Cloud Functions does not emit
    # INFO by default — an invisible version banner solves nothing.
    try:
        from equidade_data_package import __version__ as _v

        logging.warning("equidade-data-package %s loaded for function %r", _v, function_name)
    except Exception:  # never let a diagnostic break a deploy
        pass

    if auto_set:
        loader.set_environment()

    return loader

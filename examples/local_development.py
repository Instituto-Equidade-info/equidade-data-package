"""
Example: Local Development with EnvLoader

This example shows how to use EnvLoader during local development,
where you might not have access to GCP Secret Manager.
"""

import os
from equidade_data_package.config import EnvLoader, EnvConfig


def example_local_yaml_only():
    """
    Example 1: Use only YAML file (no Secret Manager).

    Useful when developing locally without GCP credentials.
    """
    print("=== Example 1: YAML Only ===")

    config = EnvConfig(
        function_name="equidade-download-data",
        project_id="equidade",
        use_secret_manager=False,  # Disable Secret Manager
    )

    env = EnvLoader(config)

    # Get non-sensitive variables from YAML
    project_id = env.get("GCP_PROJECT_ID")
    region = env.get("GCP_REGION")
    environment = env.get("ENVIRONMENT")

    print(f"Project: {project_id}")
    print(f"Region: {region}")
    print(f"Environment: {environment}")

    # Secrets will be None (not loaded from Secret Manager)
    slack_token = env.get("SLACK_BOT_TOKEN")
    print(f"Slack token: {slack_token}")  # Will be None


def example_local_with_mock_secrets():
    """
    Example 2: Mock secrets using environment variables.

    Set secrets as env vars for local testing.
    """
    print("\n=== Example 2: Mock Secrets ===")

    # Mock secrets as environment variables
    os.environ["SLACK_BOT_TOKEN"] = "xoxb-mock-token-for-testing"
    os.environ["CREDENTIALS"] = '{"type": "service_account", "project_id": "test"}'

    config = EnvConfig(
        function_name="equidade-download-data",
        project_id="equidade",
        use_secret_manager=False,
    )

    env = EnvLoader(config)

    # Runtime env vars have highest priority
    slack_token = env.get("SLACK_BOT_TOKEN")
    credentials = env.get_json("CREDENTIALS")

    print(f"Slack token: {slack_token}")
    print(f"Credentials: {credentials}")


def example_local_with_dotenv():
    """
    Example 3: Use .env file with python-dotenv.

    Create a .env file with your local secrets.
    """
    print("\n=== Example 3: .env File ===")

    try:
        from dotenv import load_dotenv

        # Load .env file
        load_dotenv()

        config = EnvConfig(
            function_name="equidade-download-data",
            project_id="equidade",
            use_secret_manager=False,
        )

        env = EnvLoader(config)

        # Variables from .env are in os.environ
        slack_token = env.get("SLACK_BOT_TOKEN")
        print(f"Slack token from .env: {slack_token}")

    except ImportError:
        print("python-dotenv not installed. Install with: pip install python-dotenv")


def example_validation_in_development():
    """
    Example 4: Validate only non-secret variables in development.
    """
    print("\n=== Example 4: Partial Validation ===")

    config = EnvConfig(
        function_name="access-processor",
        project_id="equidade",
        use_secret_manager=False,  # No secrets in dev
    )

    env = EnvLoader(config)

    # Define only the non-secret vars you need for development
    dev_required = [
        "GCP_PROJECT_ID",
        "GCP_REGION",
        "BIGQUERY_DATASET_ACCESS",
        "BIGQUERY_TABLE_LOGS",
    ]

    is_valid, missing = env.validate(required_vars=dev_required)

    if is_valid:
        print("✅ Development environment configured correctly")
    else:
        print(f"❌ Missing development variables: {missing}")


def example_selective_loading():
    """
    Example 5: Load only specific variables you need.
    """
    print("\n=== Example 5: Selective Loading ===")

    config = EnvConfig(
        function_name="etl-surveycto-function",
        project_id="equidade",
        use_secret_manager=False,
    )

    env = EnvLoader(config)

    # Get only the vars you need for local testing
    aws_region = env.get("AWS_REGION", default="us-east-1")
    surveycto_server = env.get("SURVEYCTO_SERVER", default="ccwd")

    print(f"AWS Region: {aws_region}")
    print(f"SurveyCTO Server: {surveycto_server}")


def example_development_with_gcp_emulator():
    """
    Example 6: Use GCP emulators for local development.
    """
    print("\n=== Example 6: GCP Emulator ===")

    # Set emulator environment variables
    os.environ["BIGQUERY_EMULATOR_HOST"] = "localhost:9050"
    os.environ["STORAGE_EMULATOR_HOST"] = "http://localhost:9023"

    config = EnvConfig(
        function_name="gf_treatment_data_function",
        project_id="equidade",
        use_secret_manager=False,
    )

    env = EnvLoader(config)

    # Use emulator endpoints
    bq_host = os.environ.get("BIGQUERY_EMULATOR_HOST")
    storage_host = os.environ.get("STORAGE_EMULATOR_HOST")

    print(f"BigQuery Emulator: {bq_host}")
    print(f"Storage Emulator: {storage_host}")


if __name__ == "__main__":
    """
    Run all examples.

    To use:
    1. Create a .env file with test secrets (optional)
    2. Run: python examples/local_development.py
    """
    # Example .env file content:
    # SLACK_BOT_TOKEN=xoxb-test-token
    # CREDENTIALS={"type":"service_account","project_id":"test"}

    example_local_yaml_only()
    example_local_with_mock_secrets()
    example_local_with_dotenv()
    example_validation_in_development()
    example_selective_loading()
    example_development_with_gcp_emulator()

    print("\n✅ All examples completed!")

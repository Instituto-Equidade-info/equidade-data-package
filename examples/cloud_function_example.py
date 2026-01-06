"""
Example: Using EnvLoader in a Cloud Function

This example shows how to use the EnvLoader in your Cloud Functions
to automatically load environment variables from YAML and Secret Manager.
"""

import functions_framework
from equidade_data_package.config import load_env


@functions_framework.http
def main(request):
    """
    Cloud Function entry point.

    Replace 'equidade-download-data' with your function name.
    """
    # Load environment variables automatically
    env = load_env("equidade-download-data", auto_set=True)

    # Validate required variables
    is_valid, missing = env.validate()
    if not is_valid:
        return {"error": f"Missing required environment variables: {missing}"}, 500

    # Get individual variables
    slack_token = env.get("SLACK_BOT_TOKEN")
    credentials = env.get_json("CREDENTIALS")

    # Your function logic here
    print(f"Function configured with {len(env.get_all())} environment variables")
    print(f"Slack token available: {bool(slack_token)}")
    print(f"Credentials available: {bool(credentials)}")

    return {"status": "success", "vars_loaded": len(env.get_all())}, 200


# Alternative: Manual setup with custom configuration
@functions_framework.http
def main_advanced(request):
    """
    Advanced example with custom configuration.
    """
    from equidade_data_package.config import EnvLoader, EnvConfig

    # Custom configuration
    config = EnvConfig(
        function_name="etl-surveycto-function",
        project_id="equidade",
        region="southamerica-east1",
        use_secret_manager=True,
        cache_secrets=True,
    )

    # Initialize loader
    env = EnvLoader(config)

    # Set to os.environ so other libraries can use them
    env.set_environment()

    # Get typed values
    aws_key = env.get("AWS_ACCESS_KEY_ID")
    aws_secret = env.get("AWS_SECRET_ACCESS_KEY")
    credentials = env.get_json("CREDENTIALS")
    surveycto_password = env.get("SURVEYCTO_PASSWORD")

    # Validate
    is_valid, missing = env.validate()
    if not is_valid:
        return {"error": f"Missing variables: {missing}"}, 500

    # Your ETL logic here
    print(f"AWS configured: {bool(aws_key and aws_secret)}")
    print(f"SurveyCTO configured: {bool(surveycto_password)}")

    return {"status": "success"}, 200


# Alternative: Using environment variables directly after loading
@functions_framework.http
def main_simple(request):
    """
    Simplest usage - just load and use os.environ.
    """
    import os

    # Load all env vars into os.environ
    env = load_env("gf_raw_data_function", auto_set=True)

    # Now you can use os.environ normally
    slack_token = os.environ.get("SLACK_BOT_TOKEN")
    credentials = os.environ.get("CREDENTIALS")

    # Or continue using the env object
    authorization = env.get("AUTHORIZATION_KEY_BLIP")

    return {"status": "configured"}, 200

# Migration Guide: Moving to EnvLoader

This guide shows how to migrate your existing Cloud Functions to use the centralized `EnvLoader`.

## Before (Old Approach)

Each Cloud Function had its own environment variable configuration:

```python
# Old: main.py in equidade-download-data
import os
import json

# Manually get env vars
CREDENTIALS = json.loads(os.environ.get("CREDENTIALS"))
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
LOG_EXECUTION_ID = os.environ.get("LOG_EXECUTION_ID", "false") == "true"

# Function logic...
```

**Problems:**
- ❌ Repeated code across all functions
- ❌ No validation of required variables
- ❌ Error-prone JSON parsing
- ❌ No centralized management

## After (New Approach)

Use `EnvLoader` for automatic configuration:

```python
# New: main.py in equidade-download-data
from equidade_data_package.config import load_env

# Load all env vars automatically
env = load_env("equidade-download-data", auto_set=True)

# Validate required variables
is_valid, missing = env.validate()
if not is_valid:
    raise ValueError(f"Missing env vars: {missing}")

# Get variables with type conversion
CREDENTIALS = env.get_json("CREDENTIALS")
SLACK_BOT_TOKEN = env.get("SLACK_BOT_TOKEN")
LOG_EXECUTION_ID = env.get_bool("LOG_EXECUTION_ID", default=False)

# Function logic...
```

**Benefits:**
- ✅ Single line to load all variables
- ✅ Automatic validation
- ✅ Type-safe getters (get_json, get_bool, get_int)
- ✅ Centralized configuration

## Step-by-Step Migration

### 1. Update `requirements.txt` or `pyproject.toml`

Add the package dependency:

**requirements.txt:**
```txt
git+https://github.com/your-org/equidade-data-package.git
```

**pyproject.toml:**
```toml
[project]
dependencies = [
    "equidade-data-package @ git+https://github.com/your-org/equidade-data-package.git",
]
```

### 2. Update Your Cloud Function Code

**Before:**
```python
import os
import json
import functions_framework

@functions_framework.http
def main(request):
    # Manual env var loading
    try:
        credentials = json.loads(os.environ["CREDENTIALS"])
        slack_token = os.environ["SLACK_BOT_TOKEN"]
    except KeyError as e:
        return {"error": f"Missing env var: {e}"}, 500
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}"}, 500

    # Function logic
    process_data(credentials, slack_token)
    return {"status": "ok"}, 200
```

**After:**
```python
import functions_framework
from equidade_data_package.config import load_env

@functions_framework.http
def main(request):
    # Automatic env var loading
    env = load_env("equidade-download-data", auto_set=True)

    # Validate (optional but recommended)
    is_valid, missing = env.validate()
    if not is_valid:
        return {"error": f"Missing env vars: {missing}"}, 500

    # Get variables with automatic type conversion
    credentials = env.get_json("CREDENTIALS")
    slack_token = env.get("SLACK_BOT_TOKEN")

    # Function logic
    process_data(credentials, slack_token)
    return {"status": "ok"}, 200
```

### 3. Remove Duplicate Environment Variable Declarations

**Before:**
Each function's `deploy.sh` or Cloud Function configuration had:
```bash
gcloud functions deploy equidade-download-data \
  --set-env-vars CREDENTIALS='{"type":"service_account",...}' \
  --set-env-vars SLACK_BOT_TOKEN='xoxb-...' \
  --set-env-vars LOG_EXECUTION_ID='true'
```

**After:**
Environment variables are loaded automatically from:
1. `env-files/env-shared.yaml` (non-sensitive)
2. Secret Manager (sensitive)

You only need to deploy the function:
```bash
gcloud functions deploy equidade-download-data \
  --runtime python311 \
  --trigger-http
```

### 4. Verify Function-Specific Variables

The `EnvLoader` automatically knows which variables each function needs.

Check the mapping in [`env_loader.py`](../equidade_data_package/config/env_loader.py):

```python
FUNCTION_ENV_MAP = {
    "equidade-download-data": [
        "CREDENTIALS",
        "LOG_EXECUTION_ID",
        "SLACK_BOT_TOKEN",
    ],
    # ... other functions
}
```

If your function uses variables not listed, add them to the map.

## Migration Checklist

For each Cloud Function:

- [ ] Add `equidade-data-package` to dependencies
- [ ] Replace manual `os.environ` with `load_env()`
- [ ] Replace `json.loads()` with `env.get_json()`
- [ ] Add validation with `env.validate()`
- [ ] Update deploy script to remove redundant env vars
- [ ] Test locally with env vars set
- [ ] Deploy and verify

## Common Patterns

### Pattern 1: Simple Load and Use

```python
from equidade_data_package.config import load_env

env = load_env("my-function-name", auto_set=True)

# Now all vars are in os.environ and env object
slack_token = env.get("SLACK_BOT_TOKEN")
```

### Pattern 2: Type-Safe Getters

```python
env = load_env("my-function-name")

# Automatic type conversion
max_retries = env.get_int("MAX_RETRIES", default=3)
debug_mode = env.get_bool("DEBUG", default=False)
credentials = env.get_json("CREDENTIALS")
api_url = env.get("API_URL", default="https://api.example.com")
```

### Pattern 3: Validation Before Execution

```python
env = load_env("my-function-name")

# Validate all required vars are present
is_valid, missing = env.validate()
if not is_valid:
    raise EnvironmentError(f"Missing required variables: {', '.join(missing)}")

# Safe to proceed
credentials = env.get_json("CREDENTIALS")
```

### Pattern 4: Custom Required Variables

```python
env = load_env("my-function-name")

# Validate custom set of required vars
custom_required = ["CUSTOM_VAR_1", "CUSTOM_VAR_2"]
is_valid, missing = env.validate(required_vars=custom_required)
```

## Troubleshooting

### "Secret not found" Error

**Problem:** Secret Manager can't find the secret.

**Solution:** Check secret name mapping in `SECRET_NAME_MAP`:
```python
# env_loader.py
SECRET_NAME_MAP = {
    "SLACK_BOT_TOKEN": "slack-bot-token-equidade-download-data",
    # ...
}
```

Make sure the secret exists in GCP Secret Manager with this exact name.

### "Missing required env vars" Error

**Problem:** Function needs a variable not in the mapping.

**Solution:** Add the variable to `FUNCTION_ENV_MAP`:
```python
# env_loader.py
FUNCTION_ENV_MAP = {
    "my-function-name": [
        "EXISTING_VAR",
        "NEW_VAR",  # Add this
    ],
}
```

### YAML File Not Found

**Problem:** `env-shared.yaml` not found.

**Solution:**
1. Ensure `env-shared.yaml` is in the package at `env-files/env-shared.yaml`
2. Or specify custom path:
```python
from equidade_data_package.config import EnvLoader, EnvConfig

config = EnvConfig(
    function_name="my-function",
    yaml_path="/custom/path/env-shared.yaml"
)
env = EnvLoader(config)
```

## Testing Locally

When testing locally, set environment variables normally:

```bash
# Option 1: Export before running
export SLACK_BOT_TOKEN="xoxb-test-token"
export CREDENTIALS='{"type":"service_account"}'
python main.py

# Option 2: Use .env file (requires python-dotenv)
echo "SLACK_BOT_TOKEN=xoxb-test-token" > .env
python main.py
```

The `EnvLoader` respects runtime environment variables (highest priority).

## Need Help?

Contact the Equidade team or check:
- [EnvLoader source code](../equidade_data_package/config/env_loader.py)
- [Example usage](./cloud_function_example.py)
- [Package README](../README.md)

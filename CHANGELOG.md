# Changelog - equidade-data-package

## [0.3.0] - 2026-08-14

### ✨ Application Default Credentials support

GCP clients can now authenticate as the identity the code already runs as, instead of
requiring a service account JSON key.

Resolution order is **explicit argument → `$GCP_CREDENTIALS`/`$CREDENTIALS` → ADC**.

**Upgrading changes nothing on its own.** Any function that still sets the credentials
environment variable keeps using it, byte for byte as before. The environment variable
retains precedence deliberately, so this release can roll out through the normal cascade
without coordination.

The migration is per function, on your schedule: remove the env var from one function and
it starts using its own runtime service account. Roll back by putting the env var back.

### Why

Cloud Functions and Cloud Run already have an identity. Shipping them a JSON key so they
can authenticate as a *different* account means a long-lived private key sits in an
environment variable readable by anyone who can describe the function, and rotating it
means redeploying everything holding a copy.

This also unblocks per-function service accounts: a function cannot meaningfully run
under its own identity while the code authenticates as `bigquery-loader@` from a key —
the key wins over the runtime identity.

### Changed

- New `equidade_data_package/gcp/credentials.py` with `resolve_credentials()`
- `query_bigquery()` — env-var fallback moved into the resolver; ADC when unset
- `BigQueryWaveLoader.__init__` — `credentials_json` is now **optional**
- `StorageService.__init__` — `credentials_dict` is now **optional**
- `DriveService.__init__` — `credentials_dict` is now **optional**

All four remain backward compatible: passing credentials still works exactly as before.

### ⚠️ Note on Drive

Under ADC the identity becomes the runtime service account, so any Drive folder the code
reads must be shared with that account's email. Otherwise files appear not to exist,
rather than raising a permission error.

### 🔧 Fixed

`credentials.project_id` no longer leaks into client construction. It exists on service
account credentials but **not** on ADC credentials, so `bigquery.Client(project=
credentials.project_id)` would have raised `AttributeError` the moment a key was removed.
The project is now returned separately by the resolver.


## [0.2.1] - 2026-01-06

### 🐛 Bug Fixes
- **CRITICAL**: Fixed YAML path resolution in `EnvLoader`
  - **Problem**: `env-shared.yaml` was not being found in Cloud Functions
  - **Root cause**: Path calculation was going one directory too high (`parent.parent.parent` instead of `parent.parent`)
  - **Fix**: Changed line 321 in `env_loader.py` from:
    ```python
    package_dir = Path(__file__).parent.parent.parent  # WRONG - goes to project root
    ```
    to:
    ```python
    package_dir = Path(__file__).parent.parent  # CORRECT - stays in package
    ```
  - **Impact**: Now `GCP_PROJECT_ID` and other YAML variables load correctly in Cloud Functions
  - **Before**: `projects/None` errors in BigQuery
  - **After**: Variables load from `equidade_data_package/env-files/env-shared.yaml` ✅

### 📝 Notes
- This fix resolves the `Invalid resource name projects/None` error seen in Cloud Functions
- All Cloud Functions using `load_env()` will now correctly load environment variables from YAML
- No breaking changes - existing code continues to work

### 🚀 Deployment
To use the fixed version in your Cloud Function:

```bash
# Update requirements.txt
equidade-data-package==0.2.1

# Or install directly
pip install equidade-data-package==0.2.1
```

### ✅ Verification
You can verify the fix works by checking logs for:
```
✅ Usando project_id do EnvLoader: equidade
```

Instead of:
```
❌ AVISO: GCP_PROJECT_ID não encontrado no EnvLoader
```

---

## [0.2.0] - Previous release
- Added `EnvLoader` for centralized environment configuration
- Support for YAML and Secret Manager
- Event-based BigQuery logging

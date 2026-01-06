# Changelog - equidade-data-package

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

# Changelog - equidade-data-package

## [0.5.0] - 2026-08-19

### 🐛 school-register-processor had no entry, and nobody could tell

`school-register-processor` was missing from `FUNCTION_ENV_MAP` entirely. It worked
anyway, because `shared/school_register_logger.py` in
`equidade-access-cloud-functions` called `load_env("school-register")` at import
time and every function importing it inherited that set.

When that import-time call was removed (equidade-access-cloud-functions#7), the
function began failing on its next invocation with

```
❌ Dados inválidos: DOCUSIGN_TEMPLATE_SCHOOL_REGISTER não configurado
```

and returning `status: 'ok'`, so Pub/Sub acked and dropped every school
registration until it was found.

`docusign-webhook` had the same defect on a narrower path: its own entry omitted
`BIGQUERY_DATASET_SCHOOL_REGISTER`, which it needs through the `SchoolRegisterLogger`
it imports lazily.

### Changed

- **`SCHOOL_REGISTER_VARS`**, a single module-level list, now backs the
  `school-register`, `school-register-processor` and `school-register-manager`
  entries. They were two hand-copied lists, which is precisely how the deployed
  function's own name came to be absent from both. `school-register` is retained
  because it is not a deployed function name but is the one that module passed.
- **`BIGQUERY_DATASET_SCHOOL_REGISTER`** added to `docusign-webhook`.

### Removed — variables that never resolved

Each produced a Secret Manager 404 and a warning on every cold start, for a value
nothing could use:

- **`CREDENTIALS`** from 11 entries. It maps to no secret *on purpose*, so functions
  fall through to Application Default Credentials. Listing it only made the fallback
  noisy, and that noise can mask a real secret failure.
- **`DOCUSIGN_ACCESS_TOKEN`** — the token is obtained at runtime by
  `DocuSignOAuthClient`, which reads `docusign-refresh-token` from Secret Manager
  directly. Listed, it resolved by kebab-case guess to `docusign-access-token`, which
  does not exist; the real secret is `docusign-access-token-data` and nothing reads it
  from the environment.
- **`DOCUSIGN_USER_ID`** — referenced by no runtime code in any function repository.

### Upgrade note

`equidade-access-cloud-functions` carries a `CONFIG_FALLBACKS` workaround in
`shared/env.py` covering these two functions. Once this release is deployed there,
that workaround should be deleted — it exists only because the map was wrong.

## [0.4.1] - 2026-08-14

### 🔒 Removed the last two paths back to the leaked key

`SECRET_NAME_MAP` still mapped `CREDENTIALS_pi_raw_data_function` and
`CREDENTIALS_equidade-download-data` to Secret Manager entries that hold a
`bigquery-loader@` service account key.

Because of that, removing the `CREDENTIALS` environment variable from either function did
not switch it to ADC — `EnvLoader` fetched the same key from Secret Manager instead, and
`load_env(auto_set=True)` wrote it back into `os.environ`, where the credential resolver
picked it up ahead of ADC. The function kept working. This is the third time in this
migration that "still works" and "migrated" produced identical signals.

`CREDENTIALS` is also removed from both functions' `FUNCTION_ENV_MAP` entries, so
`validate()` stops reporting it as missing.

Genuinely shared secrets (`aws-access-key-id`, `surveycto-password`, …) are untouched.

**Note:** the secrets themselves still exist and still hold the key. They are destroyed as
part of the rotation, once logs confirm nothing reads them.
## [0.4.0] - 2026-08-14

### ✨ Google Drive without a service account key

`DriveService` no longer needs a JSON key. It impersonates a dedicated Drive service
account instead.

**Why plain ADC does not work for Drive.** On Cloud Functions the ADC token comes from the
metadata server, which issues `cloud-platform` tokens. The Drive API does not accept that
scope, and asking `google.auth.default()` for `drive.readonly` does not help — the metadata
server will not widen a token beyond what the runtime was granted. A service account *key*
can request any scope, which is why the old code worked and is exactly the dependency being
removed.

Impersonation resolves it: the runtime mints a short-lived token for
`drive-reader@equidade.iam.gserviceaccount.com` with the Drive scope attached, and no key
exists anywhere.

That account **holds no project IAM roles**. If its token leaks it can read the
spreadsheets it has been shared, not the project. Override with `$DRIVE_SA`.

**Requires:** the runtime service account needs `roles/iam.serviceAccountTokenCreator` on
the Drive account — granted on that resource, not project-wide.

Verified end to end against the live project: `DriveService()` with no credentials reads
`dic_interno_wave_2` and `dicionario_eq6_gf3.xlsx`.

Passing credentials explicitly still works unchanged.


## [0.3.2] - 2026-08-14

### 🐛 Restores the SLACK_BOT_TOKEN shared mapping

0.3.1 removed both cross-pipeline secret fallbacks at once. Removing the `SLACK_BOT_TOKEN`
one broke Slack notifications for `stf-etl-qualtrics` and `stf-treatment-function`, which
had been relying on it — the ETLs kept loading data, but every run failed to notify with
`{'ok': False, 'error': 'not_authed'}`.

The two fallbacks are not equivalent, and treating them as one change was the mistake:

| | Severity |
|---|---|
| Shared **service account key** with `bigquery.admin`, `storage.admin`, `secretmanager.admin` | Security incident — stays removed |
| Shared **Slack bot token** | Untidy — restored while each function gets its own secret |

`CREDENTIALS` remains unmapped, so the 0.3.1 fix stands.

**Follow-up:** create `slack-bot-token-<function>` secrets for the functions that need
them, then remove this mapping too.


## [0.3.1] - 2026-08-14

### 🔒 Removed cross-pipeline secret fallbacks

`SECRET_NAME_MAP` registered two **per-function** secrets as **shared defaults**:

```python
"CREDENTIALS": "credentials-pi-raw-data-function",
"SLACK_BOT_TOKEN": "slack-bot-token-consistency-checker-function",
```

Any function without its own suffixed entry silently received another pipeline's
credentials. This was observed in production: after `stf-etl-qualtrics` had its
`CREDENTIALS` environment variable removed, `EnvLoader` resolved the variable from Secret
Manager and handed it `credentials-pi-raw-data-function` — which holds a
`bigquery-loader@` service account key. Nothing failed, so nothing was noticed.

Both shared entries are removed. Functions that legitimately need these secrets keep
their explicit `<VAR>_<function-name>` entries and are unaffected:

| Function | Still resolves |
|---|---|
| `pi_raw_data_function` | `credentials-pi-raw-data-function` |
| `equidade-download-data` | `credentials-equidade-download-data` |
| `consistency_checker_function` | `slack-bot-token-consistency-checker-function` |

Functions without an entry now resolve to `credentials` / `slack-bot-token`, which do not
exist, so the variable comes back missing and the function fails with a clear error.
**That is intended**: borrowing another pipeline's credentials is worse than not starting.

Genuinely shared secrets (`aws-access-key-id`, `surveycto-password`, …) are unchanged.

Unmapped sensitive variables now log a warning naming the entry that should be added.

### 🐛 Fixed

`logging` was never imported in `env_loader.py`.


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

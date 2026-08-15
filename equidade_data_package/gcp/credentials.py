"""Credential resolution for GCP clients.

Single place that answers "how do we authenticate?", so the answer can change once
instead of in every client constructor.

Resolution order:

1. Credentials passed explicitly by the caller.
2. The ``GCP_CREDENTIALS`` / ``CREDENTIALS`` environment variable, if set.
3. Application Default Credentials — the identity the code is already running as.

Step 3 is the point of this module. On Cloud Functions and Cloud Run the runtime already
*has* an identity: the function's own service account. Shipping it a service account JSON
key so it can authenticate as a different account means a long-lived private key sits in
an environment variable, readable by anyone who can describe the function, and rotating it
means redeploying everything that holds a copy. With ADC there is no key to leak or
rotate.

Step 2 is kept deliberately so that upgrading this package changes nothing on its own.
Functions migrate one at a time by removing the environment variable, and roll back by
putting it back.
"""

import json
import logging
import os
from typing import Any, Dict, Optional, Sequence, Tuple

import google.auth
from google.auth import impersonated_credentials
from google.oauth2 import service_account

CLOUD_PLATFORM_SCOPE = "https://www.googleapis.com/auth/cloud-platform"
DRIVE_READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"

# Identity used only to read shared Google Drive files. It holds NO project IAM roles —
# see resolve_drive_credentials for why it exists. Override with $DRIVE_SA.
DEFAULT_DRIVE_SA = "drive-reader@equidade.iam.gserviceaccount.com"

_ENV_VARS = ("GCP_CREDENTIALS", "CREDENTIALS")


def _coerce(raw: Any) -> Optional[Dict]:
    """Accept a dict or a JSON string; return a dict, or None if unusable."""
    if not raw:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logging.warning(
                "Credentials were provided as a string but are not valid JSON; "
                "ignoring them and falling back to Application Default Credentials."
            )
            return None
    return None


def resolve_credentials(
    credentials: Any = None,
    scopes: Optional[Sequence[str]] = None,
) -> Tuple[Optional[Any], Optional[str]]:
    """Resolve credentials and the project they belong to.

    Args:
        credentials: A service account info dict (or JSON string). When omitted, the
            environment variable is tried, then ADC.
        scopes: OAuth scopes. Defaults to cloud-platform.

    Returns:
        ``(credentials, project_id)``. Both may be ``None`` under ADC when the
        environment does not advertise a project — callers that need a project should
        fall back to their own ``project_id`` argument.

    Note:
        The project is returned separately rather than read off the credentials object.
        ``service_account.Credentials`` exposes ``.project_id``; ADC credentials do not,
        so code doing ``credentials.project_id`` breaks the moment the key is removed.
    """
    scope_list = list(scopes) if scopes else [CLOUD_PLATFORM_SCOPE]

    info = _coerce(credentials)
    source = "argument"

    if info is None:
        for var in _ENV_VARS:
            info = _coerce(os.getenv(var))
            if info is not None:
                source = f"${var}"
                break

    if info is not None:
        # WARNING, not INFO, for two reasons: Cloud Functions does not emit INFO by
        # default, so an INFO line here is invisible exactly where it matters; and using
        # a long-lived key is the condition we are trying to eliminate, so it should be
        # noisy until it stops happening.
        logging.warning(
            "Authenticating with a SERVICE ACCOUNT KEY from %s. This is the legacy path: "
            "remove the credentials from %s so the runtime's own identity (ADC) is used.",
            source, source,
        )
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=scope_list
        )
        return creds, creds.project_id

    creds, project = google.auth.default(scopes=scope_list)
    # Also WARNING-level while the migration is in progress: it is the only way to
    # confirm from Cloud Logging that a function actually stopped using the key.
    # Downgrade to INFO once every function has migrated.
    logging.warning("Authenticating with Application Default Credentials (project=%s).", project)
    return creds, project


def resolve_drive_credentials(
    credentials: Any = None,
    scopes: Optional[Sequence[str]] = None,
    drive_sa: Optional[str] = None,
) -> Tuple[Optional[Any], Optional[str]]:
    """Resolve credentials for the Google Drive API.

    Drive needs its own OAuth scope, and that is why it cannot use plain ADC. On Cloud
    Functions the ADC token comes from the metadata server, which issues
    ``cloud-platform`` tokens; the Drive API does not accept that scope. Asking
    ``google.auth.default()`` for ``drive.readonly`` does not help, because the metadata
    server will not widen the token beyond what the runtime was granted.

    A service account *key* can request any scope, which is why the old code worked — and
    is exactly the dependency being removed.

    The way out is impersonation: the runtime identity mints a short-lived token for a
    dedicated Drive service account, with the Drive scope attached, and no key exists
    anywhere. The runtime service account needs ``roles/iam.serviceAccountTokenCreator``
    **on that service account**, not project-wide.

    The Drive account deliberately holds no project IAM roles. If its token leaks it can
    read the spreadsheets it has been shared, not the project.

    Args:
        credentials: Explicit service account info. When given, the legacy key path is
            used unchanged, so existing callers keep working.
        scopes: Drive scopes. Defaults to drive.readonly.
        drive_sa: Which account to impersonate. Defaults to $DRIVE_SA, then
            DEFAULT_DRIVE_SA.

    Returns:
        ``(credentials, project_id)``.
    """
    scope_list = list(scopes) if scopes else [DRIVE_READONLY_SCOPE]

    info = _coerce(credentials)
    if info is None:
        for var in _ENV_VARS:
            info = _coerce(os.getenv(var))
            if info is not None:
                break

    if info is not None:
        logging.warning(
            "Drive: authenticating with a SERVICE ACCOUNT KEY. This is the legacy path; "
            "remove the credentials so the dedicated Drive account is impersonated instead."
        )
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=scope_list
        )
        return creds, creds.project_id

    source, project = google.auth.default(scopes=[CLOUD_PLATFORM_SCOPE])
    target = drive_sa or os.getenv("DRIVE_SA") or DEFAULT_DRIVE_SA
    logging.warning(
        "Drive: impersonating %s for scopes %s (no key involved).", target, scope_list
    )
    creds = impersonated_credentials.Credentials(
        source_credentials=source,
        target_principal=target,
        target_scopes=scope_list,
        lifetime=3600,
    )
    return creds, project

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
from google.oauth2 import service_account

CLOUD_PLATFORM_SCOPE = "https://www.googleapis.com/auth/cloud-platform"

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
        logging.info(
            "Authenticating with a service account key from %s. Prefer Application "
            "Default Credentials: remove the environment variable to use the runtime's "
            "own identity.",
            source,
        )
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=scope_list
        )
        return creds, creds.project_id

    creds, project = google.auth.default(scopes=scope_list)
    logging.info("Authenticating with Application Default Credentials (project=%s).", project)
    return creds, project

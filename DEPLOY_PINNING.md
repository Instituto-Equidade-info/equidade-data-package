# Making deploys pick up the package version you expect

## The problem

Every function pins the package with a **mutable** ref:

```
equidade-data-package @ git+https://github.com/Instituto-Equidade-info/equidade-data-package.git@main
```

The URL is identical on every build, so pip and the Cloud Build layer cache both have
every reason to reuse what they already have. A deploy then "succeeds" while running the
old code, and nothing says so. The usual workaround — appending a timestamp to
`requirements.txt` to bust the layer cache — treats the symptom and still leaves you
guessing which version ran.

## The fix, in two parts

### 1. Pin to the released version, which the cascade already sends

`trigger-deploys.yml` dispatches `client_payload.version` (e.g. `v0.3.2`) and no function
repo uses it. Add this step **before** the deploy step in each function's workflow:

```yaml
    - name: Pin equidade-data-package to the released version
      run: |
        # repository_dispatch carries the released tag; a plain push to main has no
        # payload, so fall back to main for ordinary development deploys.
        VERSION="${{ github.event.client_payload.version }}"
        VERSION="${VERSION:-main}"
        echo "Pinning equidade-data-package to ${VERSION}"

        # Adjust the path if requirements.txt is not under functions/
        sed -i.bak -E \
          "s|(equidade-data-package @ git\+https://github.com/[^@]+)@.*|\1@${VERSION}|" \
          functions/requirements.txt
        grep equidade-data-package functions/requirements.txt
```

An immutable tag changes the URL on every release, so there is nothing for a cache to
reuse. It also makes the deploy reproducible: the requirements file states exactly what
shipped.

### 2. Belt and braces: disable the pip cache in the build

```yaml
        gcloud functions deploy ... \
          --set-build-env-vars=PIP_NO_CACHE_DIR=1
```

## How to know it worked

`load_env()` logs the package version at WARNING on every cold start, so Cloud Logging
answers the question directly:

```
WARNING:root:equidade-data-package 0.3.2 loaded for function 'stf-etl-qualtrics'
```

Fleet-wide check:

```bash
gcloud logging read \
  'resource.type="cloud_function" AND textPayload:"equidade-data-package"' \
  --project=equidade --freshness=1d \
  --format="value(resource.labels.function_name,textPayload)" | sort -u
```

Any function reporting an old version did not actually pick up the release, regardless of
what its deploy job said.

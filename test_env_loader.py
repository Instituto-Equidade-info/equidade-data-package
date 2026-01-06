#!/usr/bin/env python3
"""Test script to debug env_loader"""

import os
from equidade_data_package.config import load_env

print("=" * 60)
print("Testing EnvLoader")
print("=" * 60)

# Test 1: Load env for access-processor
print("\n1. Loading env for 'access-processor'...")
env = load_env("access-processor", auto_set=True)

# Test 2: Check what was loaded
print("\n2. Checking loaded values...")
print(f"   GCP_PROJECT_ID from env.get(): {env.get('GCP_PROJECT_ID')}")
print(f"   GCP_PROJECT_ID from os.environ: {os.environ.get('GCP_PROJECT_ID')}")
print(f"   GCP_REGION from env.get(): {env.get('GCP_REGION')}")
print(f"   ENVIRONMENT from env.get(): {env.get('ENVIRONMENT')}")

# Test 3: Check internal state
print("\n3. Internal state:")
print(f"   _env_vars keys: {list(env._env_vars.keys())[:10]}...")
print(f"   Total vars loaded: {len(env._env_vars)}")

# Test 4: Validate
print("\n4. Running validate()...")
is_valid, missing = env.validate()
print(f"   Valid: {is_valid}")
if not is_valid:
    print(f"   Missing: {missing}")

print("\n" + "=" * 60)

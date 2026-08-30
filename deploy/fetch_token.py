#!/usr/bin/env python3
"""Fetch Finnkino auth token from the public homepage (requires non-blocked IP)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from curl_cffi import requests
from app import HOME, extract_api_config

response = requests.get(HOME, impersonate="chrome", timeout=30)
if response.status_code == 403 and "Just a moment" in response.text:
    raise SystemExit("Cloudflare blocked this IP — run from a residential network")
response.raise_for_status()
print(extract_api_config(response.text)["token"])

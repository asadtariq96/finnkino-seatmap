#!/usr/bin/env python3
"""Fetch Finnkino auth token from the public homepage (requires non-blocked IP)."""
import re
import sys

from curl_cffi import requests

HOME = "https://www.finnkino.fi/"


def extract_token(html: str) -> str:
    normalized = html.replace('\\"', '"').replace("\\/", "/")
    match = re.search(r'"authToken"\s*:\s*"([^"]+)"', normalized)
    if not match:
        raise ValueError("Finnkino API configuration was not found")
    return match.group(1)


response = requests.get(HOME, impersonate="chrome", timeout=30)
if response.status_code == 403 and "Just a moment" in response.text:
    raise SystemExit("Cloudflare blocked this IP — run from a residential network")
response.raise_for_status()
print(extract_token(response.text))

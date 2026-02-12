#!/usr/bin/env python3
"""Test script to debug video download with redirects."""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: GEMINI_API_KEY not found")
    exit(1)

# Test URI (replace with your actual URI)
video_uri = "https://generativelanguage.googleapis.com/v1beta/files/ej9z601zavdp:download?alt=media"

print(f"Testing video download with URI: {video_uri}\n")

# Test 1: Basic request with headers
print("=== Test 1: Basic request with allow_redirects=True ===")
try:
    headers = {"x-goog-api-key": api_key}
    response = requests.get(video_uri, headers=headers, allow_redirects=True)
    print(f"Status: {response.status_code}")
    print(f"Final URL: {response.url}")
    print(f"History: {[r.status_code for r in response.history]}")
    if response.status_code == 200:
        print(f"✅ Success! Downloaded {len(response.content)} bytes")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n=== Test 2: Using Session to preserve headers on redirect ===")
try:
    session = requests.Session()
    session.headers.update({"x-goog-api-key": api_key})

    response = session.get(video_uri, allow_redirects=True)
    print(f"Status: {response.status_code}")
    print(f"Final URL: {response.url}")
    print(f"History: {[r.status_code for r in response.history]}")
    if response.status_code == 200:
        print(f"✅ Success! Downloaded {len(response.content)} bytes")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n=== Test 3: Manual redirect following ===")
try:
    headers = {"x-goog-api-key": api_key}

    # First request - don't follow redirects
    response = requests.get(video_uri, headers=headers, allow_redirects=False)
    print(f"Initial status: {response.status_code}")

    if response.status_code in [301, 302, 303, 307, 308]:
        redirect_url = response.headers.get('Location')
        print(f"Redirect to: {redirect_url}")

        # Follow redirect with headers
        response = requests.get(redirect_url, headers=headers, allow_redirects=True)
        print(f"Final status: {response.status_code}")

        if response.status_code == 200:
            print(f"✅ Success! Downloaded {len(response.content)} bytes")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
    elif response.status_code == 200:
        print(f"✅ No redirect needed! Downloaded {len(response.content)} bytes")
    else:
        print(f"❌ Unexpected status: {response.status_code}")

except Exception as e:
    print(f"❌ Error: {e}")

#!/usr/bin/env python3
"""Generate new VAPID keys for web push notifications."""

from pywebpush import webpush
import json

# Generate VAPID keys
vapid_claims = {
    "sub": "mailto:admin@yeninesilevim.com"
}

print("Generating VAPID keys...")
print("\nUsing py-vapid library to generate proper keys:\n")

import subprocess
import sys

try:
    result = subprocess.run(['vapid', '--gen'], capture_output=True, text=True)
    print(result.stdout)
    print("\nIf vapid command not found, install it:")
    print("pip install py-vapid")
    print("\nThen run: vapid --gen")
except FileNotFoundError:
    print("vapid command not found. Installing py-vapid...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'py-vapid'])
    print("\nNow run: python -m vapid --gen")
    print("\nOr run this script again.")

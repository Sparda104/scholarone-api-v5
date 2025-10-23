#!/usr/bin/env python3
"""
V5.1 Phase 2: S1-705 Detection in endpoints.py
================================================

This script adds S1-705 "too many results" error detection to endpoints.py.

Critical fix: Without this, chunking cannot detect when to split date ranges.
"""

import os
import sys
import re
from datetime import datetime

def backup_file(filepath):
    """Create timestamped backup."""
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{filepath}.phase2_backup_{timestamp}"
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [Backup] {filepath} -> {backup_path}")
        return backup_path
    return None

def main():
    print("=" * 70)
    print("V5.1 PHASE 2: ADD S1-705 DETECTION TO ENDPOINTS.PY")
    print("=" * 70)
    print()

    # Check if endpoints.py exists
    if not os.path.exists('endpoints.py'):
        print("❌ ERROR: endpoints.py not found!")
        print("Make sure you're in the correct directory.")
        sys.exit(1)

    # Step 1: Backup
    print("[1/4] Creating backup...")
    backup_file('endpoints.py')
    print("✓ Backup created")

    # Step 2: Read current content
    print("\n[2/4] Reading endpoints.py...")
    with open('endpoints.py', 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"✓ Read {len(content)} characters")

    # Step 3: Add S1-705 detection helper function
    print("\n[3/4] Adding S1-705 detection helper...")

    # Define the helper function as a string
    helper_function = 
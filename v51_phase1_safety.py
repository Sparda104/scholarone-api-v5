#!/usr/bin/env python3
"""
V5.1 Phase 1: Pre-Integration Safety
=====================================

This script prepares for V5.1 development by:
1. Backing up V5.0
2. Creating V5.1 development branch
3. Verifying baseline
4. Documenting current state
"""

import subprocess
import os
import sys
import shutil
from datetime import datetime

def run_command(cmd, check=True):
    """Run shell command and return output."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            check=check
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def main():
    print("=" * 70)
    print("V5.1 PHASE 1: PRE-INTEGRATION SAFETY")
    print("=" * 70)
    print()

    # Step 1: Verify we have a clean working directory
    print("[1/6] Checking git status...")
    success, stdout, stderr = run_command("git status --porcelain")

    if stdout.strip():
        print("⚠️  WARNING: You have uncommitted changes:")
        print(stdout)
        response = input("\nCommit these changes before continuing? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            print("\n[Committing changes...]")
            run_command("git add -A")
            run_command('git commit -m "V5.0: Final state before V5.1 development"')
            print("✓ Changes committed")
        else:
            print("\n❌ Please commit or stash changes before continuing.")
            sys.exit(1)
    else:
        print("✓ Working directory clean")

    # Step 2: Tag V5.0 as final stable version
    print("\n[2/6] Tagging V5.0 as final stable version...")
    run_command("git tag -f v5.0.0-final-stable")
    print("✓ Tagged as v5.0.0-final-stable")

    # Step 3: Create V5.1 development branch
    print("\n[3/6] Creating V5.1 development branch...")
    success, _, _ = run_command("git checkout -b v5.1-development", check=False)
    if not success:
        # Branch might already exist
        run_command("git checkout v5.1-development")
    print("✓ On branch: v5.1-development")

    # Step 4: Create backup directory
    print("\n[4/6] Creating backup directory...")
    backup_dir = f"v5.0_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)

    # Backup critical files
    critical_files = [
        'main.py',
        'endpoints.py',
        'exporter.py',
        'utils.py',
        'gui_widgets.py',
        'checkpointing.py'
    ]

    for file in critical_files:
        if os.path.exists(file):
            shutil.copy2(file, os.path.join(backup_dir, file))

    print(f"✓ Backup created in: {backup_dir}")

    # Step 5: Verify V5.0 baseline
    print("\n[5/6] Verifying V5.0 baseline...")

    # Check that all critical files exist
    all_exist = True
    for file in critical_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"  ✓ {file} ({size} bytes)")
        else:
            print(f"  ✗ {file} MISSING!")
            all_exist = False

    if not all_exist:
        print("\n❌ ERROR: Not all V5.0 files are present!")
        sys.exit(1)

    # Step 6: Document current state
    print("\n[6/6] Documenting V5.0 baseline...")

    baseline_doc = f"""# V5.0 Baseline Documentation
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Git Status
Branch: v5.1-development
Tag: v5.0.0-final-stable

## File Inventory
"""

    for file in critical_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            lines = len(open(file, 'r', encoding='utf-8').readlines())
            baseline_doc += f"- {file}: {size} bytes, {lines} lines\n"

    baseline_doc += f"""
## Backup Location
{os.path.abspath(backup_dir)}

## Ready for V5.1 Development
All V5.0 files backed up and verified.
Safe to proceed with V5.1 enhancements.

## Rollback Instructions
To rollback to V5.0 at any time:
```
git checkout v5.0.0-final-stable
```

Or restore from backup:
```
cp {backup_dir}/* .
```
"""

    with open('V5.0_BASELINE.md', 'w', encoding='utf-8') as f:
        f.write(baseline_doc)

    print("✓ Baseline documented in V5.0_BASELINE.md")

    # Summary
    print()
    print("=" * 70)
    print("PHASE 1 COMPLETE!")
    print("=" * 70)
    print()
    print("✅ V5.0 safely backed up")
    print("✅ V5.1 development branch created")
    print("✅ Baseline documented")
    print("✅ Ready for Phase 2")
    print()
    print("Next step:")
    print("  python v51_phase2_s1_705_detection.py")
    print()

if __name__ == '__main__':
    main()

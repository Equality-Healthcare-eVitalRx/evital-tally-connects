"""
Build automation script for eVitalConnects (eVital<>Tally Connects).
Generates local, staging, beta, and production builds using PyInstaller,
then packages each build into a versioned zip archive.

Uses the same PyInstaller command as manual builds:
    uv run pyinstaller.exe --noconsole --onefile --windowed --clean ...

Usage:
    uv run python build.py                          # Build all 4 environments
    uv run python build.py --env staging            # Build only staging
    uv run python build.py --skip-zip               # Build without zipping
    uv run python build.py --clean                  # Clean build/dist first
    uv run python build.py --env local --skip-zip   # Combined flags
"""

import os
import sys
import re
import shutil
import zipfile
import subprocess
import argparse
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.resolve()
CONSTANTS_FILE = PROJECT_ROOT / "lib" / "constants.py"
VERSION_FILE = PROJECT_ROOT / "version.txt"
ENTRY_POINT = "app.py"

ICON_PATH = ".\\lib\\images\\logo2.ico"
SPLASH_IMAGE = ".\\lib\\images\\login_panel.jpg"
FONTS_DIR = "lib\\fonts"

ENVIRONMENTS = ["local", "staging", "beta", "production"]

# Base PyInstaller arguments (user's exact command style)
PYINSTALLER_ARGS = [
    "pyinstaller.exe",
    "--noconsole",
    "--onefile",
    "--windowed",
    "--clean",
    "--version-file=version.txt",
    f"--icon={ICON_PATH}",
    "--add-data", "lib/fonts/static/Manrope-Regular.ttf;lib/fonts/static/",
    "--add-data", "lib/fonts/breeze/breeze.tcl;lib/fonts/breeze",
    "--add-data", "lib/fonts/breeze/breeze/*.png;lib/fonts/breeze/breeze",
    f"--splash={SPLASH_IMAGE}",
    "--collect-all", "babel",
    ENTRY_POINT,
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_current_version() -> str:
    """Extract version string from version.txt."""
    content = VERSION_FILE.read_text(encoding="utf-8")
    match = re.search(r"StringStruct\(u'FileVersion', u'([\d.]+)'\)", content)
    if not match:
        raise RuntimeError("Could not find version in version.txt")
    return match.group(1)


def set_env_type(constants_path: Path, env: str) -> str:
    """
    Modify envtype in constants.py.
    Returns the original envtype so it can be restored later.
    """
    content = constants_path.read_text(encoding="utf-8")
    match = re.search(r'^envtype\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        raise RuntimeError('Could not find "envtype" assignment in constants.py')

    original = match.group(1)
    if original == env:
        print(f"  [SKIP] envtype already set to '{env}'")
        return original

    new_content = re.sub(
        r'^envtype\s*=\s*"([^"]+)"',
        f'envtype = "{env}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    constants_path.write_text(new_content, encoding="utf-8")
    print(f"  [SET]   envtype changed from '{original}' → '{env}'")
    return original


def clean_directories():
    """Remove build/ and dist/ directories."""
    for d in ["build", "dist"]:
        path = PROJECT_ROOT / d
        if path.exists():
            print(f"  [CLEAN] Removing {d}/")
            shutil.rmtree(path)


def run_pyinstaller():
    """Execute PyInstaller via uv with the configured arguments."""
    print("  [BUILD] Running PyInstaller via uv...")
    cmd = ["uv", "run"] + PYINSTALLER_ARGS
    print(f"         {' '.join(str(a) for a in cmd)}")

    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # Print both stdout and stderr for debugging
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"PyInstaller failed with exit code {result.returncode}")

    print("  [BUILD] PyInstaller completed successfully")
    # Print last few non-empty lines for visibility
    lines = [l for l in result.stdout.strip().splitlines() if l.strip()]
    for line in lines[-5:]:
        print(f"         {line}")


def zip_build(version: str, env: str, skip_zip: bool = False) -> Path | None:
    """
    Zip the dist output into a versioned archive.
    With --onefile, the output is a single executable at dist/app.exe.
    Returns the path to the created zip file, or None if skipped.
    """
    dist_dir = PROJECT_ROOT / "dist"
    if not dist_dir.exists() or not list(dist_dir.iterdir()):
        raise FileNotFoundError(
            f"Expected build output not found in {dist_dir}\n"
            "Did PyInstaller complete successfully?"
        )

    zip_name = f"app-v{version}-{env}.zip"
    zip_path = dist_dir / zip_name

    if skip_zip:
        print(f"  [ZIP]   Skipping zip creation (--skip-zip)")
        return None

    print(f"  [ZIP]   Creating {zip_name} ...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in dist_dir.iterdir():
            # Skip zip files themselves (from previous runs)
            if item.suffix == ".zip":
                continue
            if item.is_dir():
                for file_path in item.rglob("*"):
                    arcname = file_path.relative_to(dist_dir)
                    zf.write(file_path, arcname)
            else:
                zf.write(item, item.name)

    print(f"  [ZIP]   Created: {zip_path}")
    return zip_path


def build_env(env: str, version: str, skip_zip: bool):
    """Build and package a single environment."""
    print(f"\n{'='*60}")
    print(f"  Building: {env.upper()}")
    print(f"{'='*60}")

    # 1. Set environment in constants.py
    original_env = set_env_type(CONSTANTS_FILE, env)

    try:
        # 2. Run PyInstaller
        run_pyinstaller()

        # 3. Create zip archive
        zip_build(version, env, skip_zip)
    finally:
        # 4. Restore original envtype
        set_env_type(CONSTANTS_FILE, original_env)


# ── Main ──────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Build and package eVitalConnects for all environments"
    )
    parser.add_argument(
        "--env",
        choices=ENVIRONMENTS,
        help="Build only the specified environment (local/staging/beta/production)",
    )
    parser.add_argument(
        "--skip-zip",
        action="store_true",
        help="Skip creating zip archives after build",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove build/ and dist/ directories before starting",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    version = get_current_version()
    print(f"eVitalConnects Build Script")
    print(f"Version: {version}")
    print(f"Python:  {sys.executable}")
    print()

    if args.clean:
        clean_directories()

    environments = [args.env] if args.env else ENVIRONMENTS

    for env in environments:
        build_env(env, version, args.skip_zip)

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  BUILD COMPLETE")
    print(f"{'='*60}")
    dist_dir = PROJECT_ROOT / "dist"
    if dist_dir.exists():
        zip_files = sorted(dist_dir.glob("*.zip"))
        if zip_files:
            print(f"\n  Archives created:")
            for zf in zip_files:
                size_mb = zf.stat().st_size / (1024 * 1024)
                print(f"    {zf.name}  ({size_mb:.1f} MB)")
        else:
            print(f"\n  No zip archives created (check dist/ for build output)")
    print()


if __name__ == "__main__":
    main()
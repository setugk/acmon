#!/usr/bin/env python3
"""
restore.py — restore Acmon from a backup file.

Usage:
  python3 restore.py BACKUP_FILE [--api URL] [--key KEYFILE]

BACKUP_FILE may be:
  - a plaintext .json export (from GET /api/export or ~/.acmon/backups/), or
  - an encrypted .json.enc (from backup_acmon_mac.sh). It is decrypted with
    openssl using the key file (default ~/.acmon/backup.key).

Acmon's data is a flat key-value store (weekly schedule, health state, extras,
prefs, onboarded flag) — there's no per-item merge like Journery's notes, so
restore always fully replaces the current state with the backup's. Prompts
for a typed confirmation before doing so.

Examples:
  python3 restore.py ~/.acmon/backups/acmon-2026-07-09.json

  python3 restore.py "~/Library/Mobile Documents/com~apple~CloudDocs/AcmonBackups/acmon-2026-07-09.json.enc"
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error

DEFAULT_API = "http://10.0.0.10:5054/api"
DEFAULT_KEY = os.path.expanduser("~/.acmon/backup.key")


def decrypt(enc_path, key_path):
    if not os.path.isfile(key_path):
        sys.exit(f"Key file not found: {key_path}\n"
                 f"Provide it with --key, or retrieve the key from your password manager.")
    out = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
    try:
        subprocess.run(
            ["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "200000",
             "-in", enc_path, "-out", out, "-pass", f"file:{key_path}"],
            check=True, capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        os.path.exists(out) and os.remove(out)
        sys.exit(f"Decryption failed (wrong key?):\n{e.stderr.decode(errors='replace')}")
    return out


def main():
    ap = argparse.ArgumentParser(description="Restore Acmon from a backup file.")
    ap.add_argument("backup", help="path to a .json or .json.enc backup")
    ap.add_argument("--api", default=DEFAULT_API, help=f"API base (default {DEFAULT_API})")
    ap.add_argument("--key", default=DEFAULT_KEY, help=f"key file for .enc (default {DEFAULT_KEY})")
    args = ap.parse_args()

    path = os.path.expanduser(args.backup)
    cleanup = None
    if path.endswith(".enc"):
        print(f"Decrypting {path} …")
        path = decrypt(path, os.path.expanduser(args.key))
        cleanup = path

    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"Could not read backup as JSON: {e}")

    if not data:
        sys.exit("Refusing to restore an empty backup.")

    print(f"Backup contains keys: {', '.join(sorted(data.keys()))}")
    print(f"\n⚠️  This will REPLACE all current state at {args.api} with this backup.")
    if input("    Type 'REPLACE' to confirm: ").strip() != "REPLACE":
        sys.exit("Aborted.")

    req = urllib.request.Request(
        f"{args.api}/import",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            result = json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Import failed (HTTP {e.code}): {e.read().decode(errors='replace')}")
    except urllib.error.URLError as e:
        sys.exit(f"Could not reach {args.api} — on the home network? ({e})")
    finally:
        if cleanup:
            os.remove(cleanup)

    print(f"Done — restored {len(data)} keys.")


if __name__ == "__main__":
    main()

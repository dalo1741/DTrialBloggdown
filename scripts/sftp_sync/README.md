# sftp_sync

Copies new files from an SFTP server to a local directory. Built for small,
regular batches (e.g. a daily drop of ~15 files) as a more robust replacement
for an ad-hoc PowerShell script.

Robustness features:
- **Idempotent**: a manifest (`.sftp_sync_manifest.json`) records which files
  (by name + size + mtime) have already been copied, so re-running the
  script — e.g. from a daily cron job — never re-downloads the same file.
- **Atomic downloads**: files are written to `<name>.part` and only renamed
  into place after a size check succeeds, so a crash mid-transfer never
  leaves a corrupt file where a real one is expected.
- **Retries with backoff**: both connecting and downloading retry with
  exponential backoff on transient network/SSH errors.
- **Host key verification**: uses a `known_hosts` file when provided instead
  of blindly trusting the server.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp config.example.yaml config.yaml
# edit config.yaml: host, username, remote_dir, local_dir, key_path, etc.

# recommended: pin the server's host key
ssh-keyscan -H your.sftp.host >> known_hosts
```

If using password auth instead of a key, set the env var named in
`password_env` before running (e.g. `export SFTP_PASSWORD=...`); never put
the password itself in `config.yaml`.

## Usage

```bash
# see what would be copied without copying anything
python3 sftp_sync.py --config config.yaml --dry-run

# actually copy
python3 sftp_sync.py --config config.yaml --log-file sftp_sync.log
```

## Scheduling

Run once a day with cron:

```
0 6 * * * cd /path/to/scripts/sftp_sync && .venv/bin/python sftp_sync.py --config config.yaml --log-file sftp_sync.log >> cron.log 2>&1
```

Or via Windows Task Scheduler running the same command, if you want to keep
it on the same machine as the PowerShell script it replaces.

#!/usr/bin/env python3
"""Copy new files from an SFTP server to a local directory.

Designed for small, regular batches (e.g. ~15 files/day). Safe to run
repeatedly: already-copied files are skipped via a local manifest, and
downloads are written atomically so a crash mid-transfer never leaves a
corrupt file behind.

Configuration is read from a YAML file (see config.example.yaml) with
secrets supplied via environment variables, not committed to the file.

Usage:
    python sftp_sync.py --config config.yaml
    python sftp_sync.py --config config.yaml --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import stat
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import paramiko
import yaml

logger = logging.getLogger("sftp_sync")


@dataclass
class Config:
    host: str
    port: int
    username: str
    remote_dir: str
    local_dir: Path
    manifest_path: Path
    key_path: Path | None
    password_env: str | None
    known_hosts_path: Path | None
    file_pattern: str | None
    delete_remote_after_copy: bool
    max_retries: int
    retry_backoff_seconds: float
    connect_timeout_seconds: float

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        raw = yaml.safe_load(path.read_text())
        return cls(
            host=raw["host"],
            port=int(raw.get("port", 22)),
            username=raw["username"],
            remote_dir=raw["remote_dir"],
            local_dir=Path(raw["local_dir"]).expanduser(),
            manifest_path=Path(raw.get("manifest_path", ".sftp_sync_manifest.json")).expanduser(),
            key_path=Path(raw["key_path"]).expanduser() if raw.get("key_path") else None,
            password_env=raw.get("password_env"),
            known_hosts_path=Path(raw["known_hosts_path"]).expanduser() if raw.get("known_hosts_path") else None,
            file_pattern=raw.get("file_pattern"),
            delete_remote_after_copy=bool(raw.get("delete_remote_after_copy", False)),
            max_retries=int(raw.get("max_retries", 4)),
            retry_backoff_seconds=float(raw.get("retry_backoff_seconds", 2.0)),
            connect_timeout_seconds=float(raw.get("connect_timeout_seconds", 15.0)),
        )


class Manifest:
    """Tracks which remote files have already been copied, keyed by
    name + size + mtime so a changed file on the server is re-fetched."""

    def __init__(self, path: Path):
        self.path = path
        self._entries: dict[str, dict] = {}
        if path.exists():
            self._entries = json.loads(path.read_text())

    def _key(self, filename: str, size: int, mtime: int) -> str:
        return f"{filename}:{size}:{mtime}"

    def already_copied(self, filename: str, size: int, mtime: int) -> bool:
        return self._key(filename, size, mtime) in self._entries

    def mark_copied(self, filename: str, size: int, mtime: int) -> None:
        self._entries[self._key(filename, size, mtime)] = {
            "filename": filename,
            "size": size,
            "mtime": mtime,
            "copied_at": time.time(),
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._entries, indent=2))
        tmp.replace(self.path)


def connect(cfg: Config) -> paramiko.SFTPClient:
    client = paramiko.SSHClient()
    if cfg.known_hosts_path and cfg.known_hosts_path.exists():
        client.load_host_keys(str(cfg.known_hosts_path))
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
    else:
        logger.warning(
            "No known_hosts_path configured/found; using AutoAddPolicy. "
            "Set known_hosts_path in config for production use."
        )
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs = dict(
        hostname=cfg.host,
        port=cfg.port,
        username=cfg.username,
        timeout=cfg.connect_timeout_seconds,
    )
    if cfg.key_path:
        connect_kwargs["key_filename"] = str(cfg.key_path)
    elif cfg.password_env:
        password = os.environ.get(cfg.password_env)
        if not password:
            raise RuntimeError(f"Environment variable {cfg.password_env} is not set")
        connect_kwargs["password"] = password
    else:
        raise RuntimeError("Config must set either key_path or password_env")

    client.connect(**connect_kwargs)
    return client.open_sftp()


def connect_with_retries(cfg: Config) -> paramiko.SFTPClient:
    last_exc: Exception | None = None
    for attempt in range(1, cfg.max_retries + 1):
        try:
            return connect(cfg)
        except (paramiko.SSHException, OSError) as exc:
            last_exc = exc
            wait = cfg.retry_backoff_seconds * (2 ** (attempt - 1))
            logger.warning("Connect attempt %d/%d failed: %s (retrying in %.1fs)",
                            attempt, cfg.max_retries, exc, wait)
            time.sleep(wait)
    raise ConnectionError(f"Could not connect after {cfg.max_retries} attempts") from last_exc


def list_remote_files(sftp: paramiko.SFTPClient, cfg: Config) -> list[paramiko.SFTPAttributes]:
    entries = sftp.listdir_attr(cfg.remote_dir)
    files = [e for e in entries if not stat.S_ISDIR(e.st_mode)]
    if cfg.file_pattern:
        import fnmatch
        files = [e for e in files if fnmatch.fnmatch(e.filename, cfg.file_pattern)]
    return files


def download_one(sftp: paramiko.SFTPClient, cfg: Config, entry: paramiko.SFTPAttributes) -> None:
    remote_path = f"{cfg.remote_dir.rstrip('/')}/{entry.filename}"
    local_path = cfg.local_dir / entry.filename
    tmp_path = local_path.with_suffix(local_path.suffix + ".part")

    cfg.local_dir.mkdir(parents=True, exist_ok=True)
    sftp.get(remote_path, str(tmp_path))

    local_size = tmp_path.stat().st_size
    if local_size != entry.st_size:
        tmp_path.unlink(missing_ok=True)
        raise IOError(
            f"Size mismatch for {entry.filename}: remote={entry.st_size} local={local_size}"
        )

    tmp_path.replace(local_path)

    if cfg.delete_remote_after_copy:
        sftp.remove(remote_path)


def sync(cfg: Config, dry_run: bool = False) -> tuple[int, int]:
    manifest = Manifest(cfg.manifest_path)
    sftp = connect_with_retries(cfg)
    copied, skipped = 0, 0
    try:
        for entry in list_remote_files(sftp, cfg):
            if manifest.already_copied(entry.filename, entry.st_size, entry.st_mtime):
                skipped += 1
                continue

            if dry_run:
                logger.info("[dry-run] would copy %s (%d bytes)", entry.filename, entry.st_size)
                copied += 1
                continue

            for attempt in range(1, cfg.max_retries + 1):
                try:
                    download_one(sftp, cfg, entry)
                    manifest.mark_copied(entry.filename, entry.st_size, entry.st_mtime)
                    logger.info("Copied %s (%d bytes)", entry.filename, entry.st_size)
                    copied += 1
                    break
                except (paramiko.SSHException, OSError, IOError) as exc:
                    wait = cfg.retry_backoff_seconds * (2 ** (attempt - 1))
                    logger.warning("Failed to copy %s (attempt %d/%d): %s",
                                   entry.filename, attempt, cfg.max_retries, exc)
                    if attempt == cfg.max_retries:
                        logger.error("Giving up on %s after %d attempts", entry.filename, cfg.max_retries)
                    else:
                        time.sleep(wait)
    finally:
        sftp.close()
        if not dry_run:
            manifest.save()

    return copied, skipped


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="Path to YAML config file")
    parser.add_argument("--dry-run", action="store_true", help="List what would be copied, without copying")
    parser.add_argument("--log-file", type=Path, default=None, help="Optional path to also log to a file")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args(argv)


def setup_logging(log_file: Path | None, verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    setup_logging(args.log_file, args.verbose)

    cfg = Config.from_yaml(args.config)
    try:
        copied, skipped = sync(cfg, dry_run=args.dry_run)
    except Exception:
        logger.exception("Sync failed")
        return 1

    logger.info("Done. Copied %d file(s), skipped %d already-copied file(s).", copied, skipped)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

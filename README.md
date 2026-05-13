<div align="center">
  <img src="https://raw.githubusercontent.com/RECHERGG/paperless-backup/refs/heads/master/.github/assets/logo.png" width="144" height="144" alt="paperless-backup" />
  <h1>paperless-backup</h1>

  <p><strong>Open-source lightweight backup tool for paperless-ngx</strong></p>

  [![python-badge](https://badges.penpow.dev/badges/built-with/python/cozy.png)](https://www.python.org/)
  [![dono-badge](https://badges.penpow.dev/badges/donate/github-sponsors-singular/cozy.png)](https://github.com/sponsors/RECHERGG)
  [![docker-badge](https://badges.penpow.dev/badges/supported/docker/cozy.png)](https://hub.docker.com/r/rechergg/paperless-backup)
</div>

paperless-backup is a lightweight backup utility for paperless-ngx environments. It automates the creation of consistent backups from a running paperless container and transfers them to remote storage, such as an SFTP server.

The tool is designed to run in containerized setups and is configured entirely through environment variables. It supports configurable backup intervals, flexible file naming, and optional cleanup of local artifacts after successful uploads.

Retention policies can be applied to control long-term storage usage. Multiple strategies are available, ranging from simple "keep last N" behavior to more advanced models like Grandfather-Father-Son (GFS), allowing a balance between short-term recovery points and long-term history.

The focus of this project is reliability, predictable behavior, and minimal operational overhead.

## Table of Contents

- [Storage Backends](#storage-backends)
- [Remote Layout](#remote-layout)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Retention Strategies](#retention-strategies)

## TODO's
- [ ] better scheduler like cron job
- [ ] better readme's (format code commands etc)

## Storage Backends

| Backend | Status |
|---------|--------|
| SFTP | ✅ Supported |
| S3 / compatible | 🔜 Planned |

## Remote Layout

Backups are stored in a structured directory tree on the remote:

```
paperless/
├── backups/
│   └── YYYY/MM/DD/
│       └── <timestamp>.tar.gz
├── metadata/
│   └── YYYY/MM/DD/
│       └── <timestamp>.tar.gz.sha256
└── latest.tar.gz
```

Each archive has a corresponding `.sha256` sidecar written to `metadata/` after a successful upload. `latest.tar.gz` always points to the most recent backup.

## Getting Started

```yaml
services:
  paperless-backup:
    image: ghcr.io/rechergg/paperless-backup:latest
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      PAPERLESS_CONTAINER: paperless-webserver
      SFTP_HOST: your-storage-box.example.com
      SFTP_USERNAME: your-username
      SFTP_KEY: your-private-key
      SFTP_PATH: paperless
      BACKUP_INTERVAL_HOURS: 6
```

A full `docker-compose.coolify.yml` is available in the repository for Coolify deployments.

## Configuration

All configuration is done through environment variables. The `config.toml` in the repository documents every available option with its default value.

| Variable | Default | Description |
|----------|---------|-------------|
| `PAPERLESS_CONTAINER` | `paperless-webserver` | Name of the Paperless Docker container |
| `SFTP_HOST` | — | SFTP hostname |
| `SFTP_PORT` | `22` | SFTP port |
| `SFTP_USERNAME` | — | SFTP username |
| `SFTP_KEY` | — | SSH private key (preferred over password) |
| `SFTP_PASSWORD` | — | SSH password (fallback) |
| `SFTP_PATH` | `paperless` | Remote root directory |
| `BACKUP_INTERVAL_HOURS` | `6` | Hours between backups |
| `BACKUP_FILENAME_TEMPLATE` | `{timestamp}.tar.gz` | Archive filename template |
| `BACKUP_DELETE_LOCAL_AFTER_UPLOAD` | `true` | Delete local archive after upload |
| `BACKUP_KEEP_FAILED` | `true` | Keep local workspace on failure for debugging |

## Retention Strategies

Configure the strategy via `RETENTION_STRATEGY` (default: `gfs`).

### GFS — Grandfather-Father-Son

The default strategy. Keeps backups across four tiers so you always have recent snapshots as well as long-term history.

| Variable | Default | Description |
|----------|---------|-------------|
| `RETENTION_HOURLY` | `24` | Most recent backups to keep |
| `RETENTION_DAILY` | `7` | One backup per day for the last N days |
| `RETENTION_WEEKLY` | `4` | One backup per week for the last N weeks |
| `RETENTION_MONTHLY` | `12` | One backup per month for the last N months |

A file is kept if it qualifies in **any** tier — so a weekly snapshot is never deleted just because the hourly window has passed.

### Simple

Keeps only the N most recent backups regardless of age.

| Variable | Default | Description |
|----------|---------|-------------|
| `RETENTION_KEEP_LAST` | `10` | Number of backups to retain |

### Time-based

Deletes any backup older than a configured number of days.

| Variable | Default | Description |
|----------|---------|-------------|
| `RETENTION_MAX_AGE_DAYS` | `30` | Maximum backup age in days |
| `RETENTION_MINIMUM_KEEP` | `1` | Always keep at least this many recent backups |

`RETENTION_MINIMUM_KEEP` prevents full deletion during extended outages — even if all backups exceed `max_age_days`, the most recent one is never removed.

### Daily

Keeps one backup per calendar day for the last N days.

| Variable | Default | Description |
|----------|---------|-------------|
| `RETENTION_KEEP_DAYS` | `7` | Number of days to retain |
| `RETENTION_MINIMUM_KEEP` | `1` | Safety floor |

### None

Disables cleanup entirely. All backups are kept indefinitely.
Set `RETENTION_STRATEGY=none` — no additional variables required.

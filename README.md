<div align="center">
  <img src=".github/assets/logo.png" width="144" height="144" alt="paperless-backup" />
  <h1>paperless-backup</h1>

  <p><strong>Open-source lightweight backup tool for paperless-ngx</strong></p>

  [![python-badge](https://badges.penpow.dev/badges/built-with/python/cozy.png)](https://www.python.org/)
  [![dono-badge](https://badges.penpow.dev/badges/donate/github-sponsors-singular/cozy.png)](https://github.com/sponsors/RECHERGG)
  [![docker-badge](https://badges.penpow.dev/badges/supported/docker/cozy.png)](https://hub.docker.com/r/rechergg/paperless-backup)
</div>

paperless-backup is a lightweight backup utility for paperless-ngx environments. It automates the creation of consistent backups from a running paperless container and transfers them to remote storage, such as an SFTP server.

The tool is designed to run in containerized setups and is configured entirely through environment variables. It supports configurable backup intervals, flexible file naming, and optional cleanup of local artifacts after successful uploads.

Retention policies can be applied to control long-term storage usage. Multiple strategies are available, ranging from simple “keep last N” behavior to more advanced models like Grandfather-Father-Son (GFS), allowing a balance between short-term recovery points and long-term history.

The focus of this project is reliability, predictable behavior, and minimal operational overhead.

## Table of Contents

- [TODO's](#todos)
- [Currently supported methods](#currently-supported-methods)
- [Retention Strategies](#retention-strategies)
  - [GFS (Grandfather-Father-Son)](#gfs-grandfather-father-son)
  - [Simple Strategy](#simple-strategy)
  - [Time-Based Strategy](#time-based-strategy)
  - [Daily-Only Strategy](#daily-only-strategy)
  - [No Retention](#no-retention)

# Currently supported methods
- SFTP

## Retention Strategies

This project supports multiple retention strategies to control how many backups are kept and when old backups are deleted. The goal is to balance storage usage with the ability to restore data from different points in time.

### GFS (Grandfather-Father-Son)

The default strategy is `gfs`, which implements a tiered retention model:

- Hourly (Son): short-term backups for recent changes  
- Daily (Father): medium-term backups for day-level recovery  
- Weekly / Monthly (Grandfather): long-term backups for historical states  

Each tier defines how many backups of that type are retained:

- `hourly`: number of hourly backups to keep  
- `daily`: number of daily backups to keep  
- `weekly`: number of weekly backups to keep  
- `monthly`: number of monthly backups to keep  

Backups are grouped into time intervals and only a limited number per interval is retained. As backups age, they are effectively represented by fewer, more coarse-grained restore points (e.g. hourly → daily → weekly → monthly).

This reduces storage usage while preserving useful recovery points across different time ranges.

### Simple Strategy

The `simple` strategy keeps only the most recent backups:

- `keep_last`: total number of backups to retain  

All older backups are deleted regardless of age or distribution.

### Time-Based Strategy

The `time` strategy deletes backups based on their age:

- `max_age_days`: maximum age in days  

Any backup older than this threshold is removed. The number of retained backups depends on how frequently backups are created.

### Daily-Only Strategy

The `daily-only` strategy retains one backup per day:

- `keep_days`: number of days to keep  

This is a simplified strategy without hourly or long-term grouping.

### No Retention

The `none` strategy disables cleanup.

All backups are kept indefinitely. This will eventually lead to unbounded storage usage and should only be used in controlled environments.

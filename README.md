<div align="center">

# paperless-backup

[![docker-badge](https://badges.penpow.dev/badges/supported/docker/cozy.png)](https://www.docker.com/)
[![dono-badge](https://badges.penpow.dev/badges/donate/github-sponsors-singular/cozy.png)](https://github.com/sponsors/RECHERGG)
[![python-badge](https://badges.penpow.dev/badges/built-with/python/cozy.png)](https://www.python.org/)

</div>

## Table of Contents

- [TODO's](#todos)
- [Currently supported methods](#currently-supported-methods)
- [Retention Strategies](#retention-strategies)
  - [GFS (Grandfather-Father-Son)](#gfs-grandfather-father-son)
  - [Simple Strategy](#simple-strategy)
  - [Time-Based Strategy](#time-based-strategy)
  - [Daily-Only Strategy](#daily-only-strategy)
  - [No Retention](#no-retention)

# TODO's
- [ ] retention rules
- [ ] .tmp file
- [ ] checksume checking
- [ ] implement the other retention rules
- [ ] publish on docker hub
- [ ] update docker link to published docker image


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

---

### Simple Strategy

The `simple` strategy keeps only the most recent backups:

- `keep_last`: total number of backups to retain  

All older backups are deleted regardless of age or distribution.

---

### Time-Based Strategy

The `time` strategy deletes backups based on their age:

- `max_age_days`: maximum age in days  

Any backup older than this threshold is removed. The number of retained backups depends on how frequently backups are created.

---

### Daily-Only Strategy

The `daily-only` strategy retains one backup per day:

- `keep_days`: number of days to keep  

This is a simplified strategy without hourly or long-term grouping.

---

### No Retention

The `none` strategy disables cleanup.

All backups are kept indefinitely. This will eventually lead to unbounded storage usage and should only be used in controlled environments.
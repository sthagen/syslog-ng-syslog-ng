# Repeatable Docker Image Publishing

## Overview

**Goals:**

- Keep Docker images up-to-date with security patches while maintaining reproducibility
- Enable both automated weekly rebuilds and manual version-specific publishes
- Support locked package versions for true reproducibility when needed

**Key Features:**

- **Mutable base images** - always pulls latest security patches from `debian:trixie` / `almalinux:9` etc.
- **Automatic version detection** from git tags (no manual version tracking needed)
- **Optional package locking** - freeze syslog-ng version while OS updates (`pkg-version-lock`)
- **Dual authentication** - works with both manual triggers and workflow calls
- **CVE scanning** - integrated Trivy scans uploaded to GitHub Security tab

## Quick Reference

| Use Case | Trigger Type | pkg-version | pkg-version-lock | pkg-image-type |
|----------|--------------|-------------|------------------|----------------|
| **Weekly automated rebuild** (RECOMMENDED) | `weekly-docker-publish.yml` | Auto-detected | _empty_ | `deb` + `rpm` (both, in parallel) |
| **Manual publish specific version** | `workflow_dispatch` (UI) | **REQUIRED** (e.g., `4.11.0`) | _empty_ | `deb` or `rpm` (UI pre-selects `deb`) |
| **Called from another workflow** | `workflow_call` | Optional | _empty_ | `deb` or `rpm` (required) |
| **Lock package version + update OS** | Either | Version | **Lock** (e.g., `4.11.0-1`) | as needed |
| **Test before publishing** | Either | As needed | Any | Set `pkg-push: false` |

## Parameters

| Parameter | workflow_dispatch | workflow_call | Default | Description |
|-----------|-------------------|---------------|---------|-------------|
| `pkg-type` | **Required** | **Required** | - | `stable` or `nightly` |
| `pkg-version` | **Required** | Optional | _empty_ | Version tag (e.g., `4.11.0`). Empty = use current git tag (workflow_call only) |
| `pkg-version-lock` | Optional | Optional | _empty_ | Lock package version (e.g., `4.5.0-1`). Empty = install latest. APT or RPM, per `pkg-image-type` |
| `pkg-image-type` | **Required** | **Required** | `deb` (dispatch UI pre-selection only) | Packaging flavor: `deb` publishes to `balabit/syslog-ng` (base `debian:trixie`), `rpm` publishes to `balabit/syslog-ng-rpm` (base `almalinux:9`). The base image is derived from this input. |
| `pkg-push` | **Required** | Optional | dispatch:`false` / call:`true` | Push to Docker Hub |

**Secrets:** Use `DOCKERHUB_USERNAME` / `DOCKERHUB_PASSWORD` for manual runs, or `dockerhub-username` / `dockerhub-password` when calling from workflows. Both work via fallback.

## Common Workflows

### Automated Weekly Rebuilds (Production)

The `weekly-docker-publish.yml` workflow automatically:

- Detects latest `syslog-ng-*` git tag
- Rebuilds with latest base OS
- Publishes weekly

No manual configuration needed.

### Manual Publish

```yaml
# Via GitHub Actions UI
pkg-type: stable
pkg-version: 4.11.0  # REQUIRED
pkg-push: true
```

### Lock Package Version (Reproducible Rebuilds)

```yaml
with:
  pkg-type: stable
  pkg-version: '4.11.0'
  pkg-version-lock: '4.11.0-1'  # Locks package, OS updates only
  pkg-push: true
```

### Nightly Builds

```yaml
# Manual trigger
pkg-type: nightly
pkg-version: nightly  # REQUIRED but ignored
pkg-push: true
```

## How It Works

**Version Detection:**

- Manual (`workflow_dispatch`): Requires explicit version
- Automated (`weekly-docker-publish.yml`): Auto-detects from git tags using `docker/metadata-action`
- Workflow call: Optional version (empty = current tag)

**Package Installation:**

- Without `pkg-version-lock`: Installs latest from repository
- With `pkg-version-lock`: Locks to specific package (e.g., APT: `syslog-ng=4.5.0-1`, RPM: `syslog-ng-4.5.0-1`)

**Base Image:** Always pulls latest tag (e.g., `debian:trixie:latest`), ensuring security patches

**Version Format:**

- `pkg-version: '4.5.0'` → Docker tag: `balabit/syslog-ng:4.5.0`
- `pkg-version-lock: '4.5.0-1'` → APT install: `syslog-ng=4.5.0-1` (Debian flavor) / `syslog-ng-4.5.0-1` (RPM flavor)

## Finding Package Versions

```bash
# List available versions
curl -s https://ose-repo.syslog-ng.com/apt/dists/stable/debian-trixie/binary-amd64/Packages \
  | grep -A5 "^Package: syslog-ng$" | grep "Version:"

# Or from within container
apt-cache madison syslog-ng
```

## Troubleshooting

**Authentication fails**: Check secrets are set (`DOCKERHUB_USERNAME`/`DOCKERHUB_PASSWORD` for manual, lowercase for workflow_call)

**Push denied for `balabit/syslog-ng-rpm`** (or any new image repo): the Docker Hub repository must be pre-created and the access token scope must include it. Same applies to any future `balabit/syslog-ng-*` repo.

**Package not found**: Verify version exists with `apt-cache madison syslog-ng` (DEB) or `dnf --showduplicates list syslog-ng` (RPM)

**Build time increased**: Expected when base image updates

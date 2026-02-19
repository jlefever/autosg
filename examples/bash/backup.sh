#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="${1:-.}"
BACKUP_DIR="${2:-/tmp/backup}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="backup_${TIMESTAMP}.tar.gz"

log_info() {
    echo "[INFO] $(date '+%H:%M:%S') $*"
}

log_error() {
    echo "[ERROR] $(date '+%H:%M:%S') $*" >&2
}

create_backup() {
    local source="$1"
    local dest="$2"
    local archive="$3"

    mkdir -p "$dest"

    if tar -czf "${dest}/${archive}" -C "$source" .; then
        log_info "Backup created: ${dest}/${archive}"
    else
        log_error "Failed to create backup"
        return 1
    fi
}

cleanup_old_backups() {
    local backup_dir="$1"
    local keep_count="${2:-5}"

    local count
    count=$(find "$backup_dir" -name "backup_*.tar.gz" | wc -l)

    if [ "$count" -gt "$keep_count" ]; then
        find "$backup_dir" -name "backup_*.tar.gz" -printf '%T@ %p\n' \
            | sort -n \
            | head -n "$((count - keep_count))" \
            | cut -d' ' -f2- \
            | xargs rm -f
        log_info "Cleaned up old backups, kept last ${keep_count}"
    fi
}

create_backup "$SOURCE_DIR" "$BACKUP_DIR" "$ARCHIVE_NAME"
cleanup_old_backups "$BACKUP_DIR"

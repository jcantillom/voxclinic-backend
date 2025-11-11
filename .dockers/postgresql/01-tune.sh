#!/usr/bin/env bash
set -e
PGDATA="${PGDATA:-/var/lib/postgresql/data}"
echo "listen_addresses='*'" >> "$PGDATA/postgresql.conf"
# endurecer en prod: limita a tu red/VPC en lugar de 0.0.0.0/0
echo "host    all             all             0.0.0.0/0               md5" >> "$PGDATA/pg_hba.conf"
echo "host    all             all             ::/0                    md5" >> "$PGDATA/pg_hba.conf"

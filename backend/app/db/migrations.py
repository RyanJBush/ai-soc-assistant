from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Migration:
    version: str
    description: str
    sql: str
    checksum: str


def parse_migration_file(path: Path) -> Migration:
    sql = path.read_text(encoding="utf-8")
    version, _, description = path.stem.partition("__")
    return Migration(
        version=version,
        description=description.replace("_", " "),
        sql=sql,
        checksum=hashlib.sha256(sql.encode("utf-8")).hexdigest(),
    )


def load_migrations(sql_dir: Path, dialect: str) -> list[Migration]:
    pattern = "*_sqlite.sql" if dialect == "sqlite" else "*.sql"
    files = sorted(sql_dir.glob(pattern))
    migrations: list[Migration] = []
    for path in files:
        if dialect != "sqlite" and path.name.endswith("_sqlite.sql"):
            continue
        migrations.append(parse_migration_file(path))
    return migrations

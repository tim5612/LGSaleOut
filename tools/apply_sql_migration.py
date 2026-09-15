"""Apply one reviewed SQL migration to a non-production LGSale database."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
import lgsale_db as db


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("migration",type=Path);parser.add_argument("--allow-production",action="store_true")
    args=parser.parse_args();environment=os.getenv("LGSALEOUT_ENV","")
    if not args.allow_production and environment.casefold() not in {"lgdeva","lgdevb","development","test"}:
        raise SystemExit(f"Refusing migration in environment {environment!r}; back up production and pass --allow-production explicitly")
    path=args.migration.resolve()
    if BASE not in path.parents or path.suffix.casefold()!=".sql":raise SystemExit("Migration must be a .sql file inside this project")
    batches=[part.strip() for part in re.split(r"(?im)^\s*GO\s*$",path.read_text(encoding="utf-8-sig")) if part.strip()]
    connection=db.connect()
    try:
        cursor=connection.cursor()
        for batch in batches:cursor.execute(batch)
        connection.commit()
        print(f"Applied {path.name} to {environment} ({len(batches)} batches)")
    except Exception:
        connection.rollback();raise
    finally:connection.close()


if __name__=="__main__":main()

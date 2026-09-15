"""Compare dbTable/dbColumn metadata in the standard draw.io ERD with SQL Server."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
import sys
import re

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

import lgsale_db as db


ERD = BASE / "Codex筆記" / "LGSale_ERD_標準.drawio"


def erd_schema() -> dict[str, dict[str, str]]:
    root = ET.parse(ERD).getroot()
    result: dict[str, dict[str, str]] = defaultdict(dict)
    for item in root.iter("UserObject"):
        table = item.attrib.get("dbTable")
        if table:
            result.setdefault(table, {})
        column = item.attrib.get("dbColumn")
        identifier = item.attrib.get("id", "")
        if column and identifier.startswith("row_"):
            parent = identifier.removeprefix("row_").removesuffix("_" + column)
            result[parent][column] = item.attrib.get("dbType", "")
    return dict(result)


def database_schema() -> dict[str, dict[str, str]]:
    sql = """
    SELECT t.name,c.name,ty.name
      FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id
      JOIN sys.columns c ON c.object_id=t.object_id
      JOIN sys.types ty ON ty.user_type_id=c.user_type_id
     WHERE s.name='dbo' AND t.is_ms_shipped=0
     ORDER BY t.name,c.column_id
    """
    with db.connect() as connection:
        cursor = connection.cursor(); cursor.execute(sql)
        result: dict[str, dict[str, str]] = defaultdict(dict)
        for table, column, data_type in cursor.fetchall():
            result[table][column] = data_type
    return dict(result)


def main() -> None:
    erd, actual = erd_schema(), database_schema()
    print(f"ERD tables: {len(erd)}; database tables: {len(actual)}")
    for table in sorted(set(erd) | set(actual)):
        if table not in erd:
            print(f"DB only table: {table}")
            continue
        if table not in actual:
            print(f"ERD only table: {table}")
            continue
        missing = sorted(set(actual[table]) - set(erd[table]))
        extra = sorted(set(erd[table]) - set(actual[table]))
        base_type=lambda value:re.sub(r"\(.*\)$","",value.strip().lower())
        type_diff = sorted(column for column in set(erd[table]) & set(actual[table])
                           if base_type(erd[table][column]) != base_type(actual[table][column]))
        if missing or extra or type_diff:
            print(f"{table}: DB-only columns={missing}; ERD-only columns={extra}; type differences={[(c, erd[table][c], actual[table][c]) for c in type_diff]}")


if __name__ == "__main__":
    main()

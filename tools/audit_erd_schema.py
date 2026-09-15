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
    table_names: set[str] = set()
    for item in root.iter("UserObject"):
        table = item.attrib.get("dbTable")
        if table:
            table_names.add(table)
            result.setdefault(table, {})
        column = item.attrib.get("dbColumn")
        identifier = item.attrib.get("id", "")
        if column and identifier.startswith("row_"):
            parent = identifier.removeprefix("row_").removesuffix("_" + column)
            result[parent][column] = item.attrib.get("dbType", "")

    # draw.io may serialize newly edited database shapes as plain mxCell nodes,
    # while retaining the stable table_/row_ identifiers.  Include those nodes
    # so an editor save does not create false DB-only differences.
    for item in root.iter("mxCell"):
        identifier = item.attrib.get("id", "")
        if identifier.startswith("table_"):
            table_names.add(identifier.removeprefix("table_"))
    for table in table_names:
        result.setdefault(table, {})
    for item in root.iter("mxCell"):
        identifier = item.attrib.get("id", "")
        if not identifier.startswith("row_"):
            continue
        row_name = identifier.removeprefix("row_")
        table = next(
            (name for name in sorted(table_names, key=len, reverse=True)
             if row_name.startswith(name + "_")),
            None,
        )
        if table is None:
            continue
        column = row_name.removeprefix(table + "_")
        result[table].setdefault(column, "")
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
                           if erd[table][column]
                           and base_type(erd[table][column]) != base_type(actual[table][column]))
        if missing or extra or type_diff:
            print(f"{table}: DB-only columns={missing}; ERD-only columns={extra}; type differences={[(c, erd[table][c], actual[table][c]) for c in type_diff]}")


if __name__ == "__main__":
    main()

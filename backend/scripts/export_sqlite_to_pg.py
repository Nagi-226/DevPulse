#!/usr/bin/env python3
"""SQLite → PostgreSQL 数据导出脚本.

将本地 SQLite 数据库中的历史数据导出为 JSON 文件，
后续可通过 Alembic 迁移或手动导入 PostgreSQL。

用法:
    python scripts/export_sqlite_to_pg.py [--db ./devpulse.db] [--output ./export.json]

功能:
    1. 连接 SQLite 数据库
    2. 导出 repositories、weekly_reports、favorites、star_history 四表数据
    3. 输出为 JSON 文件（每表一个 key）
    4. 显示各表记录数校验
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime


def export_sqlite(db_path: str, output_path: str) -> dict:
    """导出 SQLite 数据库所有表数据到字典.

    Args:
        db_path: SQLite 数据库文件路径.
        output_path: 输出 JSON 文件路径.

    Returns:
        包含各表记录数的统计字典.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    tables = ["repositories", "weekly_reports", "favorites", "star_history"]
    export_data: dict[str, list[dict]] = {}
    stats: dict[str, int] = {}

    for table in tables:
        try:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            export_data[table] = [dict(row) for row in rows]
            stats[table] = len(rows)
            print(f"  ✓ {table}: {len(rows)} rows")
        except sqlite3.OperationalError as e:
            print(f"  ⚠ {table}: skipped ({e})")
            export_data[table] = []
            stats[table] = 0

    conn.close()

    # 写入 JSON
    output = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "source": db_path,
        "stats": stats,
        "data": export_data,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n✅ Export complete: {output_path}")
    print(f"   Total tables: {len(tables)}")
    print(f"   Total rows: {sum(stats.values())}")
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DevPulse SQLite → PostgreSQL 数据导出工具"
    )
    parser.add_argument(
        "--db",
        default="./devpulse.db",
        help="SQLite 数据库文件路径 (默认: ./devpulse.db)",
    )
    parser.add_argument(
        "--output",
        default="./export.json",
        help="输出 JSON 文件路径 (默认: ./export.json)",
    )
    args = parser.parse_args()

    print(f"📦 DevPulse SQLite Export Tool")
    print(f"   Source: {args.db}")
    print(f"   Target: {args.output}")
    print()

    try:
        export_sqlite(args.db, args.output)
    except FileNotFoundError:
        print(f"❌ 数据库文件不存在: {args.db}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 导出失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

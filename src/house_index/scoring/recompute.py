from __future__ import annotations

import sqlite3
from typing import Any, Callable

from house_index.db import repository as repo
from house_index.scoring.engine import compute


def recompute_all(
    conn: sqlite3.Connection,
    config: dict[str, dict[str, Any]],
    progress: Callable[[int, int], None] | None = None,
) -> int:
    props = repo.list_properties(conn, order_by="id ASC")
    total = len(props)
    for i, prop in enumerate(props, start=1):
        result = compute(prop, config)
        repo.update_index_cache(conn, prop.id, result.total, result.breakdown)
        if progress is not None:
            progress(i, total)
    return total

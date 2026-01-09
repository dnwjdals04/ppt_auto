# services/cleanup.py
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Iterable


def _safe_unlink(fp: Path) -> bool:
    try:
        fp.unlink()
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def cleanup_dir_by_age(
    base_dir: Path,
    *,
    patterns: Iterable[str],
    max_age_seconds: int,
) -> dict:
    """
    base_dir 아래에서 patterns에 매칭되는 파일들을 찾아
    mtime 기준으로 max_age_seconds보다 오래된 파일은 삭제한다.
    """
    base_dir = Path(base_dir)
    if not base_dir.exists():
        return {"scanned": 0, "deleted": 0}

    now = time.time()
    scanned = 0
    deleted = 0

    for pat in patterns:
        for fp in base_dir.glob(pat):
            if not fp.is_file():
                continue
            scanned += 1

            try:
                mtime = fp.stat().st_mtime
            except FileNotFoundError:
                continue

            age = now - mtime
            if age >= max_age_seconds:
                if _safe_unlink(fp):
                    deleted += 1

    return {"scanned": scanned, "deleted": deleted}


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

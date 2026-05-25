from __future__ import annotations

import hashlib
from pathlib import Path


class MemoryInvalidator:
    @staticmethod
    def fingerprint(paths: list[str]) -> str:
        digest = hashlib.sha256()
        for raw in sorted(paths):
            path = Path(raw)
            digest.update(raw.encode("utf-8"))
            if not path.exists():
                digest.update(b"<missing>")
                continue
            stat = path.stat()
            digest.update(str(int(stat.st_mtime)).encode("utf-8"))
            digest.update(str(stat.st_size).encode("utf-8"))
        return digest.hexdigest()

    @staticmethod
    def has_changed(previous: str | None, current: str) -> bool:
        return bool(previous) and previous != current

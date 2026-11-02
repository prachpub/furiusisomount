"""Persistence: history of opened images, mounted images list, activity log."""

from __future__ import annotations

import os
from datetime import datetime

from .mounts import MountInfo

HISTORY_LIMIT = 10


def append_log(log_file: str, message: str) -> None:
    """Append *message* to the activity log (best effort, never raises)."""
    try:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as handle:
            handle.write("[%s] %s\n" % (stamp, message))
    except OSError:
        pass


class HistoryStore:
    """Most recently used image files, newest first."""

    def __init__(self, path: str, limit: int = HISTORY_LIMIT):
        self.path = path
        self.limit = limit
        self.items: list[str] = []

    def load(self) -> list[str]:
        self.items = []
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as handle:
                    self.items = [line.strip() for line in handle if line.strip()]
        except OSError:
            self.items = []
        return list(self.items)

    def save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(self.items))
        except OSError:
            pass

    def add(self, image_path: str) -> list[str]:
        if image_path in self.items:
            self.items.remove(image_path)
        self.items.insert(0, image_path)
        self.items = self.items[: self.limit]
        self.save()
        return list(self.items)


class MountedListStore:
    """CSV persistence for the list of mounted images."""

    def __init__(self, path: str):
        self.path = path

    def load(self) -> list[MountInfo]:
        result: list[MountInfo] = []
        try:
            if not os.path.exists(self.path):
                return result
            with open(self.path, "r", encoding="utf-8") as handle:
                for line in handle:
                    parts = line.rstrip("\n").split(",")
                    if len(parts) >= 3 and parts[0]:
                        result.append(
                            MountInfo(
                                mount_point=parts[0],
                                image_file=parts[1],
                                method=parts[2],
                                device=parts[3] if len(parts) > 3 else "",
                            )
                        )
        except OSError:
            return []
        return result

    def save(self, mounts: list[MountInfo]) -> None:
        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as handle:
                for info in mounts:
                    handle.write(
                        "%s,%s,%s,%s\n"
                        % (info.mount_point, info.image_file, info.method, info.device)
                    )
        except OSError:
            pass

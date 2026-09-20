from __future__ import annotations

import re
import threading
import urllib.parse

import requests
from PySide6.QtCore import QObject, Signal


GITHUB_REPOSITORY = "Angonikro/MeshCom-Guru"
GITHUB_RELEASE_API = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/latest"


def _version_tuple(value: str) -> tuple[int, ...]:
    text = str(value or "").strip().lstrip("vV")
    parts = re.findall(r"\d+", text)
    return tuple(int(p) for p in parts[:4]) or (0,)


def check_latest_release(current_version: str, timeout: float = 5.0) -> dict:
    """Read the latest public GitHub release. Never downloads or installs anything."""
    try:
        response = requests.get(
            GITHUB_RELEASE_API,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "MeshCom-Guru"},
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()

        tag = str(data.get("tag_name", "")).strip()
        if not tag:
            return {"ok": False, "error": "GitHub hat keine Release-Version zurückgegeben."}

        latest = tag.lstrip("vV")
        current = str(current_version or "").strip().lstrip("vV")
        return {
            "ok": True,
            "current": current,
            "latest": latest,
            "update_available": _version_tuple(latest) > _version_tuple(current),
            "url": data.get("html_url") or f"https://github.com/{GITHUB_REPOSITORY}/releases/latest",
            "name": str(data.get("name") or tag),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


class UpdateChecker(QObject):
    """Small background checker so the GUI never waits for GitHub."""

    result = Signal(object)

    def check_async(self, current_version: str) -> None:
        threading.Thread(
            target=self._run,
            args=(current_version,),
            daemon=True,
            name="MeshCom-Guru-UpdateCheck",
        ).start()

    def _run(self, current_version: str) -> None:
        self.result.emit(check_latest_release(current_version))

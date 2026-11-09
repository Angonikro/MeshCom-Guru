"""Asynchronous image uploader for MeshCom-Guru (imgdb.io and Catbox)."""
import os
import threading
import requests
from PySide6.QtCore import QObject, Signal


class PicrdUploader(QObject):
    finished = Signal(str)
    error = Signal(str)

    CATBOX_API_URL = "https://catbox.moe/user/api.php"
    IMGDB_API_URL = "https://imgdb.io/api/v1/upload"
    IMGDB_MAX_BYTES = 16 * 1024 * 1024
    CATBOX_MAX_BYTES = 200 * 1024 * 1024

    def upload(self, path: str, provider: str = "catbox") -> None:
        thread = threading.Thread(
            target=self._upload_worker,
            args=(str(path), str(provider).lower()),
            daemon=True,
            name="meshcom-image-upload",
        )
        thread.start()

    def _upload_worker(self, path: str, provider: str) -> None:
        try:
            size = os.path.getsize(path)
            if provider == "imgdb":
                limit = self.IMGDB_MAX_BYTES
                label = "imgdb.io"
            elif provider == "catbox":
                limit = self.CATBOX_MAX_BYTES
                label = "Catbox"
            else:
                raise ValueError("Unbekannter Bildanbieter.")
            if size > limit:
                raise ValueError(f"Das Bild ist größer als {limit // (1024 * 1024)} MB.")
            if provider == "imgdb":
                url = self._upload_imgdb(path)
            else:
                url = self._upload_catbox(path)
            self.finished.emit(url)
        except Exception as exc:
            self.error.emit(str(exc))

    def _upload_imgdb(self, path: str) -> str:
        for use_ttl in (True, False):
            with open(path, "rb") as handle:
                data = {"ttl": "0"} if use_ttl else {}
                response = requests.post(
                    self.IMGDB_API_URL,
                    files={"file": (os.path.basename(path), handle)},
                    data=data,
                    headers={"User-Agent": "MeshCom-Guru/0.5.11"},
                    timeout=(10, 120),
                )
            if response.status_code in (200, 201):
                try:
                    payload = response.json()
                except Exception as exc:
                    raise RuntimeError("imgdb.io hat keine gültige JSON-Antwort geliefert.") from exc
                image_url = str(payload.get("url") or "").strip()
                if image_url.startswith(("https://", "http://")):
                    return image_url
                raise RuntimeError("imgdb.io hat keine gültige Bild-URL zurückgegeben.")
            if not use_ttl:
                detail = response.text[:300].strip()
                raise RuntimeError(
                    f"imgdb.io-Upload fehlgeschlagen (HTTP {response.status_code})"
                    + (f": {detail}" if detail else ".")
                )
        raise RuntimeError("imgdb.io-Upload fehlgeschlagen.")

    def _upload_catbox(self, path: str) -> str:
        with open(path, "rb") as handle:
            response = requests.post(
                self.CATBOX_API_URL,
                data={"reqtype": "fileupload"},
                files={"fileToUpload": (os.path.basename(path), handle)},
                headers={"User-Agent": "MeshCom-Guru/0.5.11"},
                timeout=(10, 180),
            )
        if response.status_code != 200:
            detail = response.text[:300].strip()
            raise RuntimeError(
                f"Catbox-Upload fehlgeschlagen (HTTP {response.status_code})"
                + (f": {detail}" if detail else ".")
            )
        url = response.text.strip()
        if not url.startswith("https://files.catbox.moe/"):
            raise RuntimeError("Catbox hat keine gültige Bild-URL zurückgegeben.")
        return url

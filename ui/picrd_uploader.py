"""Asynchronous image uploader for MeshCom-Guru (picrd.com and imgdb.io)."""
import os
import threading
import requests
from PySide6.QtCore import QObject, Signal


class PicrdUploader(QObject):
    finished = Signal(str)
    error = Signal(str)

    PICRD_API_URL = "https://picrd.com/api/upload"
    IMGDB_API_URL = "https://imgdb.io/api/v1/upload"
    MAX_BYTES = 16 * 1024 * 1024

    def upload(self, path: str, provider: str = "picrd") -> None:
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
            limit = self.MAX_BYTES if provider == "imgdb" else 10 * 1024 * 1024
            if size > limit:
                raise ValueError(f"Das Bild ist größer als {limit // (1024 * 1024)} MB.")
            if provider == "imgdb":
                url = self._upload_imgdb(path)
            elif provider == "picrd":
                url = self._upload_picrd(path)
            else:
                raise ValueError("Unbekannter Bildanbieter.")
            self.finished.emit(url)
        except Exception as exc:
            self.error.emit(str(exc))

    def _upload_imgdb(self, path: str) -> str:
        # Try to request no expiry first. If the API rejects that parameter,
        # retry once with its documented default TTL.
        for use_ttl in (True, False):
            with open(path, "rb") as handle:
                data = {"ttl": "0"} if use_ttl else {}
                response = requests.post(
                    self.IMGDB_API_URL,
                    files={"file": (os.path.basename(path), handle)},
                    data=data,
                    headers={"User-Agent": "MeshCom-Guru/0.5.9"},
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

    def _upload_picrd(self, path: str) -> str:
        with open(path, "rb") as handle:
            response = requests.post(
                self.PICRD_API_URL,
                files={"file": (os.path.basename(path), handle)},
                data={"visibility": "unlisted"},
                headers={"User-Agent": "MeshCom-Guru/0.5.9"},
                timeout=(10, 120),
            )
        if response.status_code == 429:
            raise RuntimeError("picrd: Upload-Limit erreicht.")
        if response.status_code != 200:
            detail = ""
            try:
                payload = response.json()
                detail = str(payload.get("error") or payload.get("message") or "")
            except Exception:
                pass
            raise RuntimeError(
                f"picrd-Upload fehlgeschlagen (HTTP {response.status_code})"
                + (f": {detail}" if detail else ".")
            )
        payload = response.json()
        url = str(payload.get("page_url") or payload.get("image_url") or "").strip()
        if not url.startswith(("http://", "https://")):
            raise RuntimeError("picrd hat keine gültige Bild-URL zurückgegeben.")
        return url

"""Small asynchronous picrd.com uploader for MeshCom-Guru.

The uploader intentionally does not open a browser and does not touch either
Qt's or GTK's clipboard.  A selected image is uploaded directly to picrd's
REST API and the returned page URL is emitted to the Qt UI.
"""

import threading

import requests
from PySide6.QtCore import QObject, Signal


class PicrdUploader(QObject):
    finished = Signal(str)
    error = Signal(str)

    API_URL = "https://picrd.com/api/upload"
    MAX_BYTES = 10 * 1024 * 1024

    def upload(self, path: str) -> None:
        thread = threading.Thread(
            target=self._upload_worker,
            args=(str(path),),
            daemon=True,
            name="picrd-upload",
        )
        thread.start()

    def _upload_worker(self, path: str) -> None:
        try:
            with open(path, "rb") as handle:
                data = handle.read(self.MAX_BYTES + 1)
            if len(data) > self.MAX_BYTES:
                raise ValueError("Das Bild ist größer als 10 MB.")

            with open(path, "rb") as handle:
                response = requests.post(
                    self.API_URL,
                    files={"file": (path.rsplit("/", 1)[-1], handle)},
                    data={"visibility": "unlisted"},
                    headers={"User-Agent": "MeshCom-Guru/0.3.96"},
                    timeout=(10, 120),
                )

            if response.status_code == 429:
                raise RuntimeError("picrd: Upload-Limit erreicht (60 Uploads pro Stunde).")
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
            # page_url is the useful human-facing link, analogous to the old
            # DirectUpload link.  Fall back to the direct image URL if needed.
            url = str(payload.get("page_url") or payload.get("image_url") or "").strip()
            if not url.startswith(("http://", "https://")):
                raise RuntimeError("picrd hat keine gültige Bild-URL zurückgegeben.")

            self.finished.emit(url)
        except Exception as exc:
            self.error.emit(str(exc))

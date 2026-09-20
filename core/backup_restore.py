from __future__ import annotations

import configparser
import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from core.settings import USER_CONFIG_DIR, SETTINGS_FILE


BACKUP_FORMAT = "MeshCom-Guru-Backup"
BACKUP_VERSION = 1


def create_backup(destination: str | os.PathLike) -> tuple[bool, str]:
    """Create a ZIP backup of the user's ~/.MeshCom data."""
    destination = Path(destination).expanduser()
    try:
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not SETTINGS_FILE.exists():
            # Ensure the current settings exist before creating a backup.
            from core.settings import load_settings
            load_settings()

        destination.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            info = {
                "format": BACKUP_FORMAT,
                "version": BACKUP_VERSION,
                "created": datetime.now().isoformat(timespec="seconds"),
                "application": "MeshCom-Guru",
            }
            zf.writestr("backup_info.json", json.dumps(info, ensure_ascii=False, indent=2))

            if USER_CONFIG_DIR.exists():
                for path in USER_CONFIG_DIR.rglob("*"):
                    if not path.is_file():
                        continue
                    # Never put the backup itself into the backup.
                    if path.resolve() == destination.resolve():
                        continue
                    arcname = Path("MeshCom") / path.relative_to(USER_CONFIG_DIR)
                    zf.write(path, arcname.as_posix())

        return True, str(destination)
    except Exception as exc:
        return False, str(exc)


def _validate_backup(zf: zipfile.ZipFile) -> tuple[bool, str]:
    names = zf.namelist()
    if "backup_info.json" not in names:
        return False, "Die Datei enthält keine gültige MeshCom-Guru-Datensicherung."

    try:
        info = json.loads(zf.read("backup_info.json").decode("utf-8"))
    except Exception:
        return False, "Die Backup-Informationen sind beschädigt."

    if info.get("format") != BACKUP_FORMAT:
        return False, "Das Backup stammt nicht aus MeshCom-Guru."

    settings_names = [n for n in names if n.rstrip("/") == "MeshCom/settings.ini"]
    if not settings_names:
        return False, "Im Backup wurde keine settings.ini gefunden."

    # Protect against path traversal when extracting a ZIP.
    for name in names:
        target = Path(name)
        if target.is_absolute() or ".." in target.parts:
            return False, "Das Backup enthält einen ungültigen Dateipfad."

    return True, ""


def restore_backup(source: str | os.PathLike) -> tuple[bool, str]:
    """Restore a MeshCom-Guru backup without deleting unrelated current files."""
    source = Path(source).expanduser()
    if not source.is_file():
        return False, "Die Backup-Datei wurde nicht gefunden."

    try:
        with zipfile.ZipFile(source, "r") as zf:
            valid, message = _validate_backup(zf)
            if not valid:
                return False, message

            with tempfile.TemporaryDirectory(prefix="meshcom_restore_") as tmp:
                tmp_path = Path(tmp)
                zf.extractall(tmp_path)

                restored_root = tmp_path / "MeshCom"
                restored_settings = restored_root / "settings.ini"
                if not restored_settings.is_file():
                    return False, "Die settings.ini im Backup konnte nicht gelesen werden."

                # Validate INI syntax before touching the current configuration.
                parser = configparser.ConfigParser()
                parser.read(restored_settings, encoding="utf-8")
                if "MeshCom" not in parser:
                    return False, "Die settings.ini im Backup ist ungültig."

                USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

                # Copy files into ~/.MeshCom. Existing unrelated files are kept.
                for path in restored_root.rglob("*"):
                    if not path.is_file():
                        continue
                    rel = path.relative_to(restored_root)
                    target = USER_CONFIG_DIR / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, target)

        return True, "Datensicherung erfolgreich wiederhergestellt."
    except zipfile.BadZipFile:
        return False, "Die ausgewählte Datei ist kein gültiges ZIP-Backup."
    except Exception as exc:
        return False, str(exc)

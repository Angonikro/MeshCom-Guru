from pathlib import Path
import configparser
import shutil

BASE_DIR = Path(__file__).resolve().parent.parent
# Persönliche Einstellungen liegen immer im Benutzerverzeichnis.
# Die Programmdateien unter /usr/share/MeshCom bleiben unverändert.
USER_CONFIG_DIR = Path.home() / ".MeshCom"
SETTINGS_FILE = USER_CONFIG_DIR / "settings.ini"


def load_settings():
    config = configparser.ConfigParser()
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_FILE.exists():
        template = BASE_DIR / "data" / "default_settings.ini"
        if template.exists():
            shutil.copyfile(template, SETTINGS_FILE)
    if SETTINGS_FILE.exists():
        config.read(SETTINGS_FILE, encoding="utf-8")
    if "MeshCom" not in config:
        config["MeshCom"] = {}
    section = config["MeshCom"]
    changed = False
    defaults = {
        "ip": "",
        "target": "",
        "filter_enabled": "0",
        "theme": "dark",
        "sound_enabled": "1",
        "sound_driver": "auto",
        "sound_volume": "70",
        "sound_file": "",
        "language": "de",
    }
    for key, value in defaults.items():
        if key not in section:
            section[key] = value
            changed = True
    if section.get("theme", "dark").lower() not in {"dark", "light"}:
        section["theme"] = "dark"
        changed = True
    for i in range(1, 6):
        key = f"filter_room{i}"
        if key not in section:
            section[key] = ""
            changed = True
    if changed or not SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            config.write(f)
    return section

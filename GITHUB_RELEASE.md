# MeshCom-Guru v0.3.90

## Änderungen in v0.3.90

- 💾 **Backup:** Persönliche MeshCom-Guru-Daten aus `~/.MeshCom` können als ZIP-Datei gesichert werden.
- ♻️ **Restore:** Sicherungen können wiederhergestellt und direkt in die laufende Anwendung übernommen werden.
- 🔒 **Restore-Schutz:** Beim Neustart nach dem Restore wird ein Überschreiben der restaurierten Daten durch den vorherigen In-Memory-Zustand verhindert.
- 🔄 **Update-Prüfung:** Die aktuelle GitHub-Release-Version kann geprüft werden; es erfolgt kein automatischer Download oder keine automatische Installation.
- 🌐 **Übersetzungen:** Die neuen Funktionen sind in Deutsch, English, Italiano, Nederlands und Français verfügbar.
- 🧩 **Stabilität:** Die bestehende Empfangs-, Chat-, Monitor-, Dashboard-, Karten- und Weltweit-Verarbeitung bleibt unverändert.

## Installation unter Linux / Raspberry Pi

Für die Weltweit-Ansicht wird WebKitGTK benötigt. Nach dem Entpacken einmal aus dem Projektordner ausführen:

```bash
chmod +x install_webkitgtk.sh
./install_webkitgtk.sh
```

Danach die Python-Abhängigkeiten aus `requirements.txt` installieren und MeshCom-Guru über `run_linux.sh` oder `python3 main.py` starten.

## Debian-Paket

Das Paket `MeshCom-Guru_v0.3.90_all.deb` installiert MeshCom-Guru unter `/usr/share/MeshCom`, legt den Startmenü-Eintrag einschließlich Icon an und verwendet Architektur `all`.


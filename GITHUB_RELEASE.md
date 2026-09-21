# MeshCom-Guru v0.3.92

## Änderungen in v0.3.92

- 📨 **„Alle“-Langzeit-Fix:** Empfangene Raum-Nachrichten bleiben auch nach mehreren Stunden in „Alle“ sichtbar.
- 📡 **Gezielter Fallback:** Der zusätzliche Empfangspfad ist auf „Alle“ begrenzt und greift nicht in Privat-Chats oder die normalen Raum-Tabs ein.
- 🧹 **„No messages available.“:** Die WebService-Statusmeldung wird weiterhin nicht als Chatnachricht übernommen oder gespeichert.
- 🛡️ **Stabilität:** Weltweit, Monitor, Karte und die bestehende Sendelogik bleiben unverändert.
## Installation

Das Debian-Paket `MeshCom-Guru_v0.3.92_all.deb` installiert MeshCom-Guru unter `/usr/share/MeshCom`, legt den Startmenü-Eintrag einschließlich Icon an und verwendet Architektur `all`.

## Installation unter Linux / Raspberry Pi

Für die Weltweit-Ansicht wird WebKitGTK benötigt. Nach dem Entpacken einmal aus dem Projektordner ausführen:

```bash
chmod +x install_webkitgtk.sh
./install_webkitgtk.sh
```

Danach die Python-Abhängigkeiten aus `requirements.txt` installieren und MeshCom-Guru über `run_linux.sh` oder `python3 main.py` starten.

## Debian-Paket

Das Paket `MeshCom-Guru_v0.3.92_all.deb` installiert MeshCom-Guru unter `/usr/share/MeshCom`, legt den Startmenü-Eintrag einschließlich Icon an und verwendet Architektur `all`.


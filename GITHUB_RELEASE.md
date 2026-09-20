# MeshCom-Guru v0.3.91

## Änderungen in v0.3.91

- 🧹 **„No messages available.“:** Die WebService-Statusmeldung wird nicht mehr als Chatnachricht übernommen, gespeichert oder dauerhaft am Ende des Chats angezeigt.
- 🌐 Die Statusmeldung wird auch in den vorhandenen Sprachvarianten erkannt.
- 🛠️ Die übrigen Empfangs-, Chat-, Monitor-, Dashboard-, Karten- und Weltweit-Funktionen bleiben unverändert.
## Installation

Das Debian-Paket `MeshCom-Guru_v0.3.91_all.deb` installiert MeshCom-Guru unter `/usr/share/MeshCom`, legt den Startmenü-Eintrag einschließlich Icon an und verwendet Architektur `all`.

## Installation unter Linux / Raspberry Pi

Für die Weltweit-Ansicht wird WebKitGTK benötigt. Nach dem Entpacken einmal aus dem Projektordner ausführen:

```bash
chmod +x install_webkitgtk.sh
./install_webkitgtk.sh
```

Danach die Python-Abhängigkeiten aus `requirements.txt` installieren und MeshCom-Guru über `run_linux.sh` oder `python3 main.py` starten.

## Debian-Paket

Das Paket `MeshCom-Guru_v0.3.91_all.deb` installiert MeshCom-Guru unter `/usr/share/MeshCom`, legt den Startmenü-Eintrag einschließlich Icon an und verwendet Architektur `all`.


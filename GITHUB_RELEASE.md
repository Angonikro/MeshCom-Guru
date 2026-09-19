# MeshCom-Guru v0.3.88

## Änderungen in v0.3.88

- 📡 **Rufzeichen-Menü:** Rufzeichen können im Dashboard und in der klassischen Ansicht über ein Kontextmenü weiterverarbeitet werden.
- 💬 **Privat Chat:** Direktes Öffnen eines privaten Chats für das ausgewählte Rufzeichen.
- 💬 **@Rufzeichen:** Das ausgewählte Rufzeichen kann direkt als Erwähnung in das Nachrichtenfeld übernommen werden.
- 🌐 **QRZ.com:** Direkter Aufruf des Rufzeichens im normalen Systembrowser.
- 🔎 **QRZ-Rufzeichen:** Bei Rufzeichen mit SSID wird für QRZ.com nur das Basis-Rufzeichen verwendet, z. B. `DO1ABC-12` → `DO1ABC`.
- 🧩 **Stabilität:** Die bestehende Empfangs-, Monitor- und Chat-Verarbeitung bleibt unverändert.

## Installation unter Linux / Raspberry Pi

Für die Weltweit-Ansicht wird WebKitGTK benötigt. Nach dem Entpacken einmal aus dem Projektordner ausführen:

```bash
chmod +x install_webkitgtk.sh
./install_webkitgtk.sh
```

Danach die Python-Abhängigkeiten aus `requirements.txt` installieren und MeshCom-Guru über `run_linux.sh` oder `python3 main.py` starten.

## Debian-Paket

Das Paket `MeshCom-Guru_v0.3.88_all.deb` installiert MeshCom-Guru unter `/usr/share/MeshCom`, legt den Startmenü-Eintrag einschließlich Icon an und verwendet Architektur `all`.

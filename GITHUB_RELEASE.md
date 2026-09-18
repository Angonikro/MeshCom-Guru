# GitHub Release v0.3.87

## Änderungen

- 📻 „Räume“ im Dashboard vollständig sichtbar.
- ➕ „Raum hinzufügen“ auf 155 px eingestellt.
- 🧩 Übriges Dashboard-Layout unverändert.

# MeshCom-Guru v0.3.86

## Änderungen in v0.3.86
- 📡 MH-Liste auf maximal **250 zuletzt gehörte Stationen** erweitert.
- 🧹 Beim 251. Eintrag wird automatisch die älteste Station entfernt.
- 🖥️ Klassische Ansicht und 📊 Dashboard verwenden dieselbe Begrenzung von 250 Stationen.
- 🔄 Sortierung nach dem tatsächlichen letzten Empfangszeitpunkt.
- 📡 **Dashboard-Monitor:** Pause, Leeren, Filter, Suche und Auto-Scroll direkt über dem Monitor.
- 🧹 **Dashboard-MH:** Leeren-Button für die MH-Liste.
- 📊 **Dashboard-Statistik:** Werte übersichtlich untereinander.
- 📡 **Telemetrie:** Empfangene Telemetrie-Datensätze werden in der Statistik mitgezählt.
- 🧩 **Layout unverändert:** Keine Änderung der bestehenden Panel-Größen oder Positionen.

## Änderungen in v0.3.85
- 🖥️ Dashboard-Layout nach dem festgelegten Referenzlayout angepasst.
- 💬 Chatbereich breiter dargestellt.
- 🗺️ Karte und 🌐 Weltweit entsprechend kompakter angeordnet.
- 📻 **Räume** und **+ Raum hinzufügen** direkt nebeneinander.
- 🔘 Raum-Buttons bleiben in Größe und Anordnung unverändert.
- 🖱️ Die funktionierende GTK-Capture-Mausradlösung für Weltweit bleibt erhalten.
- 🌐 WebKitGTK für Weltweit bleibt erhalten.

## Installation unter Linux / Raspberry Pi

Für die Weltweit-Ansicht wird WebKitGTK benötigt. Nach dem Entpacken einmal aus dem Projektordner ausführen:

```bash
chmod +x install_webkitgtk.sh
./install_webkitgtk.sh
```

Danach die Python-Abhängigkeiten aus `requirements.txt` installieren und MeshCom-Guru über `run_linux.sh` oder `python3 main.py` starten.

## Debian-Paket

Das Paket `MeshCom-Guru_v0.3.86_all.deb` installiert MeshCom-Guru unter `/usr/share/MeshCom`, legt den Startmenü-Eintrag einschließlich Icon an und verwendet Architektur `all`.

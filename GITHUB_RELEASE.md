# MeshCom-Guru v0.3.89

## Änderungen in v0.3.89

- 📡 **Via-/Privatnachrichten:** Die vollständige Zielangabe rechts vom `>` wird jetzt vor der Privatnachrichten-Erkennung geprüft.
- 💬 **Privat-Chat:** Via-/Raum-Header wie `OE5HWN-12,DO2GG-1 > OE5XLM-12,232` werden nicht mehr fälschlich als reine Privatnachrichten behandelt.
- 🧭 **Zielauswertung:** Eine Raumangabe hinter dem Ziel-Rufzeichen verhindert die falsche Zuordnung zu einem Privat-Chat.
- 🧩 **Stabilität:** Die bestehende Empfangs-, Monitor-, Raum-, Dashboard-, Karten- und Weltweit-Verarbeitung bleibt unverändert.

## Installation unter Linux / Raspberry Pi

Für die Weltweit-Ansicht wird WebKitGTK benötigt. Nach dem Entpacken einmal aus dem Projektordner ausführen:

```bash
chmod +x install_webkitgtk.sh
./install_webkitgtk.sh
```

Danach die Python-Abhängigkeiten aus `requirements.txt` installieren und MeshCom-Guru über `run_linux.sh` oder `python3 main.py` starten.

## Debian-Paket

Das Paket `MeshCom-Guru_v0.3.89_all.deb` installiert MeshCom-Guru unter `/usr/share/MeshCom`, legt den Startmenü-Eintrag einschließlich Icon an und verwendet Architektur `all`.


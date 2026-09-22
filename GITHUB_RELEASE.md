# MeshCom-Guru v0.3.93

## Änderungen in v0.3.93

- 🇪🇸 Spanische Benutzeroberfläche einschließlich integrierter Anleitung.
- 🇸🇪 Schwedische Benutzeroberfläche einschließlich integrierter Anleitung.
- 📖 Anleitung folgt zuverlässig der ausgewählten Sprache.
- 📡 Monitor-Zähler und dynamische Anzeigen werden beim Sprachwechsel korrekt übersetzt.
- 🗺️ Karten-Tab und 🌐 Weltweit-Tab werden beim Sprachwechsel zuverlässig aktualisiert.
- 🛰️ GPS- und Raum/Ziel-Beschriftungen sind in allen sieben Sprachen berücksichtigt.
- 🧩 Keine Änderungen an der bestehenden Nachrichten-, Empfangs-, „Alle“- und Sendelogik.

## Debian-Paket

Das Debian-Paket `MeshCom-Guru_v0.3.93_all.deb` installiert MeshCom-Guru unter `/usr/share/MeshCom`, legt den Startmenü-Eintrag einschließlich Icon an und verwendet Architektur `all`.

Für die Weltweit-Ansicht wird unter Linux/Raspberry Pi WebKitGTK benötigt. Nach dem Entpacken einmal aus dem Projektordner ausführen:

```bash
chmod +x install_webkitgtk.sh
./install_webkitgtk.sh
```

## GitHub-ZIP

Das ZIP `MeshCom-Guru_v0.3.93_GITHUB.zip` enthält den vollständigen Projektstand. Beim Entpacken entsteht direkt der Ordner `MeshCom/`.

Die integrierte Anleitung ist mehrsprachig und folgt der in MeshCom-Guru ausgewählten Sprache.

# MeshCom-Guru v0.4.1 – Vollständiger Mitternachts-Sortierfix

## Neuer Fix

- 🕛 Gespeicherte Chat-Nachrichten und der Chat-Export sortieren bei vorhandenen vollständigen Zeitstempeln jetzt nach Datum **und** Uhrzeit.
- 🌙 Der Übergang über **00:00 Uhr** ist damit auch in diesen Nebenpfaden chronologisch korrekt.
- 🛡️ Der funktionierende Live-„Alle“-Datenpfad aus v0.4.0 wurde nicht verändert.
- 🧩 Alte Karten ohne vollständiges Datum verwenden weiterhin die reine Uhrzeit als Fallback.

## Bestehende Funktionen bleiben erhalten

- 💬 Raum- und Private-Chats mit korrekter Bottom-Anker-Ausrichtung.
- ⚡ Performance-Optimierungen aus v0.3.99.
- 🕛 Mitternachts-Fix aus v0.3.98, jetzt auf die verbleibenden Sortierpfade erweitert.
- 📊 Monitor und Stations/MH.
- 🗺️ Karte und 🌐 Weltweit.
- 🌦️ Wetter-/Telemetrie-Funktionen.
- 🖼️ Picrd-Bildvorschau und anklickbare Internetlinks.
- 🇩🇪 🇬🇧 🇮🇹 🇳🇱 🇫🇷 🇪🇸 🇸🇪 🇵🇱 Mehrsprachige Oberfläche.
- 🧹 Release ohne `__pycache__`-Ordner und `.pyc`-Dateien.

## GitHub-ZIP

Beim Entpacken entsteht direkt der Ordner `MeshCom/`.

**Version:** 0.4.1  
**Status:** Release

## Debian-Paket

Das Debian-Paket verwendet die Architektur `all` und installiert MeshCom-Guru unter `/usr/share/MeshCom-Guru`.

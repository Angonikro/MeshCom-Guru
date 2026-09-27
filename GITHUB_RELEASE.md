# MeshCom-Guru v0.4.0 – Raum-Chat Bottom-Anchor Fix

## Raum-Chat Fix

- 💬 Beim Wechsel zwischen gespeicherten Räumen werden die Nachrichten wieder zuverlässig an der unteren Kante des Chatbereichs ausgerichtet.
- 🔄 Der problematische Wechsel **Raum 20 → Raum 262 → Raum 20** benötigt keinen zweiten Klick mehr, damit die letzte Nachricht unten steht.
- 🛠️ Die Ursache wurde im Chat-Layout behoben: Der freie Layout-Bereich liegt jetzt oberhalb der Nachrichten statt darunter.
- 🧪 Die Änderung wurde bewusst klein gehalten und baut direkt auf **v0.3.99** auf.

## Bestehende v0.3.99-Funktionen bleiben erhalten

- ⚡ Performance-Optimierungen für Karte, „Alle“ und Statistik.
- 🕛 Mitternachts-Fix aus v0.3.98.
- 💬 Räume und Private Chats.
- 📊 Monitor und Stations/MH.
- 🗺️ Karte und 🌐 Weltweit.
- 🌦️ Wetter-/Telemetrie-Funktionen.
- 🖼️ Picrd-Bildvorschau und anklickbare Internetlinks.
- 🇩🇪 🇬🇧 🇮🇹 🇳🇱 🇫🇷 🇪🇸 🇸🇪 🇵🇱 Mehrsprachige Oberfläche.
- 🧹 Release ohne `__pycache__`-Ordner und `.pyc`-Dateien.

## GitHub-ZIP

Beim Entpacken entsteht direkt der Ordner `MeshCom/`.

**Version:** 0.4.0  
**Status:** Test-/Release-Kandidat – nach positivem Praxistest für GitHub bereit.

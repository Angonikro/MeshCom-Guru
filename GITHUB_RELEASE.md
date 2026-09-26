# MeshCom-Guru v0.3.98 – FINAL

## Stabilitäts- und Mitternachts-Fix

- 🕛 Die zeitliche Verarbeitung bleibt auch beim Übergang über **00:00 Uhr** korrekt.
- 🧪 Der finale Stand wurde **12 Stunden im Dauerbetrieb** getestet, ohne dass der zuvor beobachtete Fehler erneut auftrat.
- 🛡️ Die bestehende Monitor-/UDP-Verarbeitung bleibt unverändert getrennt von der Darstellung in „Alle“.

## „Alle“ – eigener Live-Datenbereich

- 🔄 „Alle“ wird beim Tab-Wechsel ausschließlich aus dem eigenen `monitor_all_rows`-Live-Puffer aufgebaut.
- 🚫 Beim Wechsel Raum → „Alle“ wird kein alter WebService-/Nachrichten-Cache als Zwischenstand angezeigt.
- ⚡ MSG/POS/TEL/ACK-Daten werden direkt in den „Alle“-Puffer übernommen.
- 🌡️ Wetter-/TEL-Daten müssen beim Wechsel zu „Alle“ nicht auf einen zusätzlichen Refresh warten.
- 📤 Eigene gesendete Nachrichten werden ebenfalls direkt in „Alle“ übernommen.

## Weitere Funktionen des finalen v0.3.98-Stands

- 🇵🇱 Polnische Benutzeroberfläche und integrierte Anleitung.
- 🖼️ Picrd-Bildvorschau mit anklickbarem Original-Link.
- 🔗 Normale Internetlinks bleiben anklickbar.
- 🗺️ Karten-Verbindungen aus tatsächlich empfangenen MeshCom-Pfaden.
- 🌐 Mehrsprachige Benutzeroberfläche.
- 🧹 Keine `__pycache__`-Ordner oder `.pyc`-Dateien im Release.

## GitHub-ZIP

Beim Entpacken entsteht direkt der Ordner `MeshCom/`.

**Version:** 0.3.98  
**Status:** Final

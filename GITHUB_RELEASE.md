# MeshCom-Guru v0.3.61

## Release v0.3.61

Diese Version vereinheitlicht die Chat-Darstellung der normalen Raum-Tabs mit dem bereits funktionierenden Privat-Chat.

### Änderungen
- Normale Raum-Tabs verwenden jetzt dieselbe Bubble-Anordnung wie der Privat-Chat.
- Eigene Nachrichten werden rechts in **Grün** dargestellt.
- Empfangene Nachrichten werden links in **Blau** dargestellt.
- Kompakte `CALLSIGN>RAUM`-Antworten des MeshCom-WebService werden korrekt zerlegt.
- Absender, Zielraum und Nachricht werden sauber getrennt angezeigt.
- Der Tab **„Alle“ bleibt unverändert** und verwendet ausdrücklich nicht die neue Raum-Bubble-Darstellung.
- Bestehende Funktionen wie Privat-Chats, Karte, Monitor, MH, Wetter, Filter und Node-Info bleiben erhalten.

### Projektarchiv

- `MeshCom-Guru_v0.3.61_GITHUB.zip`
- Der oberste Projektordner im Archiv ist exakt `MeshCom/`.
- Persönliche Einstellungen werden nicht im Projekt gespeichert, sondern unter `~/.MeshCom/settings.ini` angelegt.
- `data/default_settings.ini` enthält nur neutrale Standardwerte.

### Start

**Linux:**

```bash
chmod +x run_linux.sh
./run_linux.sh
```

**Windows:** `run_windows.bat` starten.

### Hinweis für GitHub

Dieses ZIP ist das vollständige Projektarchiv für den GitHub-Release. Die Release-Beschreibung kann direkt aus diesem Dokument übernommen werden.

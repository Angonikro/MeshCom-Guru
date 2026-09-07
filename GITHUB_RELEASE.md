# GitHub-Release – MeshCom-Guru v0.3.55

## Release-Titel
MeshCom-Guru v0.3.55

## Tag
v0.3.55

## Release-Asset
`MeshCom-Guru_v0.3.55_GITHUB.zip`

## Release-Hinweise

MeshCom-Guru v0.3.55 baut auf dem stabilen v0.3.54-Stand auf und ergänzt die Begrenzung der Nachrichtenlänge auf **149 Zeichen**.

### Neu in v0.3.55
- Nachrichtenfeld auf maximal 149 Zeichen begrenzt.
- Live-Zeichenzähler direkt rechts im Nachrichtenfeld (`0/149` bis `149/149`).
- Zusätzliche Prüfung beim Senden gegen Nachrichten mit mehr als 149 Zeichen.
- Internetlinks (`http://` und `https://`) im Chat sind anklickbar und öffnen den Standard-Webbrowser.

### Erhaltener stabiler Funktionsumfang
- Normale Raum-Chats funktionieren.
- Private Nachrichten funktionieren.
- Der Tab **Alle** zeigt Nachrichten nur einmal und chronologisch korrekt.
- Eigene Nachrichten werden nicht doppelt angezeigt.
- Koordinaten werden verarbeitet und auf der Karte als Marker angezeigt.
- Node-Informationen und Kartenanzeige bleiben erhalten.
- Linux- und Windows-Startdateien sowie Desktop-Launcher sind enthalten.

## Windows-Abhängigkeiten
Unter Windows wird Python 3.10 bis 3.14 unterstützt. Die benötigte Qt-WebEngine-Unterstützung wird über `PySide6-Addons[webengine]` installiert. Das veraltete Paket `PySide6-WebEngine` wird nicht mehr verwendet.

## Wichtig
Dieses Paket enthält den vollständigen Projektordner `MeshCom/`, README, CHANGELOG, VERSION, `version.py`, Linux-/Windows-Startdateien, Desktop-Launcher, integrierte Hilfe/Info, PDF-Anleitung und die benötigten Projektdateien.

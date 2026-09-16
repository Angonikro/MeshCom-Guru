## Korrekturen in v0.3.78

- Beim Wechsel zwischen Dashboard und Klassisch wird das aktuell ausgewählte Ziel korrekt in der `settings.ini` übernommen.
- Beim Senden in der klassischen Ansicht wird das tatsächlich ausgewählte Chat-Ziel verwendet; `filter_room`-Werte werden nicht mehr versehentlich als Sendeziel verwendet.

# MeshCom-Guru v0.3.78

## Neues Dashboard-Design

v0.3.78 ergänzt zur bisherigen klassischen Oberfläche ein neues Dashboard. Unter **Einstellungen → Darstellung** kann zwischen **Klassisch** und **Dashboard** gewechselt werden.

### Dashboard
- Gespeicherte Räume direkt als anklickbare Raum-Chats
- Eigene Ansicht **Alle**
- Getrennte **Private Chats**
- Karte und **Weltweit** direkt im Dashboard
- Live-**Monitor**, **Stations / MH** und **Statistik**
- Nachrichtenversand mit **Enter** statt zusätzlichem Senden-Button
- Wetter, Node Info, Verbindung und Onlinezeit weiterhin verfügbar

### Dokumentation
- Integrierte **Hilfe → Anleitung** auf v0.3.78 aktualisiert
- Anleitung in Deutsch, English, Italiano, Nederlands und Français
- PDF-Anleitungen für alle fünf Sprachen enthalten
- README und CHANGELOG aktualisiert

### Hinweis
Die Weltweit-Webseite übernimmt weiterhin ihre eigene Aktualisierung. MeshCom-Guru verwendet keinen zusätzlichen 15-Sekunden-Refresh.

### Stabilität von Weltweit

Die eingebettete Weltweit-Webseite besitzt einen kleinen Selbstheilungs-Watchdog. Bei einem unerwarteten Renderer-Abbruch oder einem länger anhaltenden Hänger wird die Ansicht automatisch neu geladen und **ACTIVITY** wieder ausgewählt. Es gibt weiterhin keinen zusätzlichen 15-Sekunden-Refresh.

## Installation

ZIP entpacken und den enthaltenen Ordner **MeshCom** verwenden. Unter Linux kann `./run_linux.sh` verwendet werden; unter Windows steht `run_windows.bat` zur Verfügung.

# GitHub-Release – MeshCom-Guru v0.3.56

## Release-Titel
MeshCom-Guru v0.3.56

## Tag
v0.3.56

## Release-Asset
`MeshCom-Guru_v0.3.56_GITHUB.zip`

## Neu in v0.3.56

- Wetterdaten-Testfunktion unter **Einstellungen → Wetterdaten**.
- WX-Information direkt über den MeshCom-WebService `/?page=wx`.
- Temperatur, Luftfeuchte, QFE und QNH werden aus der WX-Tabelle übernommen.
- Automatischer Wetterabruf nach jedem Start, wenn Wetterdaten aktiviert sind.
- Stadtname + Wetterwerte können **ohne Raumangabe** gesendet werden.
- Unterstützung für MeshCom-Nodes mit erkanntem **BME280/BMP280**-Wettermodul.
- Überarbeitete Node-Info-Seitenleiste.
- Größere OSM-/Leaflet-Kartenansicht.
- 149-Zeichen-Limit mit Live-Zähler bleibt erhalten.

## Erhaltener Funktionsumfang

- Normale Raum-Chats.
- Private Nachrichten.
- Tab **Alle** ohne Doppelanzeigen und chronologisch korrekt.
- Eigene Nachrichten ohne unerwünschte Doppelanzeige.
- Koordinaten und Kartenmarker.
- Node-Information.
- Linux- und Windows-Startdateien.
- Desktop-Launcher und Icon.

## Windows

Python 3.10 bis 3.14 wird unterstützt. Qt WebEngine wird über `PySide6-Addons[webengine]` bereitgestellt. Das alte Paket `PySide6-WebEngine` wird nicht verwendet.

## Debian

Das Debian-Paket installiert den vollständigen Programmstand nach:

`/usr/share/MeshCom`

Es verwendet keine eigene `.venv`, kein `pip` während der Installation und kein `postinst` zur Python-Paketinstallation. Der Menüeintrag und das Icon werden direkt mitgeliefert.

## Paketstruktur

Das GitHub-ZIP enthält beim Entpacken als obersten Projektordner exakt:

`MeshCom/`

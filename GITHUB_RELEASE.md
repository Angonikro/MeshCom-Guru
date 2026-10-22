# MeshCom-Guru v0.5.9

## Änderungen in v0.5.9

- **Bildanbieter vor Dateiauswahl:** Beim Klick auf die Büroklammer zuerst `imgdb.io` oder `picrd.com` auswählen; anschließend die Bilddatei auswählen.
- **imgdb.io integriert:** Verwendet `https://imgdb.io/api/v1/upload` mit dem Formularfeld `file`.
- **Speicherdauer-Option:** Zuerst wird `ttl=0` übermittelt. Bei fehlgeschlagenem Versuch erfolgt genau ein erneuter Upload ohne TTL-Parameter. Eine dauerhafte Speicherung kann der Anbieter nicht garantiert werden.
- **Upload-Limit:** In Guru sind für imgdb.io maximal 16 MiB pro Bild vorgesehen.
- **Privatpfad-Fix beibehalten:** Der funktionierende Stand aus v0.5.8 bleibt die Grundlage; ACK/Echo, Räume, Monitor, Karte und Weltweit wurden nicht absichtlich umgebaut.

## Testhinweise

- Externer API-Test für imgdb.io erfolgreich: Upload mit HTTP 201.
- Abruf der zurückgegebenen Bild-URL erfolgreich: HTTP 200 und `image/jpeg`.
- Der direkte picrd-Upload lieferte zum Zeitpunkt der Tests HTTP 500, auch außerhalb von MeshCom-Guru. Das ist eine Momentaufnahme und keine Aussage über den aktuellen Dienststatus.
- Diese Tests bestätigen nicht automatisch jeden Upload über die installierte Anwendung. Bitte den Ablauf in Guru mit einer unkritischen Testdatei prüfen.

## Release-Dateien

- Version: `0.5.9`
- GitHub-Archiv: `MeshCom-Guru_v0.5.9_GITHUB.zip`
- Debian-Architektur des separaten Pakets: `all`

## Hinweise

- Die acht PDF-Handbücher bleiben auf dem bisherigen Dokumentationsstand v0.5.2.
- Das ZIP enthält den Projektordner `MeshCom/` als obersten Ordner und keine Python-Cache-Dateien.

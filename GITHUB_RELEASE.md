# MeshCom-Guru v0.3.80

## Weltweit mit WebKitGTK

v0.3.80 bettet die echte ÖVSV-MeshCom-Seite im Weltweit-Bereich über **WebKitGTK** ein. Der Weltweit-Bereich verwendet damit keinen eigenen QtWebEngine-/Chromium-Renderer mehr.

- ACTIVITY wird beim Laden weiterhin automatisch geöffnet.
- Die OSM-/Leaflet-Karte bleibt als vorhandene QtWebEngine-Ansicht erhalten.
- Die Startgröße des Weltweit-Bereichs wurde korrigiert, sodass die Seite sofort sichtbar ist und nicht erst über den Splitter vergrößert werden muss.
- `install_webkitgtk.sh` installiert die benötigten WebKitGTK-/GTK-Pakete unter Debian/Raspberry Pi.
- Übersetzungen für Deutsch, English, Italiano, Nederlands und Français wurden aktualisiert.
- Die Temperaturbezeichnung wurde korrigiert; der zusätzliche Buchstabe wurde entfernt.
- Die Wetteranzeige wird beim Sprachwechsel aus den Rohdaten neu aufgebaut, damit Temperatur, Luftfeuchte, QFE und QNH nicht durch mehrfaches Übersetzen beschädigt werden.

## Dokumentation

- Version auf **0.3.80** aktualisiert.
- CHANGELOG und README ergänzt.
- Die vorhandenen Funktionen und die fünf unterstützten Sprachen bleiben erhalten.

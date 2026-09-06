# Changelog

## v0.3.54
- Neu GUI Oberfläche
- Tab **Alle** wird aus dem aktuellen WebService-Nachrichtenstrom aufgebaut.
- Jede Nachricht wird dort nur einmal übernommen; Raum- und Privat-Tabs bleiben unverändert.
- Die lokale Sofortkopie eigener Sendungen wurde entfernt, damit normale und private eigene Nachrichten nicht doppelt unter **Alle** erscheinen.
- Nachrichten unter **Alle** werden anhand ihres WebService-Zeitstempels chronologisch sortiert.
- Karten-/Koordinatenlogik wurde für diesen Fix nicht verändert.

## v0.3.53
- Neues Menü **Hilfe** in der Menüleiste.
- **Hilfe → Anleitung** mit integrierter Kurzanleitung.
- **Hilfe → Info** mit MeshCom-Guru, Version und „By Goldisoft 2026“.
- Die bestehende Chat-, Karten-, UDP- und Node-Info-Funktion bleibt unverändert.

v0.3.52

- Hilfe-Menü mit integrierter Anleitung ergänzt.
- Info-Fenster mit Programmname, Version und „By Goldisoft 2026“ ergänzt.
- README um vollständige Linux-/Windows-Installation und Desktop-Launcher-Anleitung erweitert.
- PDF-Anleitung gepflegt.

- Neues Menü **Hilfe** mit integrierter Anleitung.
- Neuer Punkt **Info** mit Programmname, Version und „By Goldisoft 2026“.
- Bestehende Chat-, Karten-, Raum- und Privatfunktionen unverändert.

# Changelog

## v0.3.51 – Kartenmarker auf ursprüngliches Design zurückgestellt

- Das bisherige, schönere Leaflet-Marker-Design wurde wiederhergestellt.
- Die Koordinaten-/UDP-Verarbeitung aus v0.3.50 bleibt unverändert.
- Die eigenständige Arbeitsweise ohne MeshDash bleibt erhalten.


## v0.3.50 – Kartenmarker für direkte UDP-Positionen stabilisiert

- Leaflet-Marker auf robuste `circleMarker` umgestellt; dadurch keine Abhängigkeit von externen Marker-Icon-Dateien bei `setHtml()` mehr.
- Kartenansicht erhält eine feste Basis-URL und ruft nach Updates `invalidateSize()` auf.
- UDP-Positionen akzeptieren zusätzlich `latitude`/`longitude` sowie `position`/`gps`.
- Empfangene UDP-Pakete werden lokal in `data/udp_received.log` protokolliert, damit der direkte Empfang unabhängig von MeshDash geprüft werden kann.


## v0.3.49 – Eigenständiger UDP-Positions-Empfang

- MeshDash-/5d-Abhängigkeit für Karten- und Positionsdaten entfernt.
- MeshCom-Guru startet seinen eigenen UDP-Empfänger auf Port 1799.
- Positionspakete werden direkt aus `lat`, `long`, `lat_dir` und `long_dir` verarbeitet.
- Empfangene Stationen werden unmittelbar auf der eingebauten Leaflet-Karte aktualisiert.
- Chat und Privatnachrichten bleiben über den konfigurierten MeshCom-WebService erhalten.
- Einstellung für eine separate MeshDash-/5d-Nachrichtenquelle entfernt.
- README und PDF-Anleitung auf den eigenständigen Betrieb aktualisiert.

## v0.3.48
- Tab „Alle“ zeigt jetzt den vollständigen Nachrichtenstrom unabhängig vom aktivierten Raumfilter.
- Eingehende Privatnachrichten erscheinen dadurch auch unter „Alle“.
- Eigene gesendete Nachrichten werden unter „Alle“ nicht mehr durch den Raumfilter ausgeblendet.

- Kartenmarker erneut repariert: Die Nachrichtenquelle kann unabhängig von der Hotspot-IP eingestellt werden.
- Positionsdaten werden zusätzlich direkt aus der vollständigen MeshDash-/5d-Seite extrahiert.
- Damit werden GPS-Positionen auch erkannt, wenn die Nachrichten-Webseite auf einem anderen WebService als der Hotspot liegt.
- Hotspot-IP bleibt für Senden und Node Info zuständig.
- README und PDF-Anleitung aktualisiert.

## v0.3.47
- Kartenmarker repariert: Positionsdaten werden gepuffert, bis die Leaflet/QWebEngine-Karte vollständig geladen ist.
- Die Karte wird beim Aktualisieren nicht neu geladen; Zoom und Ansicht bleiben erhalten.
- Chat, Privatnachrichten und Node Info bleiben unverändert.

## v0.3.46
- Karten-/Koordinatenpfad gezielt untersucht und Adapter ergänzt.
- Bestehenden Chat, Privat-Chat und Node-Info-Abruf nicht ersetzt.

## v0.3.45
- Kartenanbindung auf die bereits vorhandenen Node-Info-Koordinaten vorbereitet.
- Keine Änderung am Chat, Privat-Chat oder Node-Info-Abruf.

## v0.3.44
- Koordinaten zusätzlich über den MeshCom-Dashboard-Endpunkt /5d/message.php?group=-1 eingelesen.
- Bestehenden Chat-, Privatnachrichten- und Node-Info-Pfad nicht verändert.

## v0.3.43
- Koordinaten-Erkennung und Übergabe an die vorhandene Kartenfunktion verbessert.
- Chat, Privatnachrichten und Node Info bewusst unverändert gelassen.

# Changelog

## v0.3.50 – Kartenmarker für direkte UDP-Positionen stabilisiert

- Leaflet-Marker auf robuste `circleMarker` umgestellt; dadurch keine Abhängigkeit von externen Marker-Icon-Dateien bei `setHtml()` mehr.
- Kartenansicht erhält eine feste Basis-URL und ruft nach Updates `invalidateSize()` auf.
- UDP-Positionen akzeptieren zusätzlich `latitude`/`longitude` sowie `position`/`gps`.
- Empfangene UDP-Pakete werden lokal in `data/udp_received.log` protokolliert, damit der direkte Empfang unabhängig von MeshDash geprüft werden kann.


## v0.3.41 – Koordinatenempfang repariert

- Positionsdaten aus MeshCom-Statuskarten werden jetzt robust aus den beschrifteten Koordinatenzeilen gelesen.
- N/S wird zuverlässig als Breitengrad und E/W als Längengrad behandelt, auch wenn die Weboberfläche die Bezeichnungen vertauscht.
- Unabhängig vom funktionierenden Privatnachrichten-Fix bleiben Chat und Node-Info unverändert.

# CHANGELOG

## v0.3.40 – Privatnachrichten zuverlässig anzeigen

- Privatnachrichten werden zusätzlich direkt anhand des CALL1 > CALL2-Headers erkannt.
- Privatnachrichten aus abweichenden HTML-Containern werden nicht mehr nur durch einen roten Tab signalisiert, sondern auch als Nachricht in den Privat-Chat übernommen.
- Karte, Node Info, Nachrichtenempfang, Sound und Desktop-Launcher der bestehenden Basis bleiben unverändert.


## v0.3.39 – Vollständige Oberfläche wiederhergestellt

- vollständige Kartenansicht wieder integriert
- Node-Info-Funktion wieder integriert
- Positionsdaten werden aus dem Nachrichtenstrom übernommen
- eigene GPS-Daten werden nur angezeigt, wenn tatsächlich Koordinaten hinterlegt sind
- Kartenmarker gehören nur zur aktuellen Programmsitzung
- funktionierenden Nachrichtenempfang aus der bewährten Basis beibehalten
- Empfang verwendet primär `/5d/message.php?group=-1`
- Cache-Busting und HTTP-No-Cache gegen veraltete Nachrichten ergänzt
- Raum- und Privatnachrichten bleiben in ihren Tabs verfügbar
- Windows-Sound über `winsound` bleibt enthalten
- `PySide6-WebEngine` in `requirements.txt` ergänzt
- README und PDF-Anleitung aktualisiert
- Desktop-Launcher und Programmsymbol beibehalten

## v0.3.38

- Verbesserungen am Empfang und an Privatnachrichten.

## v0.3.37

- weitere Korrekturen für Live-Empfang.

## v0.3.36

- Live-Empfang und Nachrichtenverarbeitung überarbeitet.

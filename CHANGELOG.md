# CHANGELOG

## v0.3.58 – Wetterraum, Raumfilter und Entfernungsanzeige

- **Wetter senden:** Wetterdaten werden jetzt in dem Raum gesendet, in dem man sich aktuell befindet.
- **Raumfilter:** Fehler bei der Filterung der Räume behoben; der Raumfilter funktioniert jetzt korrekt.
- **Kartenmarker:** Bei den Markern der anderen Stationen wird jetzt die Entfernung zur eigenen Station angezeigt. Die Entfernung wird aus den eigenen GPS-Koordinaten und den Koordinaten der jeweiligen Station berechnet.

## v0.3.57 – Nachrichtenstabilität und saubere Benutzereinstellungen

- Nachrichten bleiben während der laufenden Sitzung erhalten, auch wenn sie später nicht mehr vom WebService geliefert werden.
- Nachrichten werden chronologisch dargestellt und nicht unnötig doppelt übernommen.
- Der Tab „Alle“ unterdrückt doppelt gelieferte Alle-Nachrichten anhand des normalisierten Rufzeichens und Nachrichtentextes.
- Unterschiedliche HTML-/Icon-Darstellungen eines Rufzeichens werden für die Dublettenprüfung normalisiert.
- Nachrichten aus normalen Räumen werden nicht von der speziellen Alle-Dublettenprüfung erfasst.
- Nach einem Neustart beginnen alle Raum-Tabs mit einem leeren lokalen Nachrichtenbestand.
- Persönliche Einstellungen werden unter `~/.MeshCom/settings.ini` gespeichert.
- Beim ersten Start werden nur neutrale Standardwerte erzeugt; persönliche Rufzeichen, Hotspot-IP und Räume werden nicht fest in den Programmcode eingebaut.
- Bestehende Node-Info-, Wetter-, Karten- und Privatnachrichten-Funktionen bleiben erhalten.

## v0.3.56 – Wetterdaten, Kartenansicht und Release

- Wetterdaten-Testfunktion unter **Einstellungen → Wetterdaten** fertig in den Release-Stand übernommen.
- WX-Daten werden direkt über den MeshCom-WebService `/?page=wx` gelesen.
- Unterstützt **Temperatur, Luftfeuchte, QFE und QNH** aus der WX-Information.
- Bei aktivierter Wetterfunktion werden die Wetterdaten nach jedem Programmstart automatisch neu geladen.
- Stadtname kann eingegeben und zusammen mit den Wetterdaten **ohne Raumangabe** gesendet werden.
- Geeignet für MeshCom-Nodes mit erkanntem **BME280/BMP280**-Wettermodul.
- Node-Info-Seitenleiste im verbesserten Design übernommen.
- OSM-/Leaflet-Kartenansicht deutlich vergrößert.
- Projektversion auf **0.3.56** aktualisiert.
- README, Release-Hinweise, Anleitung und Windows-Startdatei auf v0.3.56 aktualisiert.
- Vollständiges GitHub-Paket mit dem Projektordner **MeshCom/**.
- Debian-Paket für Installation unter **/usr/share/MeshCom** vorbereitet.

## v0.3.55

- 149-Zeichen-Begrenzung und Live-Zeichenzähler.
- Anklickbare Internetlinks im Chat.
- Node-Info-Seitenleiste als Design-Test.
- Wetterdaten-Testfunktion über MeshCom-WebService.

## v0.3.54

- Tab **Alle** wird aus dem aktuellen WebService-Nachrichtenstrom aufgebaut.
- Jede Nachricht wird dort nur einmal übernommen; Raum- und Privat-Tabs bleiben unverändert.
- Eigene Sendungen werden nicht doppelt unter **Alle** angezeigt.
- Nachrichten unter **Alle** werden anhand ihres WebService-Zeitstempels chronologisch sortiert.
- Karten-/Koordinatenlogik wurde für diesen Fix nicht verändert.

## v0.3.53

- Neues Menü **Hilfe**.
- **Hilfe → Anleitung** mit integrierter Kurzanleitung.
- **Hilfe → Info** mit MeshCom-Guru, Version und „By Goldisoft 2026“.

## v0.3.52

- Hilfe-Menü mit integrierter Anleitung.
- Info-Fenster mit Programmname, Version und „By Goldisoft 2026“.
- README um Linux-/Windows-Installation und Desktop-Launcher ergänzt.

# Changelog

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

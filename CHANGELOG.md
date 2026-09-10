# CHANGELOG

## v0.3.61 – Einheitliche Chat-Bubbles für Raum-Tabs

- **Raum-Tabs:** Die funktionierende Bubble-Anordnung und Farbgebung des Privat-Chats wird jetzt auch für alle normalen Raum-Tabs verwendet.
- **Eigene Raum-Nachrichten:** Eigene Nachrichten werden in normalen Räumen wieder zuverlässig erkannt und wie im Privat-Chat rechts in **Grün** dargestellt.
- **Empfangene Raum-Nachrichten:** Fremde Nachrichten bleiben links in **Blau**.
- **Raum-Header:** Kompakte `CALLSIGN>RAUM`-Antworten des MeshCom-WebService werden korrekt in Absender, Zielraum und Nachricht zerlegt.
- **Tab „Alle“:** Unverändert; die neue Bubble-Darstellung wird ausdrücklich **nicht** auf „Alle“ angewendet.
- **Bestehende Funktionen:** Nachrichtenlogik, Filter, Privat-Chats, Karte, Monitor, MH und Wetter bleiben unangetastet.

## v0.3.60 – Schnelltexte, Sendebestätigung, Monitor, MH und Chat-Bubbles

- **Schnelltexte:** Neuer Schnelltexte-Button neben dem Nachrichtenfeld.
- **Schnelltexte verwalten:** Voreingestellte Schnelltexte können eingefügt und gelöscht werden; eigene Schnelltexte können hinzugefügt werden.
- **Schnelltexte speichern:** Persönliche Schnelltexte werden in den Benutzereinstellungen gespeichert.
- **Sendebestätigung:** Eigene Nachrichten zeigen ihren Versandstatus mit **⏳**, **✓** und **✓✓**.
- **Echo-/ACK-Auswertung:** Die Sendebestätigung berücksichtigt MeshCom-Echo und ACK-Rückmeldungen.
- **Neuer Tab „Monitor“:** Empfangene MeshCom-Pakete können übersichtlich überwacht werden.
- **Monitor-Filter:** Filter für **ALLE / MSG / POS / TEL / ACK**.
- **Monitor-Suche:** Empfangene Pakete können über eine Suchfunktion gefiltert werden.
- **Monitor-Steuerung:** Auto-Scroll, Pause und Leeren stehen direkt im Monitor zur Verfügung.
- **Monitor-Details:** Angezeigt werden unter anderem Zeit, Pakettyp, Von, Nach, RSSI, SNR und weitere Paketinformationen.
- **POS-Auswertung:** Positionsdaten werden mit Koordinaten, Höhe und Batterieinformationen aufbereitet.
- **TEL-Auswertung:** TEL-Daten werden im Monitor übersichtlich dargestellt.
- **ACK-Auswertung:** ACK-Pakete werden als eigener Pakettyp angezeigt.
- **Eigene Nachrichten im Monitor:** Auch selbst gesendete Nachrichten werden im Monitor berücksichtigt.
- **Neuer Tab „MH“:** Zuletzt gehörte Stationen werden in einer eigenen Übersicht angezeigt.
- **MH-Informationen:** Rufzeichen, Entfernung, RSSI, SNR, Batterie und letzter Empfang werden angezeigt.
- **MH-Entfernung:** Die Entfernung wird aus den vorhandenen GPS-Positionen berechnet.
- **MH-Auswahl:** Das eigene Rufzeichen wird nicht in der MH-Liste angezeigt; bestimmte Test-/Fremdstationen werden ausgeschlossen.
- **Chat-Bubbles:** Die Chatdarstellung wurde auf eine neue Bubble-Darstellung umgestellt.
- **Tab „Alle“:** Das Scrollverhalten wurde korrigiert, sodass die Scrollposition beim Aktualisieren des Nachrichtenverlaufs erhalten bleibt.
- **Benutzereinstellungen:** Die persönliche `settings.ini` liegt nicht mehr im Projektverzeichnis unter `data/`.
- **Standard-Einstellungen:** `data/default_settings.ini` dient als neutrale Vorlage.
- **Erststart:** Beim ersten Start wird daraus die persönliche Konfiguration unter `~/.MeshCom/settings.ini` erzeugt.
- **Bestehende Funktionen:** Die vorhandenen Raum-, Privat-, Karten-, Wetter- und Node-Info-Funktionen bleiben erhalten.

## v0.3.59 – Emoji-Unterstützung

- **Emoji-Anzeige vergrößert:** Die Smileys im Auswahlfenster sind jetzt etwas größer und dadurch beim Auswählen besser erkennbar, ohne den Picker unnötig groß zu machen.
- **Emoji-Auswahl:** Neben dem Nachrichtenfeld gibt es einen 😊-Button.
- **Emoji-Picker:** Ein kompaktes Auswahlfenster bietet häufig verwendete Smileys und Symbole.
- **Einfügen an Cursorposition:** Das ausgewählte Emoji wird direkt in die aktuelle Nachricht eingefügt.
- **149-Zeichen-Limit:** Die bestehende Nachrichtenbegrenzung bleibt aktiv; ein Emoji wird nicht eingefügt, wenn dadurch die Grenze überschritten würde.
- **Sende-/Empfangslogik:** Die bestehende MeshCom-Kommunikation wurde nicht verändert.

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

# CHANGELOG

## v0.3.63 – Sprache, Chat-Farben, Kontextmenü und Stabilität

- Projektversion auf **0.3.63** erhöht.
- Vollständige sichtbare Deutsch-/English-Umschaltung für die aktuelle Benutzeroberfläche ergänzt und dokumentiert.
- Spracheinstellung wird in `~/.MeshCom/settings.ini` gespeichert und beim Neustart wieder geladen.
- Dynamische Raum-Tabs werden korrekt als **All / Room …** bzw. **Alle / Raum …** angezeigt.
- Wetteranzeige einschließlich Temperatur, Luftfeuchte, QFE und QNH an die gewählte Sprache angepasst.
- Fehler bei wiederholtem Umschalten der Temperaturbezeichnung (`Temperatureee…`) behoben.
- Qt-Kontextmenü der Eingabefelder für Deutsch und English berücksichtigt.
- Chat-Farben dokumentiert: gemeinsamer Hintergrund für alle Chat-Ansichten, Schriftfarbe nur für „Alle“, Standard schwarz/weiß.
- Integrierte **Hilfe → Anleitung** auf den Funktionsstand v0.3.63 aktualisiert.
- Neue PDF-Benutzeranleitung `docs/MeshCom-Guru_Anleitung_v0.3.63.pdf` erstellt.
- Beenden stabilisiert: UDP-Listener wird sauber heruntergefahren und konkurrierende `closeEvent()`-Definitionen bereinigt.
- Sendererkennung für **Raum- und Privatnachrichten** korrigiert: Bei weitergeleiteten Nachrichten wird der ursprüngliche Absender verwendet; ein Relay-/Weiterleitungs-Rufzeichen wird nicht fälschlich als eigener Sender dargestellt.
- Chat-Bubbles bei einer oder wenigen Nachrichten am **unteren Rand** des Chatbereichs ausgerichtet.
- Bei längeren Chats bleibt das normale Scrollverhalten erhalten; manuelles Hochscrollen wird nicht durch neue Nachrichten zurückgesetzt.
- Bubble-Layout und Scrollbereich gezielt stabilisiert, ohne Wetter-, Karten-, Nachrichten- oder Senderlogik unnötig zu verändern.
- Die bekannten Qt-/Vulkan-/AT-SPI-Hinweise beim Start sind keine Programmfunktionen und wurden nicht künstlich unterdrückt.
- Bestehende Chat-, Privat-, Alle-, Karten-, Monitor-, MH- und Wetterfunktionen bleiben erhalten.


## v0.3.62 – Dokumentation, Anleitung und Release-Stand aktualisiert

- Projektversion auf **0.3.62** erhöht.
- Integrierte **Hilfe → Anleitung** vollständig auf den aktuellen Funktionsstand gebracht.
- Neue PDF-Benutzeranleitung für v0.3.62 erstellt.
- Dokumentation zu Nachrichten, Raum-Chats, Privat-Chats und Sendestatus aktualisiert.
- Dokumentation zu **⏳ Sanduhr / ✓✓ Empfänger-ACK** im Privat-Chat ergänzt.
- Dokumentation zu **⚡ Schnelltexten** und **😊 Emojis** ergänzt.
- Dokumentation zu **📡 Monitor** und **📋 MH** einschließlich UDP-Port 1799 aktualisiert.
- Dokumentation zu Karte, Positionsdaten, Wetter, Sound, Theme und Node Info aktualisiert.
- Persönliche Einstellungen eindeutig als `~/.MeshCom/settings.ini` dokumentiert.
- Debian-Installation nach `/usr/share/MeshCom` dokumentiert.
- Veraltete interne Analyse-/Hinweisdateien nicht in den Release-Stand übernommen.

## v0.3.61 – Einheitliche Chat-Bubbles für Raum-Tabs

- Normale Raum-Tabs verwenden dieselbe Bubble-Anordnung wie der Privat-Chat.
- Eigene Nachrichten werden rechts in Grün dargestellt.
- Empfangene Nachrichten werden links in Blau dargestellt.
- Kompakte `CALLSIGN>RAUM`-Antworten des MeshCom-WebService werden korrekt zerlegt.
- Der Tab „Alle“ bleibt unverändert.
- Bestehende Nachrichten-, Karten-, Monitor-, MH- und Wetterfunktionen bleiben erhalten.

## v0.3.60 – Schnelltexte, Sendebestätigung, Monitor, MH und Chat-Bubbles

- Schnelltexte mit Einfügen, Bearbeiten, Hinzufügen und Löschen.
- Persönliche Schnelltexte werden gespeichert.
- Sendestatus mit ⏳, ✓ und ✓✓.
- Echo-/ACK-Auswertung.
- Neuer Monitor mit Filtern ALLE / MSG / POS / TEL / ACK, Suche, Pause, Auto-Scroll und Leeren.
- Monitor-Details für Zeit, Pakettyp, Von, Nach, RSSI, SNR und weitere Paketinformationen.
- POS-, TEL- und ACK-Auswertung.
- Neuer MH-Tab mit Rufzeichen, Entfernung, RSSI, SNR, Batterie und letztem Empfang.
- Chat-Bubbles.
- Persönliche Einstellungen unter `~/.MeshCom/settings.ini`.

## v0.3.59 – Emoji-Unterstützung

- Emoji-Picker neben dem Nachrichtenfeld.
- Einfügen an der Cursorposition.
- Vergrößerte Emoji-Auswahl.
- 149-Zeichen-Limit bleibt aktiv.

## v0.3.58 – Wetterraum, Raumfilter und Entfernungsanzeige

- Wetterdaten können im aktuellen Raum gesendet werden.
- Raumfilter korrigiert.
- Entfernung zu anderen Kartenstationen wird angezeigt.

## v0.3.57 – Nachrichtenstabilität und saubere Benutzereinstellungen

- Nachrichten bleiben während der Sitzung erhalten.
- Chronologische Darstellung und Dublettenvermeidung verbessert.
- Persönliche Einstellungen nach `~/.MeshCom/settings.ini` verlagert.
- Neutrale Standardwerte ohne persönliche Vorgaben.

## v0.3.56 – Wetterdaten, Kartenansicht und Release

- WX-Testfunktion mit Temperatur, Luftfeuchte, QFE und QNH.
- OSM-/Leaflet-Kartenansicht verbessert.
- Node-Info-Seitenleiste verbessert.
- GitHub- und Debian-Release-Struktur eingeführt.

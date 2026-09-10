# CHANGELOG

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

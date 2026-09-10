# MeshCom-Guru v0.3.63

## Release v0.3.63

v0.3.63 ist der aktuelle stabile Release-Stand von MeshCom-Guru. Der Schwerpunkt dieser Version liegt auf der vollständigen Deutsch-/English-Benutzeroberfläche, den Chat-Farben, dem übersetzten Eingabefeld-Kontextmenü sowie einer stabileren Beendigung der Anwendung.

### Neu und verbessert

- Deutsch / English umschaltbar und dauerhaft gespeichert
- dynamische Raum-Tabs werden korrekt übersetzt
- Wetteranzeige wird vollständig sprachabhängig dargestellt
- Temperatur-Übersetzung bleibt bei wiederholtem Umschalten korrekt
- Qt-Kontextmenü in Eingabefeldern berücksichtigt die gewählte Sprache
- Chat-Farben: gemeinsamer Hintergrund für alle Chats, Schriftfarbe nur für „Alle“
- Standard-Chatfarben: schwarz / weiß
- integrierte Anleitung auf v0.3.63 aktualisiert
- neue PDF-Anleitung enthalten
- stabileres Beenden durch sauberes Herunterfahren des UDP-Listeners
- Sendererkennung in Raum- und Privat-Chats bei weitergeleiteten Nachrichten korrigiert
- Chat-Bubbles bei kurzen Chats am unteren Rand ausgerichtet; längere Chats behalten normales Scrollen
- manuelles Hochscrollen wird nicht durch neue Nachrichten überschrieben

### Bestehende Funktionen

- Raum-Chats und Privat-Chats
- Tab „Alle“
- einheitliche Chat-Bubbles in normalen Räumen
- Privat-Sendestatus mit **⏳** und echtem Empfänger-ACK **✓✓**
- **⚡ Schnelltexte**
- **😊 Emoji-Picker**
- 149-Zeichen-Limit mit Live-Zähler
- anklickbare HTTP-/HTTPS-Links
- **📡 Monitor** mit ALLE / MSG / POS / TEL / ACK
- **📋 MH – Most Recently Heard**
- OSM-/Leaflet-Karte und Positionsdaten
- Node Info
- Wetterdaten / WX
- Sound-Einstellungen
- Hell-/Dunkel-Theme
- Raumfilter bis zu fünf Räume
- persönliche Einstellungen unter `~/.MeshCom/settings.ini`
- Linux-, Windows- und Debian-Startwege

### Release-Dateien

- oberster Projektordner im Archiv: `MeshCom/`
- neue PDF-Anleitung: `docs/MeshCom-Guru_Anleitung_v0.3.63.pdf`
- persönliche Einstellungen nicht im Projektarchiv
- Debian-Ziel: `/usr/share/MeshCom`

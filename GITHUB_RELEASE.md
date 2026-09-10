# MeshCom-Guru v0.3.65

## Release v0.3.65

v0.3.65 ist der aktuelle Release-Stand von MeshCom-Guru. Diese Version enthält einen gezielten Fix gegen das gelegentliche Flackern der Nachrichtenblasen im Chat.

### Fehlerbehebung

- Gelegentliches Flackern der Nachrichtenblasen beim periodischen Chat-Refresh behoben.
- Bereits dargestellte Bubble-Widgets werden nicht mehr unnötig entfernt und neu erzeugt, wenn sich an der sichtbaren Darstellung nichts geändert hat.
- Ein tatsächlicher Neuaufbau erfolgt weiterhin bei neuen bzw. geänderten Nachrichten oder relevanten Statusänderungen.
- Die Änderung ist bewusst klein gehalten und greift nicht in die bestehende Nachrichtenlogik ein.

### Bestehende Funktionen

- Raum-Chats und Privat-Chats
- Tab „Alle“
- Tab „Weltweit“
- einheitliche Chat-Bubbles in den Chat-Ansichten
- Privat-Sendestatus mit **⏳** und Empfänger-ACK **✓✓**
- **⚡ Schnelltexte**
- **😊 Emoji-Picker**
- 149-Zeichen-Limit mit Live-Zähler
- anklickbare HTTP-/HTTPS-Links
- **📡 Monitor**
- **📋 MH – Most Recently Heard**
- OSM-/Leaflet-Karte und Positionsdaten
- Node Info
- Wetterdaten / WX
- Sound-Einstellungen
- Hell-/Dunkel-Theme
- Raumfilter
- persönliche Einstellungen unter `~/.MeshCom/settings.ini`
- Linux-, Windows- und Debian-Startwege

### Release-Dateien

- oberster Projektordner im Archiv: `MeshCom/`
- persönliche Einstellungen nicht im Projektarchiv
- Debian-Ziel: `/usr/share/MeshCom`

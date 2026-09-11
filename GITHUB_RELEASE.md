# MeshCom-Guru v0.3.66

## Release v0.3.66

v0.3.66 ist der stabile Release-Stand von MeshCom-Guru mit einer überarbeiteten Darstellung für Raum- und Privatnachrichten.

### Fehlerbehebung

- Das bisherige Flackern beim periodischen Aktualisieren des privaten Chats wurde beseitigt.
- Die Chat-Darstellung verwendet einen dauerhaft vorhandenen `QTextBrowser`/`QTextDocument`, sodass der Scrollbereich nicht bei jedem Refresh durch einen neuen Widget-Container ersetzt wird.
- Eingehende Nachrichten werden zuverlässig angezeigt, auch die erste neu empfangene Nachricht.
- Die aktuelle Darstellung verwendet farbige Nachrichtenfelder im stabilen Dokument.

### Bestehende Funktionen

- Raum-Chats und Privat-Chats
- Tab „Alle“
- Tab „Weltweit“
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

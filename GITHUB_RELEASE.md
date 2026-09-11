# MeshCom-Guru v0.3.67

## Release v0.3.67

v0.3.67 ist der stabile Release-Stand von MeshCom-Guru mit einer überarbeiteten Darstellung für Raum- und Privatnachrichten.

### Fehlerbehebung

- Fehler behoben, durch den ein bewusst geschlossener Privat-Chat nach einem späteren Refresh wieder geöffnet werden konnte, obwohl keine neue private Nachricht eingetroffen war.
- Der Schließzustand wird jetzt mit exakt demselben privaten Nachrichtenstand verglichen, der beim Refresh verwendet wird.
- Ein geschlossener Privat-Tab bleibt geschlossen, solange keine tatsächlich neue private Nachricht für dieses Rufzeichen vorliegt.
- Eine tatsächlich neue private Nachricht öffnet den Privat-Tab weiterhin automatisch.
- Ein erneutes bewusstes Senden an ein zuvor geschlossenes privates Ziel öffnet den zugehörigen Tab weiterhin sofort.
- Die Stabilitäts- und Flackerverbesserungen aus v0.3.66 bleiben erhalten.

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

# MeshCom-Guru v0.3.71

## Release v0.3.71

MeshCom-Guru v0.3.71 korrigiert die MH-Liste: UDP-/Gateway-Verkehr wird nicht mehr als gehörte Station übernommen. Nur tatsächlich über LoRa empfangene EXTUDP-Pakete (`src_type=lora` bzw. `node`) erzeugen MH-Einträge.

### Neu

- **MH-Liste korrigiert:** UDP-/Gateway-Pakete werden nicht mehr als gehörte Stationen übernommen.
- Bei Relay-Pfaden wird das erste Rufzeichen als ursprünglicher Absender verwendet; weitere Rufzeichen werden nicht als eigene MH-Stationen eingetragen.

- **🔗 Verbinden / ⛓️ Trennen** zur manuellen Steuerung der WebService-Verbindung.
- **Automatische Wiederverbindung** nach einem unbeabsichtigten Verbindungsverlust.
- **Trennen** deaktiviert Auto-Reconnect ausdrücklich.
- Beim Programmstart wird weiterhin **nicht automatisch verbunden**.
- **Deutsch / English / Italiano / Nederlands / Français** als umschaltbare UI-Sprachen.
- Dynamische Raum-Tabs werden sprachabhängig korrekt dargestellt.
- Übersetzungen für Status, Wetter, Schnelltexte, Statistik, Sound-Einstellungen, Kontextmenüs und weitere sichtbare UI-Texte ergänzt bzw. korrigiert.

### Erhaltene Funktionen

- Raum-Chats und Privat-Chats
- Tab **Alle** und Tab **Weltweit**
- **⚡ Schnelltexte** und **😊 Emoji-Picker**
- **📡 Monitor** und **📋 MH**
- OSM-/Leaflet-Karte und Positionsdaten
- Node Info
- Wetterdaten / WX
- Sound-Einstellungen
- Hell-/Dunkel-Theme
- Raumfilter
- persönliche Einstellungen unter `~/.MeshCom/settings.ini`
- Linux-, Windows- und Debian-Startwege

### Release-Struktur

- oberster Projektordner im Archiv: `MeshCom/`
- persönliche Einstellungen nicht im Projektarchiv
- Debian-Ziel: `/usr/share/MeshCom`

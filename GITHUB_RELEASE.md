# MeshCom-Guru v0.4.7 – WebService-Hintergrundabruf

## Änderungen

- ⚡ **WebService-Abruf im Hintergrund:** Der blockierende HTTP-Abruf läuft jetzt in einem eigenen Qt-Worker-Thread und blockiert den GUI-Thread nicht mehr.
- 🧩 **Nachrichtenverarbeitung unverändert:** Die bestehende Cache-, Sortier-, Raum-, Privat-, „Alle“-, Karten- und Statistiklogik bleibt im GUI-Thread und wurde nicht neu aufgebaut.
- ✅ **ACK/UDP unverändert:** Der direkte ACK-/UDP-Empfangspfad bleibt getrennt vom WebService-Worker.
- 🔄 **Verbindungstest/Reconnect:** Auch der erste Verbindungsabruf und automatische Reconnects verwenden den Hintergrund-Worker.
- 🛡️ **Bestehende Funktionen erhalten:** Die getesteten Funktionen und bisherigen Performance-/ACK-Fixes aus v0.4.6 und den vorherigen Versionen bleiben erhalten.

## Release-Stand

**Version:** 0.4.7  
**Projekt:** MeshCom-Guru  
**Ordner im ZIP:** `MeshCom/`

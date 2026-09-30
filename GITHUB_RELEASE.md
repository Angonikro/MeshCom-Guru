# MeshCom-Guru v0.4.4 – Performance-Optimierung

## Änderungen

- ⚡ **Langzeit-Performance:** Die vorhandene Nachrichten-Sortierung wird nur noch neu berechnet, wenn tatsächlich neue Nachrichten eingegangen sind. Dadurch wird bei langen Laufzeiten unnötige wiederholte Arbeit am wachsenden Nachrichtenbestand vermieden.
- 💬 **Sende-/Empfangspfad unverändert:** Senden, Echo, ACK und die Anzeige eigener Nachrichten wurden für diesen Performance-Fix nicht umgebaut.
- 🏠 **Raumauswahl:** Nur der aktuell ausgewählte Raum-Button bleibt blau; die anderen Raum-Buttons werden beim Raumwechsel wieder normal dargestellt.
- 🛡️ **Unbegrenzter Nachrichten-Cache:** Es wurde keine feste Cache-Grenze eingeführt und es werden keine alten Nachrichten gelöscht.

## Release-Stand

**Version:** 0.4.4  
**Projekt:** MeshCom-Guru  
**Ordner im ZIP:** `MeshCom/`

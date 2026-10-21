# MeshCom-Guru v0.5.6 – Nachrichtenpfade in Chats

## Neu in v0.5.6

- Pfadzeilen unter Nachrichten in „Alle“, Raum-Chats und Privat-Chats.
- Vorhandene EXTUDP-/WebService-Pfadinformationen werden für die passende Nachricht verwendet, soweit sie vom Datenstrom bereitgestellt werden.
- Bei eigenen ausgehenden Nachrichten kann das in der App eingestellte Rufzeichen als Ursprung dienen, wenn kein expliziter Pfad mitgeliefert wurde.
- POS-/TEL-Pfadanzeige bleibt erhalten.
- Die Karten-Verbindungshistorie wird nicht als Beweis für den Pfad einer einzelnen Nachricht verwendet.
- Die Pfadzeile verwendet die Chat-Textfarbe; vorhandene Pfadzeilen werden nicht absichtlich ein zweites Mal ergänzt.

**Version:** 0.5.6  
**Paket:** `meshcom-guru_0.5.6_all.deb`  
**GitHub-Archiv:** `MeshCom-Guru_v0.5.6_GITHUB.zip`  
**Architektur des Debian-Pakets:** `all`

## Prüfung und Testhinweis

Vor der Paketierung werden die Python-Dateien auf Syntax geprüft, das ZIP-Archiv auf Integrität geprüft und die Debian-Metadaten kontrolliert. Ein Live-Test mit einem realen MeshCom-Node/EXTUDP-Datenstrom gehört nicht zu diesen lokalen Prüfungen; deshalb kann die Verfügbarkeit vollständiger Relay-Pfade nur angezeigt werden, wenn die empfangenen Daten sie tatsächlich enthalten.

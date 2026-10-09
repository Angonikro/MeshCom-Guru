# MeshCom-Guru v0.5.5 – Bildvorschau nach dem Laden aktualisiert

## Neu in v0.5.5

- 🖼️ **Bildvorschau in „Alle“:** Wenn eine verlinkte Bildvorschau fertig geladen ist, wird „Alle“ einmal neu aufgebaut. So kann eine doppelte Darstellung direkt bereinigt werden, ohne auf eine weitere Nachricht warten zu müssen.
- 🔄 **Raumfilter-Fix erhalten:** Beim Aktivieren und Deaktivieren des Raumfilters wird die Ansicht sofort neu aufgebaut; vorhandene Wetter-/Telemetriedaten werden unmittelbar aktualisiert.
- ⚡ **POLL-FIX erhalten:** Der frühe Unverändert-Check bei identischen 5-Sekunden-WebService-Antworten bleibt enthalten.
- 🛡️ **Bestehende Funktionen:** Bild-Refresh wird über das vorhandene Qt-Signal im GUI-Thread ausgelöst. Nachrichtenbestätigungen, Räume, Privat-Chats, Favoriten, Monitor und Karte wurden für diesen Release nicht absichtlich verändert.
- 📦 **Saubere GitHub-ZIP:** Keine eingebettete Debian-Datei und keine Python-Cache-Dateien.
- 📖 **Dokumentation aktualisiert:** README, CHANGELOG, VERSION und version.py auf v0.5.5. Die acht PDF-Handbücher bleiben auf v0.5.2.

## Testhinweis

Der Ausgangspunkt ist der vom Nutzer bestätigte funktionierende Teststand `v0.5.4_IMAGE_REFRESH_TEST`. Die Bild-Refresh-Implementierung wurde unverändert übernommen. Die Syntax und ZIP-Struktur wurden geprüft; ein Live-Test mit realen Internet-Bildlinks und MeshCom-Nachrichten muss auf dem Zielgerät erfolgen.

**Version:** 0.5.5  
**Basis:** v0.5.4_IMAGE_REFRESH_TEST mit Bild-Refresh, Raumfilter-Refresh und dem bestehenden 5-Sekunden-POLL-FIX.

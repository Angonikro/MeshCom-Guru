# MeshCom-Guru v0.5.4 – Raumfilter aktualisiert Wetterdaten sofort

## Neu in v0.5.4

- 🔄 **Sofortiger Neuaufbau bei Filterwechsel:** Beim Aktivieren und Deaktivieren des Raumfilters wird die Ansicht „Alle“ einmal neu aufgebaut.
- 🌡️ **Wetterdaten ohne neue Nachricht:** Bereits empfangene Wetter-/Telemetriedaten werden sofort erneut dargestellt. Die Anzeige muss nicht mehr auf die nächste eingehende Nachricht warten.
- 🛡️ **Bestehende Logik erhalten:** Der 5-Sekunden-POLL-FIX, ACK/Echo-Bestätigungen, das 120-Sekunden-Statusfenster, Hard-Freeze, Räume, Privat-Chats, Favoriten/Online-Status, Monitor und Karte bleiben erhalten.
- 📖 **Dokumentation aktualisiert:** README, CHANGELOG, VERSION und version.py sind auf v0.5.4 gesetzt.

## Dokumentation

Die acht PDF-Handbücher bleiben auf dem Stand **v0.5.2**, weil dieser Release eine Aktualisierung der bestehenden Ansicht beim Filterwechsel korrigiert und keine neue Bedienfunktion einführt.

## Testhinweis

Der Raumfilter-Fix wurde im Teststand erfolgreich ausprobiert: Beim Aktivieren und Deaktivieren wird die Ansicht unmittelbar neu aufgebaut, sodass vorhandene Wetterdaten ohne neue Nachricht neu dargestellt werden.

**Version:** 0.5.4  
**Basis:** v0.5.3 mit unverändertem frühem Unverändert-Check für den 5-Sekunden-WebService-Poll und dem bestätigten Raumfilter-Refresh-Fix.

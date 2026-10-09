# MeshCom-Guru v0.5.3 – Optimierter 5-Sekunden-Poll

## Neu in v0.5.3

- ⚡ **Früher Unverändert-Check:** Bei einem identischen WebService-Ergebnis wird die unveränderte Rohantwort bereits vor dem Parsen der einzelnen Nachrichtenblöcke erkannt.
- 🧊 **Weniger wiederkehrende Verarbeitung:** Bei unveränderten 5-Sekunden-Abfragen werden die vorhandenen Nachrichten nicht erneut vollständig analysiert. Das reduziert die Arbeit besonders bei einem großen Nachrichtenbestand.
- 🖥️ **Weniger mögliche GUI-Belastung:** Der Poll verlässt den Verarbeitungspfad frühzeitig, wenn tatsächlich keine neuen WebService-Daten vorliegen.
- ✓ **ACK/Echo bleibt unabhängig:** ACK- und Echo-Status werden weiterhin über den bestehenden UDP-/Statuspfad verarbeitet und sind von diesem Shortcut nicht abhängig.
- 🛡️ **Bestehende Funktionen erhalten:** 120-Sekunden-Statusfenster, Hard-Freeze, Räume, Privat-Chats, Favoriten, Monitor, Karte, WebService und der bisherige Nachrichten-Signaturcheck bleiben erhalten.
- 🧩 **Bewusst kleiner Release:** „Alle“ und Monitor wurden in 0.5.3 noch nicht auf einen inkrementellen Aufbau („nur neue Einträge hinzufügen“) umgestellt.

## Dokumentation

Die vorhandenen acht PDF-Handbücher bleiben auf dem Stand **v0.5.2**, da v0.5.3 keine neue Bedienfunktion oder geänderte Benutzeroberfläche einführt.

- 🇩🇪 `docs/MeshCom-Guru_Benutzerhandbuch_v0.5.2_DE.pdf`
- 🇬🇧 `docs/MeshCom-Guru_User_Manual_v0.5.2_EN.pdf`
- 🇮🇹 `docs/MeshCom-Guru_Manuale_Utente_v0.5.2_IT.pdf`
- 🇳🇱 `docs/MeshCom-Guru_Gebruikershandleiding_v0.5.2_NL.pdf`
- 🇫🇷 `docs/MeshCom-Guru_Manuel_Utilisateur_v0.5.2_FR.pdf`
- 🇪🇸 `docs/MeshCom-Guru_Manual_de_Usuario_v0.5.2_ES.pdf`
- 🇸🇪 `docs/MeshCom-Guru_Anvandarmanual_v0.5.2_SV.pdf`
- 🇵🇱 `docs/MeshCom-Guru_Podrecznik_Uzytkownika_v0.5.2_PL.pdf`

**Version:** 0.5.3  
**Basis:** v0.5.2 mit dem gezielten frühen Unverändert-Check für den 5-Sekunden-WebService-Poll

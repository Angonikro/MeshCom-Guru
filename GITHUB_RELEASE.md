# MeshCom-Guru v0.5.2 – 5-Sekunden-Refresh und ACK/Echo-Optimierung

## Neu in v0.5.2

- ⚡ **Weniger unnötige Arbeit:** Der WebService wird weiterhin alle 5 Sekunden abgefragt. Bei unveränderten Daten wird der lokale Nachrichtenbestand nicht mehr bei jedem Durchlauf vollständig neu sortiert.
- 💤 **Leichtere Chat-Aktualisierung:** Wenn sich der sichtbare Inhalt nicht geändert hat, werden vorhandene Chat-Bubbles nicht erneut aufgebaut. Besonders bei vielen Nachrichten in **Alle** und den Räumen reduziert das die wiederkehrende GUI-Arbeit.
- ✓ **ACK/Echo unabhängig von neuen Nachrichten:** Echo und ACK werden als eigene Statusänderung behandelt. Eine vorhandene Nachricht kann dadurch auf **✓** bzw. **✓✓** wechseln, ohne dass erst eine weitere Chatnachricht eintreffen muss.
- 🏠 **Mehrere offene Sendungen:** Bestätigungen werden der passenden offenen Nachricht zugeordnet und nicht einfach der zuletzt gesendeten Nachricht. Dadurch bleiben Bestätigungen in mehreren Räumen getrennt.
- 📡 **Monitor unabhängig:** Der Chatstatus hängt nicht davon ab, ob im Monitor gerade ein ACK-Eintrag angezeigt wird.
- 🛡️ **Bestehende Statuslogik erhalten:** Das 120-Sekunden-Statusfenster und der anschließende Hard-Freeze bleiben unverändert.
- ⭐ **Favoriten aus v0.5.1 erhalten:** Favoriten können weiterhin mit Namen verwaltet werden; Name und Rufzeichen werden in der Online-Anzeige und im Popup gemeinsam dargestellt.

## Dokumentation

Die acht PDF-Handbücher wurden für **v0.5.2** neu strukturiert. Der Favoriten-/Namensabschnitt steht an der passenden Stelle im Handbuch; die neuen Refresh-/ACK-Optimierungen sind ebenfalls dokumentiert.

- 🇩🇪 `docs/MeshCom-Guru_Benutzerhandbuch_v0.5.2_DE.pdf`
- 🇬🇧 `docs/MeshCom-Guru_User_Manual_v0.5.2_EN.pdf`
- 🇮🇹 `docs/MeshCom-Guru_Manuale_Utente_v0.5.2_IT.pdf`
- 🇳🇱 `docs/MeshCom-Guru_Gebruikershandleiding_v0.5.2_NL.pdf`
- 🇫🇷 `docs/MeshCom-Guru_Manuel_Utilisateur_v0.5.2_FR.pdf`
- 🇪🇸 `docs/MeshCom-Guru_Manual_de_Usuario_v0.5.2_ES.pdf`
- 🇸🇪 `docs/MeshCom-Guru_Anvandarmanual_v0.5.2_SV.pdf`
- 🇵🇱 `docs/MeshCom-Guru_Podrecznik_Uzytkownika_v0.5.2_PL.pdf`

**Version:** 0.5.2  
**Basis:** funktionierender v0.5.1-Stand mit Favoriten-Namen, 120-Sekunden-Statusfenster und Hard-Freeze

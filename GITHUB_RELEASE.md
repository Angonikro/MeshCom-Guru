# MeshCom-Guru v0.5.1 – 120-Sekunden-Statusfenster und Hard-Freeze

## Neu in v0.5.1

- ⏳ **120-Sekunden-Bestätigungsfenster:** Eine neu gesendete oder empfangene Nachricht darf bis zu 120 Sekunden ihren Status aktualisieren.
- 📡 **Mehr Zeit für entfernte Stationen:** Echo und ACK können auch bei längeren Übertragungswegen innerhalb des offenen Zeitfensters eintreffen.
- 🔒 **Hard-Freeze:** Nach 120 Sekunden wird der Status der Nachricht endgültig eingefroren. Spätere ACKs, Echos, Refreshs oder Neuaufbauten verändern ihn nicht mehr.
- ♾️ **Kein 100-Nachrichten-Limit:** Die bisherige 100-Nachrichten-Begrenzung bleibt entfernt.
- 🧭 **Navigation unverändert:** Die funktionierende Navigation zwischen „Alle“, Räumen und privaten Chats bleibt erhalten.
- 🛡️ **Bestehende Funktionen erhalten:** Die Änderung betrifft ausschließlich das Status-Zeitfenster und den anschließenden Freeze.

## Dokumentation

Die acht vorhandenen PDF-Handbücher bleiben bewusst unverändert auf dem bisherigen Stand v0.4.9.

- 🇩🇪 `docs/MeshCom-Guru_Benutzerhandbuch_v0.4.9_DE.pdf`
- 🇬🇧 `docs/MeshCom-Guru_User_Manual_v0.4.9_EN.pdf`
- 🇮🇹 `docs/MeshCom-Guru_Manuale_Utente_v0.4.9_IT.pdf`
- 🇳🇱 `docs/MeshCom-Guru_Gebruikershandleiding_v0.4.9_NL.pdf`
- 🇫🇷 `docs/MeshCom-Guru_Manuel_Utilisateur_v0.4.9_FR.pdf`
- 🇪🇸 `docs/MeshCom-Guru_Manual_de_Usuario_v0.4.9_ES.pdf`
- 🇸🇪 `docs/MeshCom-Guru_Anvandarmanual_v0.4.9_SV.pdf`
- 🇵🇱 `docs/MeshCom-Guru_Podrecznik_Uzytkownika_v0.4.9_PL.pdf`

**Version:** 0.5.1  
**Basis:** v0.4.9 mit 120-Sekunden-Hard-Freeze

## v0.5.1 – Favoriten und Online-Status

- Favoriten-Manager und Online-Status mit einstellbaren Zeitgrenzen.
- Optionaler Signalton und Online-Popup mit einstellbarer Dauer.
- Direkte Aktivitätszeit-Übernahme beim Hinzufügen aus „Alle“ und beim manuellen Hinzufügen aus lokal bekannter Empfangsaktivität.
- Dokumentation und PDF-Handbücher in 8 Sprachen.

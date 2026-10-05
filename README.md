# MeshCom-Guru

**Aktuelle Version: 0.5.0**

MeshCom-Guru ist eine eigenständige Anwendung zur Anzeige von MeshCom-Nachrichten, Node-Informationen und Positionsdaten.


## Inhalt

- Chat mit empfangenen MeshCom-Nachrichten
- Räume und private Nachrichten
- Node-Informationen
- Kartenanzeige mit Positionsdaten
- **Karten-Verbindungen:** tatsächlich empfangene MeshCom-Pfade können als Linien auf der Karte angezeigt werden.
- **Farbige Kartenmarker:** Marker zeigen den Aktivitätsstatus über Blau/Grün/Orange/Grau; die eigene Station wird Rot dargestellt.
- **Rufzeichen auf der Karte:** Die Callsign-Anzeige kann direkt unter „Verbindungen“ ein- und ausgeschaltet werden.
- **Kompaktes Marker-Infofenster:** Position, Entfernung, letzte Aktivität sowie vorhandener Akkustand, Node-Typ und Firmware.
- Anzeige eigener Positionsdaten
- integriertes Menü **Hilfe**
- integrierte **Anleitung**
- **Info**-Fenster mit Programmversion
- Linux- und Windows-Startdateien
- Desktop-Launcher für Linux
- Nachrichtenfeld mit einer maximalen Länge von **149 Zeichen**
- Live-Zeichenzähler im Nachrichtenfeld (`0/149` bis `149/149`)
- **Emoji-Auswahl** direkt am Nachrichtenfeld mit automatischem Schließen nach der Auswahl
- **Bildvorschau für Picrd-Links:** Erkannte Bildlinks werden direkt im Chat als Vorschau angezeigt; normale Internetlinks bleiben unverändert anklickbar.

### Dokumentation

Im Release sind acht PDF-Handbücher enthalten. Alle acht wurden auf den Stand v0.4.9 aktualisiert:

- 🇩🇪 `docs/MeshCom-Guru_Benutzerhandbuch_v0.4.9_DE.pdf`
- 🇬🇧 `docs/MeshCom-Guru_User_Manual_v0.4.9_EN.pdf`
- 🇮🇹 `docs/MeshCom-Guru_Manuale_Utente_v0.4.9_IT.pdf`
- 🇳🇱 `docs/MeshCom-Guru_Gebruikershandleiding_v0.4.9_NL.pdf`
- 🇫🇷 `docs/MeshCom-Guru_Manuel_Utilisateur_v0.4.9_FR.pdf`
- 🇪🇸 `docs/MeshCom-Guru_Manual_de_Usuario_v0.4.9_ES.pdf`
- 🇸🇪 `docs/MeshCom-Guru_Anvandarmanual_v0.4.9_SV.pdf`
- 🇵🇱 `docs/MeshCom-Guru_Podrecznik_Uzytkownika_v0.4.9_PL.pdf`

## Version 0.5.0 – 120-Sekunden-Statusfenster und Hard-Freeze

- ⏳ **120-Sekunden-Bestätigungsfenster:** Eine neu gesendete oder empfangene Nachricht darf bis zu 120 Sekunden ihren Status aktualisieren. Dadurch haben auch weiter entfernte Stationen mehr Zeit für Echo und ACK.
- 🔒 **Hard-Freeze nach 120 Sekunden:** Nach Ablauf des Zeitfensters wird die Nachricht vollständig eingefroren. Spätere ACKs, Echos, Refreshs oder Neuaufbauten dürfen ihren Status nicht mehr verändern.
- 🧊 **Kein späterer Status-Neuaufbau:** Bereits eingefrorene Nachrichten werden bei späteren Aktualisierungen nicht erneut in einen offenen Status zurückgesetzt.
- ♾️ **Kein 100-Nachrichten-Limit:** Die bisherige Begrenzung auf 100 Nachrichten bleibt entfernt.
- 🧭 **Navigation erhalten:** Der funktionierende ursprüngliche Chat-Aufbau und die Navigation zwischen „Alle“, Räumen und privaten Chats bleiben erhalten.
- 🛡️ **Stabilitätsprinzip:** Die Änderung beschränkt sich auf das Status-Zeitfenster; die übrigen getesteten Funktionen werden nicht verändert.
- 📖 **Dokumentation:** Die vorhandenen PDF-Handbücher bleiben unverändert auf dem Stand v0.4.9.

## v0.4.9 – Temperatur im Karten-Infofenster und ruhige Popup-Aktualisierung

- 🌡️ **Temperatur im Karten-Infofenster:** Temperaturwerte aus der Node-Telemetrie werden bei vorhandenen Daten direkt im Kartenmarker-Infofenster angezeigt.
- 🌐 **8-sprachig:** Die neue Anzeige ist in Deutsch, Englisch, Italienisch, Niederländisch, Französisch, Spanisch, Schwedisch und Polnisch übersetzt.
- 🪟 **Popup-Refresh ohne sichtbares Blinken:** Beim Karten-Refresh werden bestehende Marker und geöffnete Popups wiederverwendet. Der Inhalt des Infofensters wird aktualisiert, ohne das Fenster zu schließen und neu zu öffnen.
- ⚡ **Marker-Performance:** Kein unnötiger kompletter Neuaufbau der Leaflet-Marker-Layer bei normalen Datenaktualisierungen; geänderte Marker werden gezielt aktualisiert.
- 🛡️ **Keine Änderungen an den bestehenden Nachrichten-/Empfangspfaden:** Die bisherigen stabilen Funktionen bleiben erhalten.
- 📖 **Dokumentation:** Integrierte Anleitung und alle acht PDF-Handbücher wurden auf v0.4.9 aktualisiert.

## Version 0.4.8 – Kartenmarker: Node-Typ und Firmware der eigenen Station

- 🗺️ **Eigene Station:** Das kompakte Karten-Infofenster zeigt jetzt auch für die eigene Station den erkannten **Node-Typ** und die **Firmware**, sofern diese Informationen aus dem eigenen POS/EXTUDP-Paket vorliegen.
- 🧩 **Einheitliche Darstellung:** Die eigene Station verwendet dabei dieselbe Node-Typ-/Firmware-Aufbereitung wie die übrigen Kartenmarker.
- 👁️ **Rufzeichen auf der Karte:** Die Rufzeichen der Stationen können direkt unter **🔗 Verbindungen** auf der Karte ein- und ausgeblendet werden.
- 🛡️ **Bestehende Kartenfunktionen erhalten:** Marker-Farben, Rufzeichen-Anzeige, Entfernungsanzeige und die übrigen Karteninformationen bleiben unverändert.
- 🛡️ **Bestehende Funktionen erhalten:** Nachrichten, Räume, private Chats, Monitor, MH, Karte, Weltweit, ACK/UDP und die bisherigen Performance-Fixes bleiben auf dem getesteten v0.4.7-Stand.
- 📖 **Dokumentation:** Alle acht PDF-Handbücher wurden auf v0.4.8 aktualisiert und enthalten die neuen Kartenmarker-/Rufzeichen-Funktionen an der passenden Stelle im Kartenabschnitt.

## Version 0.4.7 – WebService-Hintergrundabruf

- 🗺️ **Kartenmarker:** Stationsmarker werden abhängig von der letzten Aktivität farblich dargestellt: Blau (unter 30 Min.), Grün (30–120 Min.), Orange (2–12 Std.), Grau (über 12 Std.); die eigene Station bleibt Rot.
- 👁️ **Rufzeichen ein-/ausblendbar:** Direkt unter **🔗 Verbindungen** kann die Anzeige der Rufzeichen auf der Karte ein- und ausgeschaltet werden.
- ℹ️ **Kompaktes Marker-Infofenster:** Beim Anklicken eines Markers werden Position, Entfernung, letzte Aktivität sowie – sofern vorhanden – Akkustand, Node-Typ und Firmware angezeigt.
- 🌍 **Mehrsprachige Kartenanzeige:** Neue Kartenbeschriftungen und Statusbezeichnungen sind in allen acht unterstützten Sprachen verfügbar.
- 📖 **Dokumentation:** Die integrierte Anleitung und alle acht PDF-Handbücher wurden um die neuen Kartenmarker- und Rufzeichen-Funktionen ergänzt.
- ⚡ **WebService-Abruf im Hintergrund:** Der blockierende HTTP-Abruf läuft jetzt in einem eigenen Qt-Worker-Thread und blockiert den GUI-Thread nicht mehr.
- 🧩 **Nachrichtenverarbeitung unverändert:** Die bestehende Cache-, Sortier-, Raum-, Privat-, „Alle“-, Karten- und Statistiklogik bleibt im GUI-Thread und wurde nicht neu aufgebaut.
- ✅ **ACK/UDP unverändert:** Der direkte ACK-/UDP-Empfangspfad bleibt getrennt vom WebService-Worker.
- 🔄 **Verbindungstest/Reconnect:** Auch der erste Verbindungsabruf und automatische Reconnects verwenden den Hintergrund-Worker.
- 🛡️ **Bestehende Funktionen erhalten:** Die getesteten Funktionen und bisherigen Performance-/ACK-Fixes aus v0.4.6 und den vorherigen Versionen bleiben erhalten.

## Version 0.4.6 – Chat-Zeichen-Darstellung

- 💬 **Chat-Zeichen:** Sonderzeichen wie `'`, `<` und `>` werden in den Chatansichten wieder als normale Zeichen dargestellt, statt als sichtbare HTML-Zeichenreferenzen.
- 🏠 **Raum-Chats:** Die funktionierende Zeichenbehandlung der Raum-/Privatchats bleibt erhalten.
- 💬 **Alle-Chat:** Die Textaufbereitung im Bereich **„Alle“** wurde an den sicheren Textpfad angepasst, sodass Unicode- und Sonderzeichen korrekt angezeigt werden.
- 🛡️ **Bestehende Funktionen erhalten:** Nachrichten, Räume, private Chats, Monitor, MH, Karte, Weltweit sowie die bestehenden Performance- und ACK-Fixes bleiben erhalten.

## Version 0.4.5 – WebService-Performance und direkte ACK-Bestätigung

- ⚡ **WebService im Hintergrund:** Das Abrufen und Verarbeiten der WebService-Daten läuft nicht mehr im GUI-Thread. Dadurch bleibt die Oberfläche auch bei längeren Laufzeiten reaktionsfähiger.
- 🧹 **Weniger unnötige Aktualisierungen:** Unveränderte WebService-Daten werden nicht wiederholt vollständig verarbeitet und dargestellt.
- ✅ **ACK-Bestätigung direkt aktualisiert:** Sobald ein ACK empfangen wurde, wird der Status der gesendeten Nachricht direkt in der sichtbaren Chatansicht aktualisiert. Die Bestätigung muss dadurch nicht mehr auf den nächsten regulären Nachrichten-Refresh warten.
- 🗺️ **Eigener Kartenmarker:** Die Anzeige des eigenen Positionsmarkers bleibt erhalten.
- 🛡️ **Bestehende Funktionen erhalten:** Nachrichten, Räume, private Chats, Monitor, MH, Karte, Weltweit und die bisherigen Stabilitäts-/Performance-Fixes bleiben erhalten.

## Version 0.4.4 – Chat-Aufbau ohne sichtbaren Neuaufbau

- 💬 **Alle-Chat:** Der Bereich **„Alle“** wird beim Neuaufbau zunächst vollständig aufgebaut und erst danach sichtbar angezeigt. Dadurch ist der Aufbau von der ältesten zur neuesten Nachricht nicht mehr sichtbar.
- 🛡️ **Nachrichtenweg unverändert:** Nachrichtenlogik, Sortierung sowie Empfang und Senden bleiben unverändert. Die Räume und privaten Chats wurden durch diesen Fix nicht verändert.
- ⚡ **Langzeit-Performance bleibt erhalten:** Die Performance-Optimierungen aus v0.4.3 bleiben vollständig erhalten.

## Version 0.4.3 – Performance-Optimierung und Raumanzeige

- ⚡ **Langzeit-Performance:** Die bestehende Chat-Sortierung wird nur noch neu berechnet, wenn tatsächlich neue Nachrichten eingegangen sind. Dadurch entfällt die wiederholte Vollsortierung des wachsenden Nachrichtenbestands bei jedem Refresh.
- 💬 **Nachrichtenanzeige unverändert:** Senden, Echo, ACK und die Darstellung eigener Nachrichten bleiben auf dem bisherigen funktionierenden Pfad.
- 🏠 **Raumauswahl:** Beim Wechsel des Raums bleibt nur der aktuell ausgewählte Raum-Button blau markiert; die übrigen Raum-Buttons werden wieder normal dargestellt.
- 🛡️ **Cache:** Der Nachrichten-Cache bleibt weiterhin unbegrenzt; es werden keine alten Nachrichten aufgrund einer festen Cache-Grenze entfernt.

## Version 0.4.2 – Unterstützung für 6 Räume

- 🏠 **Sechs Räume:** Raumfilter, Raumverwaltung und Dashboard unterstützen jetzt bis zu **6 gespeicherte Räume**.
- 💬 **Raum-Chats:** Alle sechs gespeicherten Räume werden als eigene anklickbare Raum-Chats angezeigt.
- 🌐 **Mehrsprachige Dokumentation:** Integrierte Anleitung und alle acht PDF-Handbücher wurden auf v0.4.2 aktualisiert.
- 📚 **Dokumentation:** README, CHANGELOG und GitHub-Release-Dokumentation auf v0.4.2 aktualisiert.

## Version 0.4.1 – Vollständiger Mitternachts-Sortierfix

- 🕛 **Mitternachts-Sortierung:** Gespeicherte Chat-Nachrichten und der Chat-Export werden bei vorhandenen vollständigen Zeitstempeln nach Datum **und** Uhrzeit sortiert.
- 🔄 **00:00-Umsprung:** Nachrichten von `23:xx` und `00:xx` des Folgetages werden nicht mehr allein nach der Uhrzeit verglichen.
- 🛡️ **Live-„Alle“ unverändert:** Der funktionierende Live-Empfangsweg von v0.4.0 wurde nicht verändert.
- 🧩 **Rückwärtskompatibilität:** Ältere Karten ohne vollständiges Datum verwenden weiterhin die reine Uhrzeit als Fallback.

## Version 0.4.0 – Raum-Chat Bottom-Anchor Fix

- 💬 Raum-/Privat-Chats bleiben beim Wechsel zwischen gespeicherten Räumen zuverlässig unten ausgerichtet.
- 🔄 Der Wechsel zwischen Räumen benötigt keinen zweiten Klick mehr, um die letzte Nachricht unten anzuzeigen.
- 🛠️ Das Chat-Layout verwendet den freien Bereich oberhalb der Nachrichten statt unterhalb.
- 🛡️ Die Performance-Optimierungen und Stabilitätsfixes aus v0.3.99 bleiben erhalten.

## Version 0.3.99 – Performance-Optimierung

- ⚡ **Flüssigere Oberfläche:** Unnötige vollständige Aktualisierungen der Kartenansicht wurden reduziert.
- 🗺️ **Karte:** Marker werden nicht mehr bei jedem 5-Sekunden-Refresh vollständig gelöscht und neu aufgebaut, wenn sich die Kartendaten nicht geändert haben.
- 💬 **„Alle“:** Das komplette Chat-Dokument wird nicht mehr bei jedem Refresh neu erzeugt, wenn keine neuen Daten vorliegen.
- 📊 **Statistik:** Unveränderte Statistikdaten werden nicht mehr unnötig neu dargestellt.
- 🔄 **Weniger doppelte Aktualisierungen:** Überflüssige zweite Refresh-Durchläufe für Karte und Statistik wurden entfernt.
- 🛡️ **Funktionen erhalten:** Empfang, Senden, Räume, Private Chats, Monitor, MH, Karte, Weltweit, Wetter, Picrd-Vorschau und die bisherigen Stabilitätsfixes bleiben erhalten.
- 🧹 **Release-Bereinigung:** Keine `__pycache__`-Ordner oder `.pyc`-Dateien im GitHub-ZIP bzw. Debian-Paket.

## Version 0.3.98 – Final

- 🔄 **„Alle“ mit eigenem Live-Datenbereich:** Beim Wechsel zu „Alle“ werden die aktuellen Daten direkt aus dem eigenen Live-Puffer aufgebaut.
- ⚡ **Sofortige Darstellung:** Empfangene MSG/POS/TEL/ACK-Daten erscheinen ohne Warten auf einen zusätzlichen WebService-Refresh.
- 🌡️ **Wetter-/TEL-Daten:** Beim Wechsel zu „Alle“ müssen aktuelle Telemetriedaten nicht mehr auf den nächsten Refresh warten.
- 📤 **Eigene Nachrichten:** Gesendete Nachrichten werden ebenfalls direkt in „Alle“ übernommen.
- 🛡️ **Getrennter Empfangspfad:** Die bestehende Monitor-/UDP-Verarbeitung bleibt von der „Alle“-Darstellung getrennt.
- 🇵🇱 **Polnisch:** Die in v0.3.97 ergänzte polnische Sprache bleibt Bestandteil des finalen Releases.
- 🖼️ **Picrd-Vorschau:** Die in v0.3.96 eingeführte Bildvorschau bleibt Bestandteil des finalen Releases.
- 🕛 **Mitternachts-Fix:** Die zeitliche Verarbeitung bleibt auch beim Wechsel über 00:00 Uhr korrekt und hängt nicht mehr allein von der Uhrzeit ab.
- 🧪 **Langzeittest:** Der finale Stand wurde über 12 Stunden ohne erneutes Auftreten des zuvor beobachteten Fehlers getestet.
- 🧹 **Release-Bereinigung:** Keine `__pycache__`-Ordner oder `.pyc`-Dateien im GitHub-ZIP bzw. Debian-Paket.

## Version 0.3.97 – Polnische Sprache

- 🇵🇱 **Polnische Benutzeroberfläche:** Polski ergänzt und in die bestehende Sprachumschaltung integriert.
- 📖 **Integrierte Anleitung:** Die Hilfe/Anleitung ist auch vollständig auf Polnisch verfügbar.
- 📄 **Polnisches PDF-Handbuch:** Neues polnisches Benutzerhandbuch unter `docs/MeshCom-Guru_Podrecznik_Uzytkownika_v0.4.8_PL.pdf`.
- 🛡️ **Bestehende Funktionen unverändert:** Empfang, Senden, Räume, Private Chats, „Alle“, Monitor, MH, Karte, Weltweit, Picrd-Vorschau und Update-Prüfung wurden nicht durch einen neuen Nachrichtenweg ersetzt.
- 🧩 **Sprachmechanismus:** Polnisch ist Teil der normalen gespeicherten Spracheinstellung in `~/.MeshCom/settings.ini`.

## Version 0.3.96

### Neu in v0.3.96 – Picrd-Bildvorschau

- 🖼️ **Bildvorschau für Picrd-Links:** Bildlinks werden erkannt und direkt im Chat als Vorschau angezeigt.
- 🔗 **Original-Link bleibt erhalten:** Ein Klick auf den Link öffnet weiterhin die ursprüngliche Adresse im Standard-Webbrowser.
- 🌐 **Normale Internetlinks:** Links ohne Bildziel werden wie bisher als anklickbare Links dargestellt.
- 🔄 **Keine doppelten Vorschauen:** Bereits angezeigte Bildvorschauen werden bei späteren Chat-Aktualisierungen nicht erneut eingefügt.
- 📡 **Nachrichtenweg unverändert:** Empfang, Senden, Räume, Private Chats und „Alle“ bleiben funktional unverändert.
- 🌐 **Mehrsprachig:** Die neue Funktion ist in der integrierten Anleitung in Deutsch, English, Italiano, Nederlands, Français, Español, Svenska und Polski dokumentiert.
- 📄 **PDF-Handbücher:** Alle sieben Handbücher enthalten die Ergänzung zu v0.3.96.

# Sprache / Language

Unter **Einstellungen → Sprache / Language …** kann zwischen **Deutsch, English, Italiano, Nederlands, Français, Español, Svenska und Polski** gewechselt werden. Die Auswahl wird in `~/.MeshCom/settings.ini` gespeichert und beim nächsten Start wieder verwendet.

Die Benutzeroberfläche wird übersetzt; empfangene Nachrichten, Rufzeichen, Raum- und Zielnummern sowie persönliche Inhalte bleiben unverändert. Die integrierte **Hilfe → Anleitung** folgt der gewählten Sprache.

# Chat-Farben

Unter **Einstellungen → Chat-Farben …** können die Chat-Farben angepasst werden. Die Hintergrundfarbe gilt gemeinsam für alle Raum- und Chat-Ansichten. Die Schriftfarbe wird nur für den Tab **Alle** verwendet; die normalen Chat-Bubbles behalten ihre bestehende Farb- und Textdarstellung. Zusätzlich kann die Farbe für **anklickbare Rufzeichen und Internetlinks** unabhängig ausgewählt werden.

Die gewählte Linkfarbe wird gespeichert und in den Chat-Bubbles sowie beim HTML-Chat-Export verwendet. Mit **Standard wiederherstellen** werden die Chat-Farben einschließlich der Linkfarbe auf die Standardwerte zurückgesetzt; die Standard-Linkfarbe ist `#062f6f`.

# Kontextmenü in Eingabefeldern

Ein Rechtsklick in ein Eingabefeld öffnet das Qt-Kontextmenü. Die Standardbefehle wie Rückgängig, Wiederholen, Ausschneiden, Kopieren, Einfügen, Löschen und Alles auswählen werden entsprechend der gewählten Sprache angezeigt.

# Wetterdaten – BME280/BMP280

Unter **Einstellungen → Wetterdaten** kann die Wetteranzeige aktiviert werden. MeshCom-Guru liest die WX-Information direkt aus dem MeshCom-WebService des verbundenen Nodes. Unterstützt werden die dort angezeigten Werte **Temperatur, Luftfeuchte, QFE und QNH**.

Wenn am MeshCom-Node ein **BME280 oder BMP280 Wettermodul** erkannt wird, können die Wetterinformationen genutzt werden. Der eingegebene **Stadtname** wird zusammen mit den aktuellen Wetterwerten über **Wetter senden** ohne Raumangabe übertragen.

Ist die Wetterfunktion aktiviert, wird die WX-Information nach jedem Programmstart automatisch neu geladen. Die Funktion ist weiterhin als **Testfunktion** gedacht.

# OSM-Karte

Die OSM-/Leaflet-Kartenansicht bietet eine vergrößerte Kartenfläche.

# Persönliche Einstellungen

Die persönliche Konfiguration wird benutzerbezogen unter folgendem Pfad gespeichert:

```text
~/.MeshCom/settings.ini
```

Die Programmdateien selbst bleiben unter `/usr/share/MeshCom`. Beim ersten Start werden nur neutrale Standardwerte angelegt; persönliche Rufzeichen, Hotspot-IP und Räume werden nicht fest in den Programmdateien vorgegeben.

# Debian-Paket

Das Debian-Paket installiert MeshCom-Guru direkt unter:

```text
/usr/share/MeshCom
```

Es wird **keine eigene virtuelle Python-Umgebung** angelegt und während der Paketinstallation werden keine Python-Pakete per `pip` installiert. Das Paket bringt einen Menüeintrag und das Programm-Icon mit.

# Nachrichtenlänge

MeshCom-Nachrichten dürfen maximal **149 Zeichen** enthalten. Das Nachrichtenfeld begrenzt die Eingabe automatisch auf 149 Zeichen. Rechts im Eingabefeld zeigt ein Live-Zähler jederzeit die aktuelle Länge an, zum Beispiel `0/149`, `24/149`, `57/149` oder `149/149`.

Damit ist sofort sichtbar, wie viele Zeichen noch zur Verfügung stehen.

## Internetlinks und Bildvorschau im Chat

Internetlinks in empfangenen Nachrichten werden automatisch als anklickbare Links dargestellt. Ein Klick auf einen Link mit `http://` oder `https://` öffnet die Adresse im Standard-Webbrowser des Systems.

**Picrd-Bildlinks** werden zusätzlich geprüft. Wenn das Linkziel ein Bild bereitstellt, zeigt MeshCom-Guru eine kleine Bildvorschau direkt im Chat. Der ursprüngliche Link bleibt unter der Vorschau anklickbar. Links ohne Bildziel werden weiterhin ganz normal dargestellt. Bereits angezeigte Vorschauen werden bei späteren Chat-Aktualisierungen nicht doppelt eingefügt.

## Chat-Export

Über **Datei → Chat exportieren …** kann der aktuell ausgewählte Chat als **HTML, TXT oder CSV** gespeichert werden. Der HTML-Export enthält anklickbare Rufzeichen und Internetlinks und verwendet die aktuell eingestellte Linkfarbe. Der Export greift auf die vorhandenen Chatdaten zu und verändert die laufende Chat-Darstellung nicht.

---

# Installation unter Linux

## 1. ZIP-Datei entpacken

Entpacke die ZIP-Datei so, dass der Projektordner genau

`MeshCom`

heißt.

Beispiel:

```text
~/Downloads/MeshCom
```

## 2. Terminal öffnen

Wechsle in den Projektordner:

```bash
cd ~/Downloads/MeshCom
```

## 3. WebKitGTK für „Weltweit“ installieren

Unter **Linux / Raspberry Pi** benötigt der Tab **🌐 Weltweit** WebKitGTK.

Führe im Projektordner einmal aus:

```bash
chmod +x install_webkitgtk.sh
./install_webkitgtk.sh
```

Das Skript installiert die benötigten WebKitGTK-Systempakete. Dieser Schritt ist unter Linux für die Weltweit-Ansicht erforderlich.

## 4. Abhängigkeiten installieren

Führe aus:

```bash
chmod +x run_linux.sh install_desktop_launcher.sh scripts/create_desktop_entry.sh
```

Danach:

```bash
python3 -m pip install -r requirements.txt
```

Falls dein Linux-System die Installation von Python-Paketen außerhalb einer virtuellen Umgebung verhindert, kannst du eine virtuelle Umgebung verwenden:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 5. MeshCom-Guru starten

Mit:

```bash
./run_linux.sh
```

Alternativ:

```bash
python3 main.py
```

---

# Desktop-Launcher unter Linux installieren

MeshCom-Guru enthält ein Skript zum Erstellen einer Desktop-Verknüpfung.

Wechsle zuerst in den Projektordner:

```bash
cd ~/Downloads/MeshCom
```

Dann:

```bash
chmod +x install_desktop_launcher.sh
./install_desktop_launcher.sh
```

Falls das Skript mit fehlenden Rechten abbricht:

```bash
sudo ./install_desktop_launcher.sh
```

Danach sollte ein Starter für **MeshCom-Guru** im Desktop-/Anwendungsmenü vorhanden sein.

Zusätzlich kann der Desktop-Eintrag über das enthaltene Skript erstellt werden:

```bash
chmod +x scripts/create_desktop_entry.sh
./scripts/create_desktop_entry.sh
```

Der Launcher startet MeshCom-Guru über das Projekt und verwendet das mitgelieferte Icon.

---

# Installation unter Windows

## 1. ZIP-Datei entpacken

Entpacke die ZIP-Datei in einen geeigneten Ordner, zum Beispiel:

```text
C:\MeshCom
```

Der eigentliche Projektordner muss **MeshCom** heißen.

## 2. Python installieren

Für Windows wird Python **3.10 bis 3.14** benötigt. Die aktuelle PySide6-Version 6.11.2 unterstützt diese Python-Versionen.

Bei der Python-Installation sollte **Add Python to PATH** aktiviert werden.

## 3. Abhängigkeiten installieren

Öffne die Eingabeaufforderung oder PowerShell und wechsle in den Projektordner:

```bat
cd C:\MeshCom
```

Danach:

```bat
python -m pip install -r requirements.txt
```

Die Kartenfunktion verwendet die integrierte OSM-/Leaflet-Darstellung. Für die Weltweit-Ansicht wird unter Linux/Raspberry Pi WebKitGTK verwendet.

**Hinweis:** `PySide6-WebEngine` wird nicht mehr als eigenes Paket verwendet.

## 4. MeshCom-Guru starten

Die mitgelieferte Windows-Startdatei kann verwendet werden:

```text
run_windows.bat
```

Alternativ:

```bat
python main.py
```

Die mitgelieferte `run_windows.bat` prüft die Python-Version, installiert die benötigten Pakete und startet anschließend MeshCom-Guru.

---

# Hilfe und Info

In der Menüleiste befindet sich der Punkt:

**Hilfe**

Dort stehen zwei Funktionen zur Verfügung:

### Weltweit

Der Tab **🌐 Weltweit** befindet sich direkt neben **Karte** und öffnet die öffentliche MeshCom-Aktivitätsseite des ÖVSV. Beim Laden wird automatisch **ACTIVITY** ausgewählt. Die eingebettete Webseite übernimmt ihre eigene Aktualisierung; MeshCom-Guru führt keinen zusätzlichen 15-Sekunden-Refresh aus.

### Anleitung

Öffnet eine integrierte Kurzanleitung direkt in MeshCom-Guru.

### Info

Öffnet ein kleines Informationsfenster mit:

**MeshCom-Guru**  
**Version 0.5.0**

**By Goldisoft 2026**

---

# Chat

Im Chatbereich werden empfangene MeshCom-Nachrichten angezeigt.

Die vorhandenen Tabs ermöglichen die getrennte Anzeige von:

- allen Nachrichten
- Räumen
- privaten Nachrichten

Nachrichten können über das Eingabefeld erstellt und mit **Senden** übertragen werden.

### Wetter senden

Die Wetterfunktion sendet die aktuelle Wetterinformation jetzt in den Raum, in dem man sich aktuell befindet.

### Raumfilter

Der Raumfilter filtert die Nachrichten jetzt korrekt nach den gespeicherten Räumen.

### Kartenentfernung

Bei anderen Stationen wird im Kartenmarker zusätzlich die Entfernung zur eigenen Station angezeigt, sofern eigene GPS-Koordinaten vorhanden sind.

---

# Node-Informationen

Empfangene Node-Informationen können angezeigt werden.

Je nach übertragenen Daten können unter anderem folgende Informationen vorhanden sein:

- Rufzeichen
- Firmware
- Hardware-ID
- RSSI
- SNR
- Batterie
- Temperatur
- weitere Telemetriedaten
- Positionsdaten

---

# Karte und Koordinaten

Wenn ein Node Positionsdaten überträgt, können diese auf der Karte als Marker dargestellt werden.

Dabei werden insbesondere folgende Daten verwendet:

- Breitengrad
- Längengrad
- Höhe
- Rufzeichen

Die Positionsdaten stammen aus den empfangenen MeshCom-Daten.

### Kartenmarker-Infofenster

Beim Anklicken eines Markers zeigt das Infofenster Position, Entfernung und letzte Aktivität. Wenn Telemetriedaten vorhanden sind, werden zusätzlich Akkustand, Node-Typ, Firmware und **Temperatur** angezeigt. Das geöffnete Infofenster bleibt bei normalen Kartenaktualisierungen geöffnet und wird ohne kompletten Neuaufbau aktualisiert.

---

# Eigene Position

Falls die Funktion verwendet wird, können die eigenen Koordinaten über die dafür vorgesehenen Eingabefelder angegeben werden.

Beispiel:

```text
Breitengrad: 51.93
Längengrad: 8.88
```

---

# Eigenständiger Betrieb

MeshCom-Guru ist als eigenständige Anwendung aufgebaut.

Die Anwendung benötigt **keine Zusammenarbeit mit MeshDash**.

---

# Projektdateien

Wichtige Dateien und Verzeichnisse:

```text
MeshCom/
├── core/
├── data/
├── docs/
├── icons/
├── scripts/
├── ui/
├── main.py
├── requirements.txt
├── run_linux.sh
├── run_windows.bat
├── install_desktop_launcher.sh
├── README.md
├── CHANGELOG.md
└── VERSION
```

---

# Start unter Linux – Kurzfassung

```bash
cd ~/Downloads/MeshCom
chmod +x run_linux.sh
./run_linux.sh
```

Desktop-Launcher:

```bash
cd ~/Downloads/MeshCom
chmod +x install_desktop_launcher.sh
./install_desktop_launcher.sh
```

---

# Start unter Windows – Kurzfassung

Im Ordner `MeshCom` einfach

```text
run_windows.bat
```

starten.

---

**MeshCom-Guru v0.5.0**  
**By Goldisoft 2026**


## GitHub

Dieses Paket ist als vollständiger Projektstand für GitHub vorbereitet.
Der ZIP-Inhalt beginnt mit dem Ordner `MeshCom/`.

Die Projektdateien, Dokumentation, Startdateien, Desktop-Launcher,
Anleitung und das Programm-Icon sind im Projekt enthalten.

Die integrierte Anleitung in **Hilfe → Anleitung** ist die aktuelle, mehrsprachige Anleitung. Die mitgelieferten PDF-Handbücher entsprechen dem aktuellen v0.4.9-Dokumentationsstand.


## Hilfe und Info

In der Menüleiste gibt es **Hilfe → Anleitung** mit einer integrierten Kurzanleitung sowie **Hilfe → Info** mit Programmname, Version und Urheberhinweis.

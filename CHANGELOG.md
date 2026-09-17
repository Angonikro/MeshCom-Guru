# Changelog

## v0.3.80 – Weltweit mit WebKitGTK und Übersetzungs-/Wetterkorrekturen

- **🌐 Weltweit neu umgesetzt:** Die echte ÖVSV-MeshCom-Seite wird innerhalb von MeshCom-Guru über **WebKitGTK** eingebettet. Dadurch benötigt der Weltweit-Bereich keinen eigenen QtWebEngine/Chromium-Renderer mehr.
- **Automatische Plattform-Erkennung:** MeshCom-Guru erkennt beim Start selbst, ob die Anwendung unter **Linux** oder **Windows** läuft, und wählt für den Tab **Weltweit** automatisch die passende Web-Technik: **WebKitGTK unter Linux/Raspberry Pi** und **QtWebEngine unter Windows**. Die OSM-Karte bleibt auf beiden Plattformen bei der vorhandenen QtWebEngine-Implementierung.
- **ACTIVITY automatisch:** Beim Laden der ÖVSV-Seite wird weiterhin automatisch **ACTIVITY** geöffnet.
- **OSM-Karte erhalten:** Die vorhandene OSM-/Leaflet-Karte bleibt unverändert als QtWebEngine-Ansicht erhalten.
- **Weltweit-Größe korrigiert:** Die eingebettete WebKitGTK-Seite erhält beim Start zuverlässig ihre verfügbare Höhe und muss nicht mehr erst durch Ziehen des Splitters sichtbar gemacht werden.
- **WebKitGTK-Installation:** Das Projekt enthält `install_webkitgtk.sh` für die benötigten Debian/Raspberry-Pi-Pakete.
- **Übersetzungen aktualisiert:** Sichtbare Dashboard-, Monitor-, MH- und Wetterbezeichnungen wurden für Deutsch, English, Italiano, Nederlands und Français ergänzt bzw. korrigiert.
- **Temperaturanzeige korrigiert:** Die Wetteranzeige verwendet wieder die saubere Bezeichnung **Temperatur** bzw. die jeweilige Übersetzung; der fehlerhafte zusätzliche Buchstabe am Ende der Bezeichnung wurde entfernt.
- **Temperatur-/Wetter-Sprachwechsel stabilisiert:** Wetterwerte werden aus den Rohdaten neu aufgebaut, statt bereits übersetzte Texte erneut zu übersetzen.
- Die bisherigen Emoji-, Schnelltext-, Chat-, Monitor-, MH-, GPS-, Wetter-, Statistik-, Dashboard- und Kartenfunktionen bleiben erhalten.


## v0.3.79 – Emoji-Einfügen korrigiert

- **Emoji-Popup korrigiert:** Das Emoji-Fenster öffnet sich wieder direkt über dem jeweils gedrückten Smiley-Symbol – sowohl in **Klassisch** als auch im **Dashboard**.
- **Emoji-Fix:** Das ausgewählte Emoji wird jetzt zuverlässig in das Nachrichtenfeld eingefügt, das vor dem Öffnen des Emoji-Pickers aktiv war.
- Verhindert, dass ein zuvor verwendetes Emoji aus dem anderen Nachrichtenfeld erneut übernommen wird.
- Nach dem Einfügen bleibt der Fokus auf dem tatsächlich verwendeten Nachrichtenfeld.
- Schnelltexte und die übrigen Funktionen aus **v0.3.78** bleiben erhalten.

## v0.3.78 – Neues Dashboard

- Rufzeichen direkt im Dashboard in der ersten Reihe editierbar und speicherbar.
- Raum/Ziel, Node Info, GPS und „Einstellungen speichern“ kompakt in der zweiten Reihe angeordnet.
- Doppelte GPS-Speicher-Schaltfläche im Dashboard entfernt.
- **GPS-Synchronisation korrigiert:** Beim Wechsel von **Klassisch** zu **Dashboard** werden die aktuell eingegebenen GPS-Daten aus der klassischen Ansicht übernommen, sodass keine alten Dashboard-Werte angezeigt werden.
- **Ansichtswechsel korrigiert:** Beim Wechsel zwischen **Dashboard** und **Klassisch** wird das aktuell ausgewählte Chat-Ziel korrekt über die `settings.ini` übernommen.
- **Senden korrigiert:** In der klassischen Ansicht wird beim Senden das tatsächlich ausgewählte Chat-Ziel verwendet; gespeicherte `filter_room`-Werte überschreiben das Sendeziel nicht mehr.
- **Neues Dashboard-Design:** Unter **Einstellungen → Darstellung** kann zwischen **Dashboard** und **Klassisch** gewechselt werden. Beide Ansichten verwenden dieselben vorhandenen MeshCom-Daten und Funktionen.
- **Dashboard als vollständige Ansicht:** Räume, **Alle**, Private Chats, Karte, Weltweit, Monitor, Stations / MH und Statistik sind direkt im Dashboard erreichbar.
- **Alle oben:** Die Ansicht **Alle** befindet sich direkt unter dem Raumfilter.
- **Raum-Chats:** Die gespeicherten Räume werden direkt als anklickbare Raum-Chats angezeigt und bleiben auch für den klassischen Nachrichtenfilter erhalten.
- **Private Chats:** Private Unterhaltungen sind getrennt erreichbar und besitzen einen eigenen Scrollbereich.
- **Karte:** Stations- und Positionsdaten bleiben direkt im Dashboard verfügbar.
- **🌐 Weltweit:** Die MeshCom-Activity-Seite ist direkt eingebettet. Die Webseite übernimmt ihre eigene Aktualisierung; ein zusätzlicher 15-Sekunden-Refresh wird nicht verwendet.
- **Weltweit-Watchdog:** Ein Renderer-Absturz oder ein länger anhaltender Hänger der eingebetteten Weltweit-Ansicht wird erkannt und die Ansicht automatisch wiederhergestellt. Danach wird **ACTIVITY** wieder ausgewählt.
- **Klassisch-Ansicht korrigiert:** Beim Wechsel vom Dashboard zurück auf Klassisch werden Karte und Weltweit wieder als echte Qt-WebEngine-Ansichten aufgebaut. Die bisherigen Platzhalter werden nicht mehr angezeigt.
- **Monitor verbessert:** Lange Informationen und Nachrichten werden vollständig dargestellt, automatisch umgebrochen und bei Bedarf über die vorhandene Scrollmöglichkeit lesbar gehalten.
- **Auto-Reconnect:** Nach einem unbeabsichtigten Verbindungsverlust wird automatisch erneut verbunden; die bisherige Onlinezeit läuft beim Reconnect weiter. Ein manuelles Trennen setzt die Onlinezeit bewusst zurück.
- **Wetter und GPS:** Wetterdaten, Wetter-Aktualisierung, Wetter-Senden und GPS-Eingabe sind kompakt im Dashboard zusammengeführt.
- **Mehrsprachige Dashboard-Oberfläche:** Die neuen Bereiche und Bezeichnungen sind für Deutsch, English, Italiano, Nederlands und Français vorbereitet.
- **Anleitungen:** Die integrierte Anleitung und die mitgelieferten PDF-Anleitungen bleiben Teil des v0.3.78-Stands.
- Bestehende Funktionen aus **v0.3.77** bleiben erhalten.

## v0.3.77

- **🌐 Weltweit-Tab integriert:** Der Weltweit-Tab ist direkt neben **Karte** verfügbar und öffnet die öffentliche MeshCom-Aktivitätsseite des ÖVSV.
- Beim Laden wird automatisch **ACTIVITY** ausgewählt. Die eingebettete Webseite übernimmt ihre eigene Aktualisierung; MeshCom-Guru verwendet keinen zusätzlichen 15-Sekunden-Refresh.
- **Mehrsprachigkeit erweitert:** Der neue Weltweit-Tab und die zugehörigen Hinweise sind in Deutsch, English, Italiano, Nederlands und Français berücksichtigt.
- **Integrierte Anleitung aktualisiert:** Die neue Weltweit-Funktion ist in allen fünf Sprachen dokumentiert.
- Alle bestehenden Funktionen aus **v0.3.76** – einschließlich **Chat exportieren** und der erweiterten **Farbauswahl** – bleiben erhalten.

## v0.3.76

- **Mehrsprachige Oberfläche aktualisiert:** Die neuen Funktionen **Chat exportieren** und die **erweiterte Farbauswahl** sind jetzt in Deutsch, English, Italiano, Nederlands und Français berücksichtigt.
- **Chat exportieren** ist in allen unterstützten Sprachen beschriftet, einschließlich Exportdialog, Statusmeldungen und Fehlermeldungen.
- **Erweiterte Farbauswahl:** Die Auswahl für Chat-Hintergrund, Schriftfarbe von „Alle“ und die Farbe für anklickbare Rufzeichen und Internetlinks ist vollständig übersetzt.
- Die bestehende Chat-Export-Funktion (HTML, TXT, CSV) und die neue Link-/Rufzeichenfarbe bleiben unverändert erhalten.
- **Kein Weltweit-Tab in dieser GitHub-Version:** Die Weltweit-Funktion bleibt bewusst der späteren privaten Version vorbehalten.


## v0.3.75

- **Chat-Export (Testfunktion):** Der aktuell ausgewählte Chat kann über **Datei → Chat exportieren …** als HTML-, TXT- oder CSV-Datei gespeichert werden.
- Der HTML-Export übernimmt anklickbare Rufzeichen und Internetlinks sowie die aktuell eingestellte Linkfarbe.
- Der Export verwendet die vorhandenen Chatdaten und verändert die bestehende Chat-Darstellung und Nachrichtenverarbeitung nicht.
- **Farbwahl für anklickbare Rufzeichen und Internetlinks:** Unter **Einstellungen → Chat-Farben** kann die Farbe dieser Links jetzt unabhängig von der normalen Chat-Schriftfarbe ausgewählt werden.
- Die ausgewählte Linkfarbe wird gespeichert und in den runden Chat-Bubbles verwendet.
- **Standard wiederherstellen** setzt die Linkfarbe auf `#062f6f` zurück.
- Alle bestehenden Funktionen aus v0.3.74 bleiben erhalten.


## v0.3.74

- **Chat-Bubbles auf Methode 4 umgestellt:** Die normalen Raum- und Privat-Chats verwenden jetzt stabile Qt-`QWidget`-Bubbles mit runden Ecken.
- Eigene Nachrichten werden weiterhin **rechts/grün**, empfangene Nachrichten **links/blau** dargestellt.
- Die Bubble-Darstellung wurde mit langen Chatverläufen bis mindestens **30 Nachrichten** getestet und blieb dabei stabil.
- Bestehende Nachrichten-, Verbindungs-, Raum-, Privat-, Alle-, Weltweit-, Karten-, Monitor-, MH-, Wetter- und Statistikfunktionen bleiben erhalten.

## v0.3.73

- **Onlinezeit korrigiert:** Bei einem unbeabsichtigten Verbindungsverlust bleibt die bereits erreichte Onlinezeit erhalten. Nach dem automatischen Reconnect läuft die Onlinezeit weiter, statt wieder bei `00:00:00` zu beginnen.
- **Manuelles Trennen:** Ein bewusstes Trennen setzt die Onlinezeit weiterhin auf `00:00:00` zurück.
- Alle übrigen Funktionen und Inhalte aus v0.3.72 bleiben unverändert.

## v0.3.72

- Rufzeichen in den blauen Nachrichtenfeldern der normalen Räume und Privat-Chats werden dunkler dargestellt.
- Der Tab „Alle“ bleibt von dieser Änderung ausgenommen.
- Alle übrigen Funktionen und Inhalte von v0.3.71 bleiben unverändert.

## v0.3.71

- **MH-Liste korrigiert:** Nur tatsächlich über LoRa empfangene Pakete (`src_type=lora` bzw. `node`) dürfen neue Stationen in die MH-Liste eintragen. UDP-/Gateway-Verkehr wird nicht mehr als gehörte Station übernommen.
- Bei Relay-Pfaden wird weiterhin ausschließlich das **erste Rufzeichen** als ursprünglicher Absender verwendet; nachfolgende Rufzeichen sind Relay-Hops.

## v0.3.70 – Automatische Wiederverbindung nach Verbindungsverlust

- Die integrierte **Hilfe → Anleitung** wurde auf v0.3.70 aktualisiert und unterstützt jetzt Deutsch, English, Italiano, Nederlands und Français.
- Die separate PDF-Anleitung wurde auf den Funktionsstand v0.3.70 aktualisiert.

- Italienisch, Niederländisch und Französisch als zusätzliche UI-Sprachen ergänzt.
- Sprachauswahl erweitert; Sprache wird in `settings.ini` gespeichert.
- Übersetzungskataloge für alle drei neuen Sprachen vollständig ergänzt, einschließlich Statusmeldungen, Wetteranzeige, Schnelltexte, Sound-Einstellungen, Statistik und Kontextmenüs.
- Fehlende bzw. noch deutsche/englische UI-Texte in Italienisch, Niederländisch und Französisch korrigiert.
- Dynamische Raum-Tabs werden jetzt korrekt in der jeweils gewählten Sprache angezeigt (z. B. **Stanza 10**, **Ruimte 10**, **Salon 10**) und bleiben auch nach einem Sprachwechsel korrekt übersetzt.
- Sprachbezeichnungen im Sprachauswahl-Dialog wurden für Französisch, Italienisch und Niederländisch korrigiert.
- Mehrere sprachlich unnatürliche Wetter-/Statusformulierungen in Französisch, Italienisch und Niederländisch verbessert.
- Die Übersetzung der sichtbaren UI-Texte verwendet bei dynamischen Tabs jetzt den internen Raum-Schlüssel statt des bereits übersetzten Tab-Titels. Dadurch werden doppelte oder falsche Sprachwechsel verhindert.


- Die Verbindung zum MeshCom-WebService wird nach einem einmaligen Klick auf **Verbinden** automatisch wiederhergestellt, wenn der WebService, das Netzwerk oder der Hotspot die Verbindung verliert.
- Der vorhandene 5-Sekunden-Refresh prüft gleichzeitig, ob eine verlorene Verbindung wieder verfügbar ist.
- Ein vorübergehender HTTP-/Netzwerkfehler schaltet die automatische Wiederverbindung nicht mehr dauerhaft ab.
- **Trennen** beendet die automatische Wiederverbindung ausdrücklich. Nach einem manuellen Trennen verbindet sich das Programm nicht selbst wieder.
- Beim erneuten Verbinden wird der normale Verbindungsstatus wieder auf **ONLINE** gesetzt.
- Beim Programmstart bleibt das bisherige Verhalten erhalten: Es wird **nicht automatisch verbunden**; erst **Verbinden** aktiviert die automatische Wiederverbindung.
- Bestehende Nachrichten-, Raum-, Privat-, Alle-, Weltweit-, Karten-, Monitor-, MH-, Wetter- und Statistikfunktionen bleiben unverändert.

## v0.3.69 – Englische Übersetzung der neuen Funktionen
- Statistik-Tab wechselt beim Umschalten der Sprache sofort zwischen Deutsch und Englisch; kein Neustart mehr erforderlich.

- Die neuen Funktionen aus v0.3.68 wurden in die englische Benutzeroberfläche aufgenommen.
- **Statistik** wird auf Englisch als **Statistics** angezeigt.
- **Verbinden** wird als **Connect** angezeigt.
- **Trennen** wird als **Disconnect** angezeigt.
- Die zugehörigen Online-/Offline-Statusmeldungen, Verbindungsmeldungen und Fehlermeldungen wurden ergänzt.
- Die neuen Statistik-Bezeichnungen wurden ergänzt.
- Bestehende Übersetzungen und Funktionen wurden nicht verändert.

## v0.3.68 – Online-Status und Statistik

- Sichtbare Verbindungsanzeige in der oberen Statuszeile ergänzt.
- **🟢 ONLINE** bei erfolgreicher Verbindung zum MeshCom-WebService.
- **🔴 OFFLINE** bei fehlender Verbindung.
- Anzeige der aktuellen Verbindungsdauer mit **„seit HH:MM:SS“**.
- Online-Status und Uhr/Datum deutlich größer und besser lesbar dargestellt.
- Neuer fester Tab **📊 Statistik** ohne Schließen-X.
- Statistik zeigt die vorhandenen Nachrichten- und Raumdaten übersichtlich an.
- Bestehende Nachrichten-, Raum-, Privat-, Alle-, Weltweit-, Karten-, Monitor-, MH- und Wetterfunktionen bleiben erhalten.

## v0.3.67 – Privatchat-Schließen korrigiert

- Fehler behoben, durch den ein bewusst geschlossener Privat-Chat nach einem späteren Nachrichten-Refresh wieder automatisch geöffnet werden konnte, obwohl keine neue Nachricht eingetroffen war.
- Der Schließzustand eines Privat-Tabs wird jetzt mit exakt demselben Nachrichtenstand verglichen, der beim Refresh geprüft wird.
- Ein geschlossener Privat-Tab bleibt geschlossen, solange keine tatsächlich neue private Nachricht für dieses Rufzeichen eingetroffen ist.
- Wird eine neue private Nachricht empfangen, darf der entsprechende Privat-Tab weiterhin automatisch wieder erscheinen.
- Wird nach dem Schließen erneut bewusst an dasselbe Rufzeichen gesendet, wird der Privat-Tab wie bisher sofort wieder geöffnet.
- Die bestehenden Flacker- und Stabilitätsverbesserungen aus v0.3.66 bleiben erhalten.
- Nachrichten-, Raum-, Privat-, Alle-, Weltweit-, Karten-, Monitor-, MH- und Wetterfunktionen bleiben ansonsten unverändert.


## v0.3.65 – Chat-Bubble-Flackerfix

- Gezielten Fehler beim gelegentlichen Flackern der Nachrichtenblasen behoben.
- Der periodische Chat-Refresh baut die vorhandenen Bubble-Widgets nicht mehr unnötig neu auf, wenn sich der sichtbare Inhalt nicht geändert hat.
- Dadurch bleiben bestehende Nachrichtenblasen beim normalen Hintergrund-Refresh stabil sichtbar.
- Neuaufbau erfolgt weiterhin, wenn sich der sichtbare Nachrichteninhalt oder ein relevanter Sendestatus tatsächlich ändert.
- Bestehende Nachrichten-, Raum-, Privat-, Alle-, Weltweit-, Karten-, Monitor-, MH- und Wetterfunktionen bleiben unverändert.

## v0.3.64

- Alle-Scrollfix

## v0.3.63 – Sprache, Chat-Farben, Kontextmenü und Stabilität

- Projektversion auf **0.3.63** erhöht.
- Vollständige sichtbare Deutsch-/English-Umschaltung für die aktuelle Benutzeroberfläche ergänzt und dokumentiert.
- Spracheinstellung wird in `~/.MeshCom/settings.ini` gespeichert und beim Neustart wieder geladen.
- Dynamische Raum-Tabs werden korrekt als **All / Room …** bzw. **Alle / Raum …** angezeigt.
- Wetteranzeige einschließlich Temperatur, Luftfeuchte, QFE und QNH an die gewählte Sprache angepasst.
- Fehler bei wiederholtem Umschalten der Temperaturbezeichnung (`Temperatureee…`) behoben.
- Qt-Kontextmenü der Eingabefelder für Deutsch und English berücksichtigt.
- Chat-Farben dokumentiert: gemeinsamer Hintergrund für alle Chat-Ansichten, Schriftfarbe nur für „Alle“, Standard schwarz/weiß.
- Integrierte **Hilfe → Anleitung** auf den Funktionsstand v0.3.63 aktualisiert.
- Neue PDF-Benutzeranleitung `docs/MeshCom-Guru_Anleitung_v0.3.63.pdf` erstellt.
- Beenden stabilisiert: UDP-Listener wird sauber heruntergefahren und konkurrierende `closeEvent()`-Definitionen bereinigt.
- Sendererkennung für **Raum- und Privatnachrichten** korrigiert: Bei weitergeleiteten Nachrichten wird der ursprüngliche Absender verwendet; ein Relay-/Weiterleitungs-Rufzeichen wird nicht fälschlich als eigener Sender dargestellt.
- Chat-Bubbles bei einer oder wenigen Nachrichten am **unteren Rand** des Chatbereichs ausgerichtet.
- Bei längeren Chats bleibt das normale Scrollverhalten erhalten; manuelles Hochscrollen wird nicht durch neue Nachrichten zurückgesetzt.
- Bubble-Layout und Scrollbereich gezielt stabilisiert, ohne Wetter-, Karten-, Nachrichten- oder Senderlogik unnötig zu verändern.
- Die bekannten Qt-/Vulkan-/AT-SPI-Hinweise beim Start sind keine Programmfunktionen und wurden nicht künstlich unterdrückt.
- Bestehende Chat-, Privat-, Alle-, Karten-, Monitor-, MH- und Wetterfunktionen bleiben erhalten.


## v0.3.62 – Dokumentation, Anleitung und Release-Stand aktualisiert

- Projektversion auf **0.3.62** erhöht.
- Integrierte **Hilfe → Anleitung** vollständig auf den aktuellen Funktionsstand gebracht.
- Neue PDF-Benutzeranleitung für v0.3.62 erstellt.
- Dokumentation zu Nachrichten, Raum-Chats, Privat-Chats und Sendestatus aktualisiert.
- Dokumentation zu **⏳ Sanduhr / ✓✓ Empfänger-ACK** im Privat-Chat ergänzt.
- Dokumentation zu **⚡ Schnelltexten** und **😊 Emojis** ergänzt.
- Dokumentation zu **📡 Monitor** und **📋 MH** einschließlich UDP-Port 1799 aktualisiert.
- Dokumentation zu Karte, Positionsdaten, Wetter, Sound, Theme und Node Info aktualisiert.
- Persönliche Einstellungen eindeutig als `~/.MeshCom/settings.ini` dokumentiert.
- Debian-Installation nach `/usr/share/MeshCom` dokumentiert.
- Veraltete interne Analyse-/Hinweisdateien nicht in den Release-Stand übernommen.

## v0.3.61 – Einheitliche Chat-Bubbles für Raum-Tabs

- Normale Raum-Tabs verwenden dieselbe Bubble-Anordnung wie der Privat-Chat.
- Eigene Nachrichten werden rechts in Grün dargestellt.
- Empfangene Nachrichten werden links in Blau dargestellt.
- Kompakte `CALLSIGN>RAUM`-Antworten des MeshCom-WebService werden korrekt zerlegt.
- Der Tab „Alle“ bleibt unverändert.
- Bestehende Nachrichten-, Karten-, Monitor-, MH- und Wetterfunktionen bleiben erhalten.

## v0.3.60 – Schnelltexte, Sendebestätigung, Monitor, MH und Chat-Bubbles

- Schnelltexte mit Einfügen, Bearbeiten, Hinzufügen und Löschen.
- Persönliche Schnelltexte werden gespeichert.
- Sendestatus mit ⏳, ✓ und ✓✓.
- Echo-/ACK-Auswertung.
- Neuer Monitor mit Filtern ALLE / MSG / POS / TEL / ACK, Suche, Pause, Auto-Scroll und Leeren.
- Monitor-Details für Zeit, Pakettyp, Von, Nach, RSSI, SNR und weitere Paketinformationen.
- POS-, TEL- und ACK-Auswertung.
- Neuer MH-Tab mit Rufzeichen, Entfernung, RSSI, SNR, Batterie und letztem Empfang.
- Chat-Bubbles.
- Persönliche Einstellungen unter `~/.MeshCom/settings.ini`.

## v0.3.59 – Emoji-Unterstützung

- Emoji-Picker neben dem Nachrichtenfeld.
- Einfügen an der Cursorposition.
- Vergrößerte Emoji-Auswahl.
- 149-Zeichen-Limit bleibt aktiv.

## v0.3.58 – Wetterraum, Raumfilter und Entfernungsanzeige

- Wetterdaten können im aktuellen Raum gesendet werden.
- Raumfilter korrigiert.
- Entfernung zu anderen Kartenstationen wird angezeigt.

## v0.3.57 – Nachrichtenstabilität und saubere Benutzereinstellungen

- Nachrichten bleiben während der Sitzung erhalten.
- Chronologische Darstellung und Dublettenvermeidung verbessert.
- Persönliche Einstellungen nach `~/.MeshCom/settings.ini` verlagert.
- Neutrale Standardwerte ohne persönliche Vorgaben.

## v0.3.56 – Wetterdaten, Kartenansicht und Release

- WX-Testfunktion mit Temperatur, Luftfeuchte, QFE und QNH.
- OSM-/Leaflet-Kartenansicht verbessert.
- Node-Info-Seitenleiste verbessert.
- GitHub- und Debian-Release-Struktur eingeführt.

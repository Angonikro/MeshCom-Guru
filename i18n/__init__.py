import json
import os
import re

_language = "de"
_SUPPORTED_LANGUAGES = ("de", "en", "it", "nl", "fr")
_catalogs = {}
_base = os.path.dirname(__file__)
for _lang in ("de", "en", "it", "nl", "fr"):
    try:
        with open(os.path.join(_base, _lang + ".json"), "r", encoding="utf-8") as _f:
            _catalogs[_lang] = json.load(_f)
    except Exception:
        _catalogs[_lang] = {}

# Load the additional UI language catalogs.
for _lang in ("it", "nl", "fr"):
    try:
        with open(os.path.join(_base, _lang + ".json"), "r", encoding="utf-8") as _f:
            _catalogs[_lang].update(json.load(_f))
    except Exception:
        pass

# Static UI translations. Runtime/user data (messages, callsigns, room numbers,
# weather values, etc.) is deliberately not translated here.
_UI = {
    "Datei": "File",
    "Einstellungen": "Settings",
    "Theme": "Theme",
    "Hilfe": "Help",
    "Einstellungen speichern": "Save settings",
    "Nachrichten aktualisieren": "Refresh messages",
    "Beenden": "Exit",
    "Sprache / Language …": "Language / Sprache …",
    "Sound-Einstellungen": "Sound settings",
    "Chat-Farben …": "Chat colors …",
    "Wetterdaten": "Weather data",
    "Dunkel": "Dark",
    "Hell": "Light",
    "Anleitung": "User guide",
    "Info": "About",
    "Hotspot IP": "Hotspot IP",
    "Raum / Ziel": "Room / Target",
    "Eigene Station / GPS": "Own station / GPS",
    "Raumfilter aktiv": "Room filter active",
    "Nachrichtenfilter – bis zu 5 Räume": "Message filter – up to 5 rooms",
    "Filter speichern": "Save filter",
    "Wetterdaten": "Weather data",
    "Stadt:": "City:",
    "Stadtname, z. B. Bielefeld": "City name, e.g. Bielefeld",
    "Wetter aktualisieren": "Refresh weather",
    "Wetter senden": "Send weather",
    "Warte auf WX-Information …": "Waiting for WX information …",
    "Karte": "Map",
    "📡 Monitor": "📡 Monitor",
    "📋 MH": "📋 MH",
    "Nachricht:": "Message:",
    "⚡ Schnelltexte": "⚡ Quick texts",
    "Senden": "Send",
    "Aktualisieren": "Refresh",
    "Leeren": "Clear",
    "Filter:": "Filter:",
    "Suchen …": "Search …",
    "Auto-Scroll": "Auto-scroll",
    "Information": "Information",
    "Zeit": "Time",
    "Typ": "Type",
    "Von": "From",
    "Nach": "To",
    "Rufzeichen": "Callsign",
    "Entfernung": "Distance",
    "Batterie": "Battery",
    "Zuletzt gehört": "Last heard",
    "Node Info aufrufen": "Open Node Info",
    "Emoji einfügen": "Insert emoji",
    "Maximal 149 Zeichen": "Maximum 149 characters",
    "Schnelltext auswählen oder bearbeiten": "Select or edit quick text",
    "Schnelltexte bearbeiten": "Edit quick texts",
    "Schnelltext eingeben …": "Enter quick text …",
    "Einfügen": "Insert",
    "Löschen": "Delete",
    "＋ Schnelltext hinzufügen": "＋ Add quick text",
    "Schnelltexte hier bearbeiten. Mit „Einfügen“ wird der Text nur ins Nachrichtenfeld übernommen – nicht automatisch gesendet.": "Edit quick texts here. “Insert” only puts the text into the message field – it is not sent automatically.",
    "Chat-Farben": "Chat colors",
    "Chat-Hintergrundfarbe": "Chat background color",
    "Chat-Schriftfarbe": "Chat text color",
    "Chat-Hintergrund:": "Chat background:",
    "Schriftfarbe für „Alle“:": "Text color for “All”:",
    "🎨 Farbe auswählen …": "🎨 Choose color …",
    "✏️ Farbe auswählen …": "✏️ Choose color …",
    "🔄 Standard wiederherstellen": "🔄 Restore defaults",
    "Gemeinsame Farben für alle Räume und Chat-Ansichten:": "Shared colors for all rooms and chat views:",
    "OK": "OK",
    "Abbrechen": "Cancel",
    "Undo": "Rückgängig",
    "Redo": "Wiederholen",
    "Cut": "Ausschneiden",
    "Copy": "Kopieren",
    "Paste": "Einfügen",
    "Delete": "Löschen",
    "Select All": "Alles auswählen",
    "Schließen": "Close",
    "Testen": "Test",
    "Einstellungen gespeichert": "Settings saved",
    # v0.3.68 – Verbindungssteuerung und Statistik
    "Verbinden": "Connect",
    "Trennen": "Disconnect",
    "🔗 Verbinden": "🔗 Connect",
    "⛓️ Trennen": "⛓️ Disconnect",
    "Mit dem MeshCom-WebService verbinden": "Connect to the MeshCom WebService",
    "Verbindung zum MeshCom-WebService trennen": "Disconnect from the MeshCom WebService",
    "ONLINE  |  seit": "ONLINE  |  since",
    "OFFLINE  |  keine Verbindung": "OFFLINE  |  no connection",
    "Verbinde mit MeshCom-WebService …": "Connecting to MeshCom WebService …",
    "Mit MeshCom-WebService verbunden": "Connected to MeshCom WebService",
    "Vom MeshCom-WebService getrennt": "Disconnected from MeshCom WebService",
    "Verbindung fehlgeschlagen: ": "Connection failed: ",
    "Bitte zuerst mit dem MeshCom-WebService verbinden": "Please connect to the MeshCom WebService first",
    "📊 MeshCom-Guru Statistik": "📊 MeshCom-Guru Statistics",
    "📊 Statistik": "📊 Statistics",
    "Nachrichten:": "Messages:",
    "Nodes:": "Nodes:",
    "Positionen:": "Positions:",
    "Privatnachrichten:": "Private messages:",
    "Monitor-Einträge:": "Monitor entries:",
    "Nachrichten nach Raum:": "Messages by room:",
    "noch keine Daten": "no data yet",
    "Fehler: Keine Hotspot-IP eingetragen": "Error: No hotspot IP entered",
    "Fehler: Ungültige eigene Koordinaten": "Error: Invalid own coordinates",
    "Keine Nachricht eingegeben": "No message entered",
    "Nachricht darf maximal 149 Zeichen lang sein": "Message may be at most 149 characters long",
    "Keine Wetterdaten vorhanden – zuerst Wetter aktualisieren": "No weather data available – refresh weather first",
    "Bitte zuerst einen Stadtnamen eingeben": "Please enter a city name first",
    "Wettermeldung ist länger als 149 Zeichen": "Weather message is longer than 149 characters",
    "Speichern": "Save",
    "Soundtreiber:": "Sound driver:",
    "Automatisch": "Automatic",
    "Qt Multimedia": "Qt Multimedia",
    "System-Beep": "System beep",
    "Eigener Sound:": "Custom sound:",
    "Datei wählen …": "Choose file …",
    "leer = mitgelieferten Signalton verwenden": "empty = use the bundled notification sound",
    "Lautstärke:": "Volume:",
    "Wetterdaten an": "Weather data to",
    "Wetterdaten-Fenster ein- oder ausblenden": "Show or hide the weather data panel",
    "Über MeshCom-Guru": "About MeshCom-Guru",
    "Node Information": "Node Information",
    "Emoji": "Emoji",
    "Alle": "All",
    "Bereit": "Ready",
    "Keine Nachrichten.": "No messages.",
    "Wetterdaten": "Weather data",
    "Position": "Position",
    "Firmware": "Firmware",
    "Höhe": "Altitude",
    "Breite": "Latitude",
    "Länge": "Longitude",
    "Temperatur": "Temperature",
    "Luftfeuchte": "Humidity",
    "Batteriekapazität": "Battery capacity",
    "Wetterdaten konnten nicht gesendet werden": "Weather data could not be sent",
    "▶ Weiter": "▶ Resume",
    "⏸ Pause": "⏸ Pause",
    "Station(en)": "Station(s)",
    "Letzter Sendeauftrag: noch keiner": "Last send request: none yet",
    "Nachricht eingeben ...": "Enter message ...",
    "Nachricht eingeben …": "Enter message …",
    "Breitengrad, z. B. 51.93": "Latitude, e.g. 51.93",
    "Längengrad, z. B. 8.88": "Longitude, e.g. 8.88",
    "eigenes Rufzeichen, z. B. DL9ABC-1": "own callsign, e.g. DL9ABC-1",
    "Raum oder Ziel, z. B. 262 oder DL9ABC-1": "room or target, e.g. 262 or DL9ABC-1",
    "Letzter Sendeauftrag: noch keiner": "Last send request: none yet",
    "Letzter Sendeauftrag": "Last send request",
    "Sendeauftrag an den Hotspot übertragen – warte auf Node-Rückmeldung": "Send request transmitted to hotspot – waiting for node response",
    "Nachrichten aktualisiert – alle Räume": "Messages refreshed – all rooms",
    "Nachrichten aktualisiert – Filter: ": "Messages refreshed – Filter: ",
    "keine Räume": "no rooms",
    "Abruf fehlgeschlagen: ": "Request failed: ",
    "Warte auf WX-Information …": "Waiting for WX information …",
    "WX-Information wird geladen …": "Loading WX information …",
    "WX-Information erfolgreich aus dem MeshCom-WebService gelesen": "WX information successfully read from the MeshCom WebService",
    "Keine Wetterwerte in der WX-Information gefunden": "No weather values found in the WX information",
    "Keine vollständigen WX-Werte in der Antwort gefunden.": "No complete WX values found in the response.",
    "Keine Hotspot-IP eingetragen": "No hotspot IP entered",
    "Wetterdaten ohne Raumangabe an den Hotspot übertragen": "Weather data transmitted to the hotspot without a room",
    "Wetterdaten an ": "Weather data transmitted to ",
    " übertragen": " transmitted",
    "Wetterdaten konnten nicht gesendet werden: ": "Weather data could not be sent: ",
    "Letzter Wetter-Sendeauftrag": "Last weather send request",
    "Fehler: ": "Error: ",
    "Node Information im Standard-Browser geöffnet": "Node information opened in the default browser",
    "Node Info konnte nicht geöffnet werden: ": "Node Info could not be opened: ",
    "Node Information geladen": "Node information loaded",
    "Node Information konnte nicht geladen werden": "Node information could not be loaded",
    "Privatchat geöffnet: ": "Private chat opened: ",
    "Privatchat geschlossen: ": "Private chat closed: ",
    "Senden fehlgeschlagen: ": "Sending failed: ",
    "Letzter Sendeauftrag: FEHLER – ": "Last send request: ERROR – ",
    "Position empfangen: ": "Position received: ",
    "Theme gespeichert: ": "Theme saved: ",
    "Filter gespeichert: ": "Filter saved: ",
    "Wetterdaten": "Weather data",
    "Temperatur:": "Temperature:",
    "Luftfeuchte:": "Humidity:",
    "QFE:": "QFE:",
    "QNH:": "QNH:",
    "Breite:": "Latitude:",
    "Länge:": "Longitude:",
    "Höhe:": "Altitude:",
    "Batteriekapazität:": "Battery capacity:",
    "Eigene Station": "Own station",
    "Zuletzt gehört:": "Last heard:",
    "Entfernung:": "Distance:",
    "Nachricht:": "Message:",
    "Alle": "All",
    "Raum": "Room",
    "Keine Nachrichten.": "No messages.",
    "Maximale Länge erreicht: 149 Zeichen": "Maximum length reached: 149 characters",
    "Noch ": "Still ",
    " Zeichen frei": " characters left",
    "0 angezeigt · 0 gespeichert": "0 shown · 0 saved",
    "Sound-Einstellungen gespeichert": "Sound settings saved",
    "Akustisches Signal bei neuen Nachrichten": "Sound notification for new messages",
    "Bei neuen Nachrichten in einem nicht aktiven Tab wird einmalig ein Signal abgespielt. Der Ton wird nicht bei jedem Aktualisieren wiederholt.": "A notification sound is played once for new messages in an inactive tab. The sound is not repeated on every refresh.",
    "Sounddatei auswählen": "Choose sound file",
    "WAV-Dateien (*.wav);;Alle Dateien (*)": "WAV files (*.wav);;All files (*)",
    "Kartenansicht benötigt PySide6-WebEngine.\nBitte requirements.txt erneut installieren.": "Map view requires PySide6-WebEngine.\nPlease install requirements.txt again.",
}

# Complete multilingual coverage for UI labels and runtime status text.
EXTRA_UI_TRANSLATIONS = {'Node Information des verbundenen MeshCom-WebService anzeigen': 'Show Node Information of the connected MeshCom WebService', 'Raum {i + 1}': 'Room {i + 1}', '0 angezeigt · 0 gespeichert': '0 displayed · 0 stored', 'Verbindung verloren – verbinde erneut …': 'Connection lost – reconnecting …', 'Verbindung verloren – neuer Versuch: ': 'Connection lost – retry: ', 'Verbindung verloren – verbinde erneut … (': 'Connection lost – reconnecting … (', 'Theme gespeichert: ': 'Theme saved: ', 'Letzter Wetter-Sendeauftrag ': 'Last weather send request ', 'Letzter Sendeauftrag ': 'Last send request ', 'Node Info konnte nicht geöffnet werden: ': 'Node Info could not be opened: ', 'Privatchat geöffnet: ': 'Private chat opened: ', 'Privatchat geschlossen: ': 'Private chat closed: ', 'Nachrichten aktualisiert – Filter: ': 'Messages refreshed – Filter: ', 'Senden fehlgeschlagen: ': 'Sending failed: ', 'Abruf fehlgeschlagen: ': 'Request failed: ', 'Position empfangen: ': 'Position received: ', 'Filter gespeichert: ': 'Filter saved: ', 'Einstellungen gespeichert': 'Settings saved', 'Sound-Einstellungen gespeichert': 'Sound settings saved', 'Emoji passt nicht mehr in die 149 Zeichen': 'Emoji no longer fits within the 149-character limit', 'Nachricht eingeben …': 'Enter message …', 'Nachricht eingeben ...': 'Enter message ...', 'Suchen …': 'Search …', 'Schnelltexte bearbeiten': 'Edit quick texts', 'Schnelltext eingeben …': 'Enter quick text …', 'leer = mitgelieferten Signalton verwenden': 'empty = use the bundled notification sound', 'Chat-Farben': 'Chat colors', 'Über MeshCom-Guru': 'About MeshCom-Guru', 'Sound-Einstellungen': 'Sound settings', 'Node Information': 'Node Information', 'Wetterdaten': 'Weather data', 'Kartenansicht benötigt PySide6-WebEngine.\nBitte requirements.txt erneut installieren.': 'Map view requires PySide6-WebEngine.\nPlease install requirements.txt again.', 'Breitengrad, z. B. 51.93': 'Latitude, e.g. 51.93', 'Längengrad, z. B. 8.88': 'Longitude, e.g. 8.88', 'eigenes Rufzeichen, z. B. DL9ABC-1': 'own callsign, e.g. DL9ABC-1', 'Raum oder Ziel, z. B. 262 oder DL9ABC-1': 'room or target, e.g. 262 or DL9ABC-1'}
_UI.update(EXTRA_UI_TRANSLATIONS)

_REVERSE = {v: k for k, v in _UI.items()}

def set_language(language):
    global _language
    _language = language if language in _SUPPORTED_LANGUAGES else "de"

def get_language():
    return _language

def _translated(key, language=None):
    lang = language or _language
    if lang == "de":
        return _catalogs.get("de", {}).get(key, key) if key in _catalogs.get("de", {}) else key
    if lang == "en" and key in _UI:
        return _UI[key]
    if lang in _catalogs and key in _catalogs[lang]:
        return _catalogs[lang][key]
    if key in _UI:
        return _UI[key]
    return _catalogs.get("en", {}).get(key, key)

def tr(key, fallback=None):
    value = _translated(key)
    if value == key and fallback is not None:
        return fallback
    return value

def ui_text(text):
    """Translate static UI text and known runtime status phrases."""
    if text is None:
        return text

    # Direct German source text.
    if text in _UI or text in _catalogs.get(_language, {}):
        return _translated(text)

    # Also recognize an already translated phrase and map it back to German.
    for lang in _SUPPORTED_LANGUAGES:
        if lang == "de":
            continue
        for de_key, translated in _catalogs.get(lang, {}).items():
            if text == translated:
                return _translated(de_key)
        if text in _UI.values() and _language != "en":
            for de_key, en_value in _UI.items():
                if text == en_value:
                    return _translated(de_key)

    if isinstance(text, str):
        def replace_ui_phrase(value, source, target):
            pattern = re.escape(source)
            if source and source[0].isalnum():
                pattern = r"(?<!\\w)" + pattern
            if source and source[-1].isalnum():
                pattern = pattern + r"(?!\\w)"
            return re.sub(pattern, lambda _m: target, value)

        # Always replace from German source phrases to the selected language.
        # This keeps dynamic values such as callsigns, rooms and timestamps intact.
        replacements = []
        for de_key in _UI:
            target = _translated(de_key)
            if target != de_key:
                replacements.append((de_key, target))
        for de_key in _catalogs.get("de", {}):
            target = _translated(de_key)
            if target != de_key:
                replacements.append((de_key, target))
        for de, target in sorted(replacements, key=lambda kv: len(kv[0]), reverse=True):
            text = replace_ui_phrase(text, de, target)
        return text
    return text

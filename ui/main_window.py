import configparser
import hashlib
import html
import re
import os
import platform
import subprocess
import json
import socket
import threading
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, QUrl, Signal
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except Exception:
    QWebEngineView = None
try:
    from PySide6.QtMultimedia import QSoundEffect
except Exception:
    QSoundEffect = None
from PySide6.QtGui import QAction, QTextCursor, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSlider,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.meshcom import MeshCom
from core.settings import SETTINGS_FILE, load_settings
from version import VERSION


CALLSIGN_RE = re.compile(r"\b[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?\b", re.IGNORECASE)
ROOM_RE = re.compile(r"(?:>|&gt;)\s*(\d{1,8})\b")
TARGET_RE = re.compile(r"(?:>|&gt;)\s*([A-Z0-9]{1,6}(?:-[0-9]{1,2})?)\b", re.IGNORECASE)
OWN_CALLSIGN = ""  # eigenes Rufzeichen kommt ausschließlich aus settings.ini


DIRECT_HEADER_RE = re.compile(
    r"(?P<left>(?:[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?\s*,?\s*)+)"
    r">\s*(?P<right>[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?)\b",
    re.IGNORECASE,
)





def _meshcom_extract_coordinates(raw):
    """Extract latitude/longitude from the actual received node text."""
    from html import unescape
    s = unescape(str(raw or ""))
    s = re.sub(r"<[^>]*>", " ", s)
    s = " ".join(s.split())
    n = r"[-+]?\d+(?:[.,]\d+)?"

    # German/English labelled coordinates.
    a = re.search(rf"(?:breitengrad|latitude|lat)\s*[:=]?\s*({n})\s*([NS])?", s, re.I)
    b = re.search(rf"(?:längengrad|laengengrad|longitude|lon)\s*[:=]?\s*({n})\s*([EW])?", s, re.I)
    if a and b:
        lat = float(a.group(1).replace(",", "."))
        lon = float(b.group(1).replace(",", "."))
        if a.group(2) and a.group(2).upper() == "S":
            lat = -abs(lat)
        if b.group(2) and b.group(2).upper() == "W":
            lon = -abs(lon)
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon

    # 52.1234 N / 8.1234 E
    m = re.search(rf"({n})\s*([NS])\s*[,;/ ]+\s*({n})\s*([EW])", s, re.I)
    if m:
        lat = float(m.group(1).replace(",", "."))
        lon = float(m.group(3).replace(",", "."))
        if m.group(2).upper() == "S":
            lat = -abs(lat)
        if m.group(4).upper() == "W":
            lon = -abs(lon)
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon

    # GPS/Position: 52.1234, 8.1234
    m = re.search(rf"(?:gps|position|pos|koordinaten?)\s*[:=]?\s*({n})\s*[,;]\s*({n})", s, re.I)
    if m:
        lat = float(m.group(1).replace(",", "."))
        lon = float(m.group(2).replace(",", "."))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon

    return None


class ChatView(QTextBrowser):
    callsignClicked = Signal(str)





    def _trace_and_place_node_coordinate(self, lat, lon, label="Node"):
        """Place a known coordinate using the existing map implementation."""
        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            return False
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return False

        # First use an existing Python marker function, if present.
        for name in (
            "add_node_marker", "add_map_marker", "_add_map_marker",
            "update_map_marker", "_update_map_marker", "set_node_position"
        ):
            fn = getattr(self, name, None)
            if callable(fn):
                for args in ((lat, lon, label), (lat, lon), (label, lat, lon)):
                    try:
                        fn(*args)
                        return True
                    except TypeError:
                        continue
                    except Exception:
                        continue

        # Then use a QWebEngineView if the map is embedded that way.
        js = (
            "(function(){"
            "var lat=" + repr(lat) + ",lon=" + repr(lon) + ",label=" + repr(str(label)) + ";"
            "if(window.addMeshComMarker) return window.addMeshComMarker(lat,lon,label);"
            "if(window.setNodeMarker) return window.setNodeMarker(lat,lon,label);"
            "return false;"
            "})()"
        )
        for attr in (
            "map_view", "map_webview", "web_view", "webview",
            "mapWidget", "browser", "leaflet_view"
        ):
            view = getattr(self, attr, None)
            if view is not None and hasattr(view, "page"):
                try:
                    view.page().runJavaScript(js)
                    return True
                except Exception:
                    continue

        # Keep the exact position for the existing refresh cycle.
        if not hasattr(self, "_pending_map_coordinates"):
            self._pending_map_coordinates = {}
        self._pending_map_coordinates[str(label)] = (lat, lon)
        return False


    def _map_coordinates_from_node_info(self, node_info, label="Node"):
        """Use coordinates already returned by Node Info for the map."""
        if node_info is None:
            return False

        def get(obj, names):
            if isinstance(obj, dict):
                for name in names:
                    if name in obj and obj[name] not in (None, ""):
                        return obj[name]
            for name in names:
                try:
                    value = getattr(obj, name)
                except Exception:
                    continue
                if value not in (None, ""):
                    return value
            return None

        lat = get(node_info, ("latitude", "lat", "breitengrad", "gps_lat", "gpsLatitude"))
        lon = get(node_info, ("longitude", "lon", "längengrad", "gps_lon", "gpsLongitude"))

        try:
            lat = float(str(lat).replace(",", "."))
            lon = float(str(lon).replace(",", "."))
        except (TypeError, ValueError):
            return False

        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return False

        # Prefer the project's existing map implementation.
        for name in (
            "add_node_marker", "add_map_marker", "_add_map_marker",
            "update_map_marker", "_update_map_marker",
        ):
            fn = getattr(self, name, None)
            if callable(fn):
                for args in ((lat, lon, label), (lat, lon), (label, lat, lon)):
                    try:
                        fn(*args)
                        return True
                    except TypeError:
                        continue
                    except Exception:
                        break

        # Store the exact Node Info coordinates for the map refresh.
        if not hasattr(self, "_node_info_coordinates"):
            self._node_info_coordinates = {}
        self._node_info_coordinates[str(label)] = (lat, lon)
        return True


    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)
        self.anchorClicked.connect(self._anchor_clicked)
        self.setPlaceholderText("MeshCom-Nachrichten werden hier angezeigt …")

    def _anchor_clicked(self, url: QUrl):
        value = url.toString().strip()
        if value.startswith("meshcom://call/"):
            call = value.rsplit("/", 1)[-1]
            self.callsignClicked.emit(call)
        elif value.startswith(("http://", "https://")):
            QDesktopServices.openUrl(QUrl(value))

    def scroll_to_bottom(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()


class MainWindow(QMainWindow):
    udpPacketReceived = Signal(dict)
    weatherUpdated = Signal(dict)
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"MeshCom-Guru v{VERSION}")
        self.resize(1100, 930)
        self.setMinimumSize(900, 930)

        settings = load_settings()
        self.current_theme = settings.get("theme", "dark").strip().lower()
        if self.current_theme not in {"light", "dark"}:
            self.current_theme = "dark"
        self.sound_enabled = settings.get("sound_enabled", "1") == "1"
        self.sound_driver = settings.get("sound_driver", "auto").strip().lower() or "auto"
        self.sound_volume = max(0, min(100, int(settings.get("sound_volume", "70") or 70)))
        self.sound_file = settings.get("sound_file", "").strip()
        self.weather_enabled = settings.get("weather_enabled", "0") == "1"
        self._weather_fetch_in_progress = False
        self.weather_data = {}
        self._sound_effect = None
        self._prepare_sound()
        self.mesh = MeshCom(settings.get("ip", ""))
        self.refresh_in_progress = False
        self.last_sent = None
        self.last_sent_time = None
        # Merkt die zuletzt von diesem Client gesendete Direktnachricht.
        # Der Node liefert das eigene Echo ebenfalls zurück; dieses Echo darf
        # keinen neuen Privat-Tab für das eigene Rufzeichen erzeugen.
        self.last_private_sent = None
        # Nur für den Gesamtstrom „Alle“: eigene Sendungen lokal merken.
        self.local_all_messages = []
        self.tab_keys = {}
        self.tab_hashes = {}
        self.unread = set()
        # Privat-Tabs bleiben geöffnet, bis der Benutzer sie ausdrücklich schließt.
        # Geschlossene Tabs werden nicht bei jedem Nachrichten-Refresh erneut geöffnet.
        self.closed_private = {}
        self.station_positions = {}
        # Zeitpunkt, zu dem eine Station zuletzt mit Positionsdaten gehört wurde.
        self.station_last_heard = {}
        self.station_last_heard_signature = {}
        self.udp_position_blocks = []
        self.udp_socket = None
        self.udp_thread = None
        self.udp_stop = threading.Event()
        self.udp_enabled = True
        self.udp_status = "UDP: wird gestartet …"
        self.udpPacketReceived.connect(self._handle_udp_packet)
        self.own_callsign = settings.get("own_callsign", "").strip().upper()
        try:
            self.own_lat = float(settings.get("own_lat", ""))
            self.own_lon = float(settings.get("own_lon", ""))
        except (TypeError, ValueError):
            self.own_lat = None
            self.own_lon = None

        self._build_menu()
        self._build_ui(settings)
        self._apply_theme(self.current_theme)
        self._load_filter_fields(settings)
        self._set_weather_panel_visible(self.weather_enabled)
        self.weatherUpdated.connect(self._apply_weather_result)
        # Wenn Wetterdaten dauerhaft aktiviert sind, beim Start automatisch
        # eine frische WX-Information vom MeshCom-Node laden. Die kurze
        # Verzögerung stellt sicher, dass das Hauptfenster und die Verbindung
        # vollständig initialisiert sind.
        if self.weather_enabled:
            QTimer.singleShot(1500, self._refresh_weather)

        # Eigenständiger MeshCom-Positions-/Status-Empfang direkt per UDP.
        self._start_udp_listener(1799)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_messages)
        self.timer.start(5000)

        # Uhr und Datum auf der Oberfläche aktuell halten.
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()

        # Der Nachrichtenstrom wird über den funktionierenden HTTP-WebService
        # abgerufen. Positionskarten sind Bestandteil desselben HTML-Responses
        # und werden dort direkt aus den message-row/message-bubble-Blöcken
        QTimer.singleShot(200, self.update_messages)

    # ---------- MeshCom UDP-Schnittstelle ----------
    def _start_udp_listener(self, port=1799):
        def worker():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                if hasattr(socket, "SO_REUSEPORT"):
                    try:
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                    except OSError:
                        pass
                sock.bind(("0.0.0.0", port))
                sock.settimeout(1.0)
                self.udp_socket = sock
                self.udpPacketReceived.emit({"_status": f"UDP 1799: aktiv"})
                while not self.udp_stop.is_set():
                    try:
                        data, _addr = sock.recvfrom(65535)
                    except socket.timeout:
                        continue
                    except OSError:
                        break
                    try:
                        text = data.decode("utf-8", errors="replace").strip()
                        if not text:
                            continue
                        packet = json.loads(text)
                        if isinstance(packet, dict):
                            self.udpPacketReceived.emit(packet)
                    except (UnicodeError, json.JSONDecodeError):
                        continue
            except OSError as exc:
                self.udpPacketReceived.emit({"_status": f"UDP 1799 nicht verfügbar: {exc}"})
            finally:
                try:
                    sock.close()
                except Exception:
                    pass
                self.udp_socket = None

        self.udp_thread = threading.Thread(target=worker, name="MeshCom-UDP", daemon=True)
        self.udp_thread.start()

    @staticmethod
    def _udp_callsign(src):
        value = str(src or "").strip().upper()
        for part in re.split(r"[,/ >]+", value):
            if CALLSIGN_RE.fullmatch(part):
                return part
        match = CALLSIGN_RE.search(value)
        return match.group(0).upper() if match else ""

    @staticmethod
    def _udp_coordinate(packet):
        try:
            lat_value = packet.get("lat", packet.get("latitude", ""))
            lon_value = packet.get("long", packet.get("lon", packet.get("longitude", "")))
            lat = float(str(lat_value).replace(",", ".").strip())
            lon = float(str(lon_value).replace(",", ".").strip())
        except (TypeError, ValueError):
            return None
        lat_dir = str(packet.get("lat_dir", "N")).upper().strip()
        lon_dir = str(packet.get("long_dir", packet.get("lon_dir", "E"))).upper().strip()
        if lat_dir == "S":
            lat = -abs(lat)
        elif lat_dir == "N":
            lat = abs(lat)
        if lon_dir == "W":
            lon = -abs(lon)
        elif lon_dir == "E":
            lon = abs(lon)
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon
        return None

    def _handle_udp_packet(self, packet):
        status = packet.get("_status") if isinstance(packet, dict) else None
        if status:
            self.udp_status = status
            return
        if not isinstance(packet, dict):
            return
        # Diagnose den direkten UDP-Empfang unabhängig von der Kartenanzeige.
        try:
            debug_file = Path(__file__).resolve().parent.parent / "data" / "udp_received.log"
            with debug_file.open("a", encoding="utf-8") as fh:
                fh.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + json.dumps(packet, ensure_ascii=False) + "\n")
        except Exception:
            pass
        ptype = str(packet.get("type", packet.get("packet_type", ""))).lower().strip()
        callsign = self._udp_callsign(packet.get("src", ""))
        coords = self._udp_coordinate(packet)
        if ptype in {"pos", "position", "gps"} and callsign and coords:
            self.station_positions[callsign] = coords
            self.station_last_heard[callsign.upper()] = datetime.now().strftime("%H:%M:%S")
            # POS-Paket zusätzlich als normale sichtbare Meldung führen.
            # Dadurch sieht man die Koordinaten nicht nur auf der Karte, sondern
            # auch im Tab „Alle“. Über msg_id wird dieselbe POS-Meldung nicht
            # mehrfach eingefügt.
            msg_id = str(packet.get("msg_id", "")).strip()
            signature = msg_id or f"{callsign}:{coords[0]:.6f}:{coords[1]:.6f}"
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            lat_dir = str(packet.get("lat_dir", "N")).upper()
            lon_dir = str(packet.get("long_dir", packet.get("lon_dir", "E"))).upper()
            alt = packet.get("alt")
            batt = packet.get("batt")
            extra = []
            if alt not in (None, ""):
                extra.append(f"Höhe: {html.escape(str(alt))} m")
            if batt not in (None, ""):
                extra.append(f"Batteriekapazität: {html.escape(str(batt))} %")
            extra_html = "<br>".join(extra)
            block = (
                '<div class="message meshcom-position" data-msgid="' + html.escape(signature) + '">'
                f'<div>MsgId: {html.escape(msg_id or "UDP-POS")} (udp)</div>'
                f'<div>Jetzt {stamp} Von: {html.escape(callsign)} Ziel: all</div>'
                f'<div><b>Breitengrad:</b> {coords[0]:.6f} {lat_dir}<br>'
                f'<b>Längengrad:</b> {coords[1]:.6f} {lon_dir}'
                + (f'<br>{extra_html}' if extra_html else '') + '</div></div>'
            )
            if not any(f'data-msgid="{html.escape(signature)}"' in b for b in self.udp_position_blocks):
                self.udp_position_blocks.append(block)
                self.udp_position_blocks = self.udp_position_blocks[-100:]
            self._update_map()
            self.status.setText(f"Position empfangen: {callsign} {coords[0]:.6f}, {coords[1]:.6f} | {self.udp_status}")
            return
        # Textpakete werden weiterhin über HTTP dargestellt; UDP dient hier
        # vor allem dazu, Positions-/Statuspakete in Echtzeit zu übernehmen.

    def closeEvent(self, event):
        self.udp_stop.set()
        if self.udp_socket is not None:
            try:
                self.udp_socket.close()
            except Exception:
                pass
        super().closeEvent(event)

    # ---------- UI ----------
    def _build_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Datei")

        save_action = QAction("Einstellungen speichern", self)
        save_action.triggered.connect(self.save_all_settings)
        file_menu.addAction(save_action)

        refresh_action = QAction("Nachrichten aktualisieren", self)
        refresh_action.triggered.connect(self.update_messages)
        file_menu.addAction(refresh_action)
        file_menu.addSeparator()

        exit_action = QAction("Beenden", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        settings_menu = menu_bar.addMenu("Einstellungen")
        sound_action = QAction("Sound-Einstellungen", self)
        sound_action.triggered.connect(self.open_sound_settings)
        settings_menu.addAction(sound_action)

        self.weather_action = QAction("Wetterdaten", self)
        self.weather_action.setCheckable(True)
        self.weather_action.setChecked(False)
        self.weather_action.setToolTip("Wetterdaten-Fenster ein- oder ausblenden")
        self.weather_action.toggled.connect(self._toggle_weather_panel)
        settings_menu.addAction(self.weather_action)

        theme_menu = menu_bar.addMenu("Theme")
        dark_action = QAction("Dunkel", self)
        dark_action.setCheckable(True)
        light_action = QAction("Hell", self)
        light_action.setCheckable(True)
        dark_action.triggered.connect(lambda: self.set_theme("dark"))
        light_action.triggered.connect(lambda: self.set_theme("light"))
        theme_menu.addAction(dark_action)
        theme_menu.addAction(light_action)
        self.dark_action = dark_action
        self.light_action = light_action
        self._sync_theme_actions()

        # Hilfe-Menü
        help_menu = menu_bar.addMenu("Hilfe")
        guide_action = QAction("Anleitung", self)
        guide_action.triggered.connect(self.open_help)
        help_menu.addAction(guide_action)

        info_action = QAction("Info", self)
        info_action.triggered.connect(self.open_about)
        help_menu.addAction(info_action)

    def _build_ui(self, settings):
        # Uhr/Datum oben rechts in der Oberfläche.
        self.datetime_label = QLabel()
        self.datetime_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.datetime_label.setMinimumWidth(190)
        self.datetime_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        top_row = QHBoxLayout()
        top_row.addStretch(1)
        top_row.addWidget(self.datetime_label)

        self.ip_input = QLineEdit(settings.get("ip", ""))
        self.target_input = QLineEdit(settings.get("target", ""))
        self.target_input.setPlaceholderText("Raum oder Ziel, z. B. 262 oder DL9ABC-1")

        form = QFormLayout()
        form.addRow("Hotspot IP", self.ip_input)
        form.addRow("Raum / Ziel", self.target_input)

        self.own_callsign_input = QLineEdit(settings.get("own_callsign", ""))
        self.own_callsign_input.setPlaceholderText("eigenes Rufzeichen, z. B. DL9ABC-1")
        self.own_lat_input = QLineEdit(settings.get("own_lat", ""))
        self.own_lat_input.setPlaceholderText("Breitengrad, z. B. 51.93")
        self.own_lon_input = QLineEdit(settings.get("own_lon", ""))
        self.own_lon_input.setPlaceholderText("Längengrad, z. B. 8.88")
        location_row = QHBoxLayout()
        location_row.addWidget(self.own_callsign_input)
        location_row.addWidget(self.own_lat_input)
        location_row.addWidget(self.own_lon_input)
        form.addRow("Eigene Station / GPS", location_row)

        self.save_button = QPushButton("Einstellungen speichern")
        self.save_button.clicked.connect(self.save_all_settings)
        self.node_info_button = QPushButton("Node Info aufrufen")
        self.node_info_button.setToolTip("Node Information des verbundenen MeshCom-WebService anzeigen")
        self.node_info_button.clicked.connect(self.open_node_info)

        self.filter_enabled = QCheckBox("Raumfilter aktiv")
        self.filter_enabled.setChecked(settings.get("filter_enabled", "0") == "1")
        self.filter_enabled.toggled.connect(self._filter_toggled)

        self.filter_inputs = []
        filter_row = QHBoxLayout()
        for i in range(5):
            field = QLineEdit()
            field.setPlaceholderText(f"Raum {i + 1}")
            field.setMaxLength(10)
            self.filter_inputs.append(field)
            filter_row.addWidget(field)
        self.filter_save_button = QPushButton("Filter speichern")
        self.filter_save_button.clicked.connect(self.save_filter_settings)
        filter_row.addWidget(self.filter_save_button)

        filter_box = QVBoxLayout()
        filter_box.addWidget(QLabel("Nachrichtenfilter – bis zu 5 Räume"))
        filter_box.addWidget(self.filter_enabled)
        filter_box.addLayout(filter_row)

        # ---------- Wetterdaten-Testfunktion ----------
        self.weather_panel = QWidget()
        weather_layout = QVBoxLayout(self.weather_panel)
        weather_layout.setContentsMargins(0, 4, 0, 4)
        weather_title = QLabel("Wetterdaten")
        weather_title.setStyleSheet("font-weight: 600;")
        weather_layout.addWidget(weather_title)

        weather_row = QHBoxLayout()
        weather_row.addWidget(QLabel("Stadt:"))
        self.weather_city_input = QLineEdit()
        self.weather_city_input.setPlaceholderText("Stadtname, z. B. Bielefeld")
        self.weather_city_input.setText(settings.get("weather_city", ""))
        weather_row.addWidget(self.weather_city_input, 1)
        self.weather_refresh_button = QPushButton("Wetter aktualisieren")
        self.weather_refresh_button.clicked.connect(self._refresh_weather)
        weather_row.addWidget(self.weather_refresh_button)
        self.weather_send_button = QPushButton("Wetter senden")
        self.weather_send_button.clicked.connect(self._send_weather)
        weather_row.addWidget(self.weather_send_button)
        weather_layout.addLayout(weather_row)

        self.weather_values_label = QLabel("Warte auf WX-Information …")
        self.weather_values_label.setWordWrap(True)
        weather_layout.addWidget(self.weather_values_label)
        self.weather_status_label = QLabel("")
        self.weather_status_label.setWordWrap(True)
        weather_layout.addWidget(self.weather_status_label)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._tab_changed)

        self.map_view = QWebEngineView() if QWebEngineView is not None else QLabel(
            "Kartenansicht benötigt PySide6-WebEngine.\nBitte requirements.txt erneut installieren."
        )
        # Die OSM-Karte soll deutlich höher sein: ca. 4 cm zusätzliche
        # Kartenhöhe auf typischen 96-DPI-Desktops (rund 150 Pixel).
        self.map_view.setMinimumHeight(300)
        self._map_ready = False
        self._map_pending_stations = []
        if QWebEngineView is not None:
            # setHtml() ist asynchron. Früher konnte _update_map() schon laufen,
            # bevor window.updateStations existierte. Dann gingen die Marker
            # stillschweigend verloren. Erst nach loadFinished darf JavaScript
            # die aktuellen Stationsdaten übernehmen.
            self.map_view.loadFinished.connect(self._map_load_finished)
            self.map_view.setHtml(self._map_html([]), QUrl("https://meshcom-guru.local/"))
        self.map_tab_index = self.tabs.addTab(self.map_view, "Karte")
        # Die Karte ist ein fester Tab und darf nicht geschlossen werden.
        self.tabs.tabBar().setTabButton(
            self.map_tab_index,
            self.tabs.tabBar().ButtonPosition.RightSide,
            None,
        )

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Nachricht eingeben …")
        self.message_input.setMaxLength(149)

        # Zeichenzähler für MeshCom-Nachrichten: maximal 149 Zeichen.
        self.message_counter = QLabel("0/149")
        self.message_counter.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.message_counter.setMinimumWidth(48)
        self.message_counter.setToolTip("Maximal 149 Zeichen")
        self.message_input.textChanged.connect(self._update_message_counter)

        self.send_button = QPushButton("Senden")
        self.update_button = QPushButton("Aktualisieren")
        self.send_button.clicked.connect(self.send)
        self.update_button.clicked.connect(self.update_messages)
        self.message_input.returnPressed.connect(self.send)

        buttons = QHBoxLayout()
        buttons.addWidget(self.send_button)
        buttons.addWidget(self.update_button)

        self.send_log = QLabel("Letzter Sendeauftrag: noch keiner")
        self.send_log.setWordWrap(True)
        self.status = QLabel("Bereit")
        self.status.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addLayout(top_row)
        layout.addLayout(form)
        settings_buttons = QHBoxLayout()
        settings_buttons.addWidget(self.save_button)
        settings_buttons.addWidget(self.node_info_button)
        layout.addLayout(settings_buttons)
        layout.addLayout(filter_box)
        layout.addWidget(self.weather_panel)
        layout.addWidget(self.tabs, 1)
        layout.addWidget(QLabel("Nachricht:"))

        message_row = QHBoxLayout()
        message_row.addWidget(self.message_input, 1)
        message_row.addWidget(self.message_counter)
        layout.addLayout(message_row)

        layout.addLayout(buttons)
        layout.addWidget(self.send_log)
        layout.addWidget(self.status)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

    def _update_message_counter(self, text):
        """Update the visible character counter for the 149-character limit."""
        self.message_counter.setText(f"{len(text)}/149")
        if len(text) >= 149:
            self.message_counter.setToolTip("Maximale Länge erreicht: 149 Zeichen")
        else:
            self.message_counter.setToolTip(f"Noch {149 - len(text)} Zeichen frei")

    def _load_filter_fields(self, settings):
        for i, field in enumerate(self.filter_inputs, 1):
            field.setText(settings.get(f"filter_room{i}", ""))
        self._ensure_room_tabs()

    def _update_clock(self):
        now = datetime.now()
        self.datetime_label.setText(now.strftime("%d.%m.%Y  |  %H:%M:%S"))

    # ---------- Theme ----------
    def _apply_theme(self, theme):
        # Reines UI-Styling: Nachrichten-, Tab-, Karten- und Sende-Logik
        # bleiben unverändert. Die Farben passen sich weiterhin dem
        # gespeicherten Hell-/Dunkelmodus an.
        if theme == "light":
            self.setStyleSheet(r"""
                QMainWindow { background: #eef2f6; }
                QWidget { background: #eef2f6; color: #202733; font-size: 10pt; }
                QLabel { background: transparent; color: #303947; }
                QLineEdit, QTextEdit, QTextBrowser {
                    background: #ffffff; color: #202733;
                    border: 1px solid #c7ced8; border-radius: 7px;
                    padding: 7px 9px; selection-background-color: #5b8def;
                }
                QLineEdit:focus, QTextEdit:focus, QTextBrowser:focus {
                    border: 2px solid #6d94df; padding: 6px 8px;
                }
                QPushButton {
                    background: #ffffff; color: #263142;
                    border: 1px solid #c5ccd6; border-radius: 7px;
                    padding: 7px 14px; min-height: 20px;
                }
                QPushButton:hover { background: #e9eff9; border-color: #7898d4; }
                QPushButton:pressed { background: #dce6f7; }
                QTabWidget::pane {
                    background: #ffffff; border: 1px solid #c7ced8;
                    border-radius: 8px; top: -1px;
                }
                QTabBar::tab {
                    background: #dfe5ed;
                    border: 1px solid #c7ced8; border-bottom: none;
                    border-top-left-radius: 7px; border-top-right-radius: 7px;
                    padding: 8px 15px; margin-right: 2px;
                }
                QTabBar::tab:hover { background: #edf2f8; }
                QTabBar::tab:selected {
                    background: #ffffff; font-weight: 600;
                }
                QCheckBox { spacing: 7px; color: #303947; }
                QCheckBox::indicator {
                    width: 16px; height: 16px; border-radius: 4px;
                    border: 1px solid #aeb8c6; background: #ffffff;
                }
                QCheckBox::indicator:checked { background: #5b8def; border-color: #5b8def; }
                QMenuBar { background: #e4e9f0; color: #283344; padding: 3px; }
                QMenuBar::item { padding: 6px 10px; border-radius: 5px; }
                QMenuBar::item:selected { background: #d4deed; }
                QMenu { background: #ffffff; color: #202733; border: 1px solid #c7ced8; padding: 4px; }
                QMenu::item { padding: 7px 22px; border-radius: 4px; }
                QMenu::item:selected { background: #e8eef8; }
                QSlider::groove:horizontal { height: 5px; background: #cfd6e0; border-radius: 2px; }
                QSlider::handle:horizontal { width: 15px; margin: -5px 0; border-radius: 8px; background: #5b8def; }
            """)
        else:
            self.setStyleSheet(r"""
                QMainWindow { background: #151922; }
                QWidget { background: #151922; color: #edf1f7; font-size: 10pt; }
                QLabel { background: transparent; color: #cdd5e1; }
                QLineEdit, QTextEdit, QTextBrowser {
                    background: #202632; color: #edf1f7;
                    border: 1px solid #394354; border-radius: 7px;
                    padding: 7px 9px; selection-background-color: #527fd6;
                }
                QLineEdit:focus, QTextEdit:focus, QTextBrowser:focus {
                    border: 2px solid #648ee3; padding: 6px 8px;
                }
                QPushButton {
                    background: #242b38; color: #edf1f7;
                    border: 1px solid #414b5d; border-radius: 7px;
                    padding: 7px 14px; min-height: 20px;
                }
                QPushButton:hover { background: #303a4b; border-color: #6688ca; }
                QPushButton:pressed { background: #1d2531; }
                QTabWidget::pane {
                    background: #1d232e; border: 1px solid #394354;
                    border-radius: 8px; top: -1px;
                }
                QTabBar::tab {
                    background: #252c38;
                    border: 1px solid #394354; border-bottom: none;
                    border-top-left-radius: 7px; border-top-right-radius: 7px;
                    padding: 8px 15px; margin-right: 2px;
                }
                QTabBar::tab:hover { background: #303948; }
                QTabBar::tab:selected {
                    background: #1d232e; font-weight: 600;
                }
                QCheckBox { spacing: 7px; color: #cdd5e1; }
                QCheckBox::indicator {
                    width: 16px; height: 16px; border-radius: 4px;
                    border: 1px solid #4a5669; background: #202632;
                }
                QCheckBox::indicator:checked { background: #5f89df; border-color: #5f89df; }
                QMenuBar { background: #1c222d; color: #dce3ed; padding: 3px; }
                QMenuBar::item { padding: 6px 10px; border-radius: 5px; }
                QMenuBar::item:selected { background: #303948; }
                QMenu { background: #202632; color: #edf1f7; border: 1px solid #3b4658; padding: 4px; }
                QMenu::item { padding: 7px 22px; border-radius: 4px; }
                QMenu::item:selected { background: #303a4b; }
                QSlider::groove:horizontal { height: 5px; background: #394354; border-radius: 2px; }
                QSlider::handle:horizontal { width: 15px; margin: -5px 0; border-radius: 8px; background: #648ee3; }
            """)
        self._sync_theme_actions()

    def _sync_theme_actions(self):
        if hasattr(self, "dark_action"):
            self.dark_action.setChecked(self.current_theme == "dark")
            self.light_action.setChecked(self.current_theme == "light")

    def set_theme(self, theme):
        if theme not in {"dark", "light"}:
            return
        self.current_theme = theme
        self._apply_theme(theme)
        self._write_settings()
        self.status.setText("Theme gespeichert: " + ("Dunkel" if theme == "dark" else "Hell"))

    # ---------- Settings ----------
    def _write_settings(self):
        config = configparser.ConfigParser()
        if SETTINGS_FILE.exists():
            config.read(SETTINGS_FILE, encoding="utf-8")
        if "MeshCom" not in config:
            config["MeshCom"] = {}
        section = config["MeshCom"]
        section["ip"] = self.ip_input.text().strip().rstrip("/")
        section["target"] = self.target_input.text().strip()
        section["filter_enabled"] = "1" if self.filter_enabled.isChecked() else "0"
        section["theme"] = self.current_theme
        section["sound_enabled"] = "1" if self.sound_enabled else "0"
        section["sound_driver"] = self.sound_driver
        section["sound_volume"] = str(self.sound_volume)
        section["sound_file"] = self.sound_file
        section["weather_enabled"] = "1" if getattr(self, "weather_enabled", False) else "0"
        section["weather_city"] = self.weather_city_input.text().strip() if hasattr(self, "weather_city_input") else ""
        section["own_callsign"] = self.own_callsign_input.text().strip().upper()
        section["own_lat"] = self.own_lat_input.text().strip()
        section["own_lon"] = self.own_lon_input.text().strip()
        for i, field in enumerate(self.filter_inputs, 1):
            section[f"filter_room{i}"] = field.text().strip()
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            config.write(f)

    def save_all_settings(self):
        ip = self.ip_input.text().strip().rstrip("/")
        if not ip:
            self.status.setText("Fehler: Keine Hotspot-IP eingetragen")
            return
        try:
            lat_text = self.own_lat_input.text().strip().replace(",", ".")
            lon_text = self.own_lon_input.text().strip().replace(",", ".")
            if lat_text or lon_text:
                lat = float(lat_text)
                lon = float(lon_text)
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError
            else:
                lat = lon = None
        except ValueError:
            self.status.setText("Fehler: Ungültige eigene Koordinaten")
            return
        self.own_callsign = self._normalize_callsign(self.own_callsign_input.text())
        self.own_lat, self.own_lon = lat, lon
        self._write_settings()
        self.mesh = MeshCom(ip)
        self._ensure_room_tabs()
        self._update_map()
        self.status.setText("Einstellungen gespeichert")

    def save_filter_settings(self):
        self._write_settings()
        self._ensure_room_tabs()
        self.update_messages()
        rooms = self._rooms()
        self.status.setText("Filter gespeichert: " + (", ".join(rooms) if rooms else "keine Räume"))

    def _filter_toggled(self, _enabled):
        self._write_settings()
        self.update_messages()

    # ---------- Wetterdaten ----------
    def _toggle_weather_panel(self, enabled):
        self.weather_enabled = bool(enabled)
        if hasattr(self, "weather_panel"):
            self.weather_panel.setVisible(self.weather_enabled)
        if hasattr(self, "weather_action") and self.weather_action.isChecked() != self.weather_enabled:
            self.weather_action.blockSignals(True)
            self.weather_action.setChecked(self.weather_enabled)
            self.weather_action.blockSignals(False)
        if hasattr(self, "weather_city_input"):
            self._write_settings()
        if self.weather_enabled and hasattr(self, "weather_panel"):
            self._refresh_weather()

    def _set_weather_panel_visible(self, enabled):
        self.weather_enabled = bool(enabled)
        self.weather_panel.setVisible(self.weather_enabled)
        if hasattr(self, "weather_action"):
            self.weather_action.blockSignals(True)
            self.weather_action.setChecked(self.weather_enabled)
            self.weather_action.blockSignals(False)

    @staticmethod
    def _parse_wx_html(content):
        """Read the WX table returned by MeshCom's /?page=wx endpoint."""
        text = html.unescape(str(content or ""))
        rows = {}
        for match in re.finditer(r"<tr\b[^>]*>(.*?)</tr>", text, flags=re.I | re.S):
            cells = re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", match.group(1), flags=re.I | re.S)
            if len(cells) < 2:
                continue
            def clean(value):
                value = re.sub(r"<[^>]+>", " ", value)
                return " ".join(html.unescape(value).split())
            key = clean(cells[0])
            value = clean(cells[1])
            if key:
                rows[key.lower()] = value
        aliases = {
            "temperature": ("temperature", "temp", "temperatur"),
            "humidity": ("humidity", "luftfeuchte", "hum"),
            "qfe": ("qfe",),
            "qnh": ("qnh",),
        }
        result = {}
        for target, names in aliases.items():
            for key, value in rows.items():
                if any(key == name or key.startswith(name + " ") for name in names):
                    result[target] = value
                    break
        return result

    def _refresh_weather(self):
        if self._weather_fetch_in_progress:
            return
        ip = self.ip_input.text().strip().rstrip("/") if hasattr(self, "ip_input") else ""
        if not ip:
            self.weather_values_label.setText("Keine Wetterwerte in der WX-Information gefunden")
            self.weather_status_label.setText("Keine Hotspot-IP eingetragen")
            return
        self._weather_fetch_in_progress = True
        self.weather_refresh_button.setEnabled(False)
        self.weather_status_label.setText("WX-Information wird geladen …")
        url = ip + "/"

        def worker():
            try:
                import requests
                response = requests.get(url, params={"page": "wx"}, timeout=8)
                response.raise_for_status()
                data = self._parse_wx_html(response.text)
                data["url"] = response.url
                if not all(data.get(k) for k in ("temperature", "humidity", "qfe", "qnh")):
                    data["error"] = "Keine vollständigen WX-Werte in der Antwort gefunden."
                self.weatherUpdated.emit(data)
            except Exception as exc:
                self.weatherUpdated.emit({"error": str(exc)})

        threading.Thread(target=worker, name="MeshCom-Wetter", daemon=True).start()

    def _apply_weather_result(self, data):
        self._weather_fetch_in_progress = False
        self.weather_refresh_button.setEnabled(True)
        if data.get("error"):
            self.weather_values_label.setText("Keine Wetterwerte in der WX-Information gefunden")
            self.weather_status_label.setText(str(data["error"]))
            return
        self.weather_data = data
        self.weather_values_label.setText(
            f"Temperatur: {data.get('temperature', '–')} | "
            f"Luftfeuchte: {data.get('humidity', '–')} | "
            f"QFE: {data.get('qfe', '–')} | "
            f"QNH: {data.get('qnh', '–')}"
        )
        self.weather_status_label.setText("WX-Information erfolgreich aus dem MeshCom-WebService gelesen")

    def _send_weather(self):
        if not self.weather_data:
            self.status.setText("Keine Wetterdaten vorhanden – zuerst Wetter aktualisieren")
            return
        city = self.weather_city_input.text().strip()
        if not city:
            self.status.setText("Bitte zuerst einen Stadtnamen eingeben")
            return
        text = (
            f"{city}: {self.weather_data.get('temperature', '–')} | "
            f"Luftfeuchte {self.weather_data.get('humidity', '–')} | "
            f"QFE {self.weather_data.get('qfe', '–')} | "
            f"QNH {self.weather_data.get('qnh', '–')}"
        )
        if len(text) > 149:
            self.status.setText("Wettermeldung ist länger als 149 Zeichen")
            return
        self.weather_send_button.setEnabled(False)
        try:
            _answer, _url, method = self.mesh.send_message(text, "")
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.send_log.setText(f"Letzter Wetter-Sendeauftrag {timestamp}: → alle | {text} | HTTP {method} 200")
            self.status.setText("Wetterdaten ohne Raumangabe an den Hotspot übertragen")
            self._write_settings()
        except Exception as exc:
            self.status.setText(f"Wetterdaten konnten nicht gesendet werden: {exc}")
        finally:
            self.weather_send_button.setEnabled(True)

    # ---------- Hilfe / Info ----------
    def open_help(self):
        """Show the built-in MeshCom-Guru user guide."""
        dialog = QDialog(self)
        dialog.setWindowTitle("MeshCom-Guru – Anleitung")
        dialog.resize(760, 620)
        layout = QVBoxLayout(dialog)

        view = QTextBrowser(dialog)
        view.setOpenExternalLinks(True)
        view.setHtml(f"""
        <h2>MeshCom-Guru v{VERSION}</h2>
        <h3>Kurzanleitung</h3>
        <p><b>Hotspot IP:</b> IP-Adresse des MeshCom-Hotspots eintragen.</p>
        <p><b>Raum / Ziel:</b> Eine Raumnummer (z. B. 262) oder ein Rufzeichen für eine private Nachricht eintragen.</p>
        <p><b>Eigene Station / GPS:</b> Eigenes Rufzeichen sowie optional Breitengrad und Längengrad eintragen.</p>
        <p><b>Einstellungen speichern:</b> Speichert die aktuellen Einstellungen dauerhaft.</p>
        <p><b>Node Info aufrufen:</b> Öffnet die Node-Information des verbundenen MeshCom-WebService.</p>
        <h3>Nachrichten</h3>
        <p>Über die Raumfilter können bis zu fünf Räume ausgewählt werden. Mit <b>Aktualisieren</b> werden neue Nachrichten abgerufen.</p>
        <p>Mit <b>Senden</b> wird eine Nachricht an den eingetragenen Raum bzw. das Ziel übertragen.</p>
        <h3>Karte und Positionen</h3>
        <p>Empfangene MeshCom-Positionsdaten werden eigenständig über UDP Port 1799 empfangen und auf der Karte dargestellt. MeshCom-Guru benötigt dafür keine Zusammenarbeit mit MeshDash.</p>
        <h3>Menü</h3>
        <p><b>Datei:</b> Einstellungen speichern, Nachrichten aktualisieren und Programm beenden.</p>
        <p><b>Einstellungen:</b> Sound-Einstellungen und die Testfunktion <b>Wetterdaten</b>. Bei aktiviertem Wetterfenster werden die WX-Werte des verbundenen MeshCom-Nodes angezeigt. Mit einer eingetragenen Stadt können die Werte ohne Raumangabe gesendet werden.</p>
        <p><b>Theme:</b> Dunkles oder helles Erscheinungsbild.</p>
        <p><b>Hilfe → Info:</b> Versions- und Urheberinformation.</p>
        <h3>Installation</h3>
        <p><b>Linux:</b> Im Projektordner <code>./run_linux.sh</code> ausführen. Für einen Desktop-Eintrag <code>./install_desktop_launcher.sh</code> verwenden.</p>
        <p><b>Windows:</b> <code>run_windows.bat</code> starten. Python und die Pakete aus <code>requirements.txt</code> müssen installiert sein.</p>
        """)
        layout.addWidget(view, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        dialog.exec()

    def open_about(self):
        """Show compact program information."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Über MeshCom-Guru")
        dialog.setFixedSize(360, 190)
        layout = QVBoxLayout(dialog)
        title = QLabel("<h2>MeshCom-Guru</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        version_label = QLabel(f"Version v{VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        by_label = QLabel("By Goldisoft 2026")
        by_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(by_label)
        layout.addStretch(1)
        close_btn = QPushButton("OK")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec()

    # ---------- Node Information ----------
    def open_node_info(self):
        """Open the connected MeshCom node's own Node Information page in-app.

        The MeshCom WebService provides a browser-based information page with
        firmware, start date, callsign, hardware, UTC offset and power/status
        values. We deliberately show that page inside MeshCom-Guru instead of
        trying to duplicate firmware-specific fields in our own parser. This
        keeps the feature compatible with newer node firmware as the WebService
        adds fields.
        """
        url = self.mesh.ip.rstrip('/') + '/'
        if QWebEngineView is None:
            # WebEngine is already required for the map, but keep a safe fallback
            # for installations where it could not be imported.
            try:
                from PySide6.QtGui import QDesktopServices
                QDesktopServices.openUrl(QUrl(url))
                self.status.setText("Node Information im Standard-Browser geöffnet")
            except Exception as exc:
                self.status.setText(f"Node Info konnte nicht geöffnet werden: {exc}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Node Information")
        dialog.resize(900, 750)
        dialog.setMinimumSize(820, 650)
        layout = QVBoxLayout(dialog)

        view = QWebEngineView(dialog)
        view.setUrl(QUrl(url))
        layout.addWidget(view, 1)

        buttons = QHBoxLayout()
        refresh = QPushButton("Aktualisieren")
        refresh.clicked.connect(lambda: view.reload())
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(dialog.accept)
        buttons.addWidget(refresh)
        buttons.addStretch(1)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

        view.loadFinished.connect(
            lambda ok: self.status.setText(
                "Node Information geladen" if ok else "Node Information konnte nicht geladen werden"
            )
        )
        dialog.exec()

    # ---------- Sound ----------
    def _prepare_sound(self):
        """Prepare the configurable notification sound without blocking the UI."""
        try:
            sound_path = self._effective_sound_file()
            if sound_path and sound_path.exists():
                if QSoundEffect is None:
                    self._sound_effect = None
                    return
                self._sound_effect = QSoundEffect(self)
                self._sound_effect.setSource(QUrl.fromLocalFile(str(sound_path)))
                self._sound_effect.setVolume(self.sound_volume / 100.0)
        except Exception:
            self._sound_effect = None

    def _effective_sound_file(self):
        if self.sound_file:
            path = Path(os.path.expanduser(self.sound_file))
            if path.exists():
                return path
        return Path(__file__).resolve().parent.parent / "data" / "notification.wav"

    def _play_notification_sound(self):
        if not self.sound_enabled:
            return
        driver = self.sound_driver
        sound_path = self._effective_sound_file()
        volume = max(0, min(100, self.sound_volume))
        try:
            if driver in {"auto", "qt"} and sound_path.exists():
                if self._sound_effect is None:
                    self._prepare_sound()
                if self._sound_effect is not None:
                    self._sound_effect.setVolume(volume / 100.0)
                    self._sound_effect.play()
                    return
                if driver == "qt":
                    QApplication.beep()
                    return

            if driver == "pulse" and sound_path.exists():
                # paplay expects a PulseAudio/PipeWire volume in the range 0..65536.
                subprocess.Popen(
                    ["paplay", f"--volume={int(volume * 65536 / 100)}", str(sound_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return

            if driver == "alsa" and sound_path.exists():
                subprocess.Popen(
                    ["aplay", "-q", str(sound_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return

            if driver == "windows" and platform.system().lower().startswith("win") and sound_path.exists():
                import winsound
                winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
                return

            # Last-resort notification: always available on Qt platforms.
            QApplication.beep()
        except Exception:
            # Sound must never be allowed to break the chat application.
            try:
                QApplication.beep()
            except Exception:
                pass

    def open_sound_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Sound-Einstellungen")
        dialog.resize(560, 260)

        layout = QVBoxLayout(dialog)

        enabled = QCheckBox("Akustisches Signal bei neuen Nachrichten")
        enabled.setChecked(self.sound_enabled)
        layout.addWidget(enabled)

        form = QFormLayout()
        driver = QComboBox()
        driver.addItem("Automatisch", "auto")
        driver.addItem("Qt Multimedia", "qt")
        driver.addItem("System-Beep", "beep")
        driver.addItem("PulseAudio / PipeWire", "pulse")
        driver.addItem("ALSA (aplay)", "alsa")
        driver.addItem("Windows (winsound)", "windows")
        idx = max(0, driver.findData(self.sound_driver))
        driver.setCurrentIndex(idx)
        form.addRow("Soundtreiber:", driver)

        volume = QSlider(Qt.Orientation.Horizontal)
        volume.setRange(0, 100)
        volume.setValue(self.sound_volume)
        volume_label = QLabel(f"{self.sound_volume} %")
        volume.valueChanged.connect(lambda value: volume_label.setText(f"{value} %"))
        volume_row = QHBoxLayout()
        volume_row.addWidget(volume, 1)
        volume_row.addWidget(volume_label)
        form.addRow("Lautstärke:", volume_row)

        file_input = QLineEdit(self.sound_file)
        file_input.setPlaceholderText("leer = mitgelieferten Signalton verwenden")
        browse = QPushButton("Datei wählen …")
        browse.clicked.connect(lambda: self._choose_sound_file(file_input))
        file_row = QHBoxLayout()
        file_row.addWidget(file_input, 1)
        file_row.addWidget(browse)
        form.addRow("Eigener Sound:", file_row)
        layout.addLayout(form)

        hint = QLabel(
            "Bei neuen Nachrichten in einem nicht aktiven Tab wird einmalig ein Signal abgespielt. "
            "Der Ton wird nicht bei jedem Aktualisieren wiederholt."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        test_button = buttons.addButton("Testen", QDialogButtonBox.ButtonRole.ActionRole)
        test_button.clicked.connect(
            lambda: self._preview_sound(
                bool(enabled.isChecked()), driver.currentData(), volume.value(), file_input.text().strip()
            )
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.sound_enabled = enabled.isChecked()
            self.sound_driver = str(driver.currentData() or "auto")
            self.sound_volume = volume.value()
            self.sound_file = file_input.text().strip()
            self._prepare_sound()
            self._write_settings()
            self.status.setText("Sound-Einstellungen gespeichert")

    @staticmethod
    def _choose_sound_file(target):
        filename, _ = QFileDialog.getOpenFileName(
            None,
            "Sounddatei auswählen",
            "",
            "WAV-Dateien (*.wav);;Alle Dateien (*)",
        )
        if filename:
            target.setText(filename)

    def _preview_sound(self, enabled, driver, volume, filename):
        if not enabled:
            QApplication.beep()
            return
        old = (self.sound_enabled, self.sound_driver, self.sound_volume, self.sound_file)
        self.sound_enabled = True
        self.sound_driver = str(driver or "auto")
        self.sound_volume = int(volume)
        self.sound_file = str(filename or "")
        self._prepare_sound()
        self._play_notification_sound()
        self.sound_enabled, self.sound_driver, self.sound_volume, self.sound_file = old
        self._prepare_sound()

    # ---------- Tabs ----------
    def _rooms(self):
        result = []
        for field in self.filter_inputs:
            value = field.text().strip()
            if value and value not in result:
                result.append(value)
        return result

    def _ensure_room_tabs(self):
        self._ensure_tab(("all", "all"), "Alle")
        rooms = self._rooms()
        for room in rooms:
            self._ensure_tab(("room", room), f"Raum {room}")

        # Remove room tabs whose filter entry was cleared.
        wanted = set(rooms)
        for key, index in list(self.tab_keys.items()):
            if key[0] == "room" and key[1] not in wanted:
                self.tabs.removeTab(index)
                del self.tab_keys[key]
                self._reindex_tabs()
                self.tab_hashes.pop(key, None)
                self.unread.discard(key)

    def _ensure_tab(self, key, title=None):
        if key in self.tab_keys:
            return self.tab_keys[key]
        view = ChatView()
        view._mesh_key = key
        view.callsignClicked.connect(self.open_private_chat)
        index = self.tabs.addTab(view, title or key[1])
        self.tab_keys[key] = index
        # Nur echte Privat-Chats dürfen geschlossen werden.
        # Die Tabs "Alle" und die fünf Filter-Räume bleiben fest bestehen.
        if key[0] != "private":
            self.tabs.tabBar().setTabButton(index, self.tabs.tabBar().ButtonPosition.RightSide, None)
        self.tab_hashes.setdefault(key, "")
        return index

    def _close_tab(self, index):
        """Schließt ausschließlich einen privaten Chat-Tab."""
        key = self._key_for_index(index)
        if key is None or key[0] != "private":
            return
        self.tabs.removeTab(index)
        self.tab_keys.pop(key, None)
        # Merke den aktuellen Inhalt des geschlossenen Privat-Tabs.
        # Solange beim Refresh exakt derselbe Nachrichtenstand vorliegt,
        # wird der Tab nicht sofort wieder künstlich geöffnet. Sobald aber
        # eine neue Nachricht für diesen Chat eintrifft, ändert sich der
        # Inhalt-Digest und der Tab darf automatisch wieder erscheinen.
        closed_hash = self.tab_hashes.get(key, "")
        self.tab_hashes.pop(key, None)
        self.unread.discard(key)
        self.closed_private[key[1].upper()] = closed_hash
        self._reindex_tabs()
        self.status.setText(f"Privatchat geschlossen: {key[1]}")

    def _reindex_tabs(self):
        self.tab_keys = {}
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            key = getattr(widget, "_mesh_key", None)
            if key is not None:
                self.tab_keys[key] = i

    def _tab_changed(self, index):
        key = self._key_for_index(index)
        if key is None:
            return
        self.unread.discard(key)
        self._set_tab_normal(key)
        if key[0] == "room":
            self.target_input.setText(key[1])
        elif key[0] == "private":
            self.target_input.setText(key[1])
        elif key[0] == "all":
            self.target_input.clear()
        view = self.tabs.widget(index)
        if isinstance(view, ChatView):
            view.scroll_to_bottom()

    def _key_for_index(self, index):
        for key, idx in self.tab_keys.items():
            if idx == index:
                return key
        return None

    def _set_tab_unread(self, key):
        if key not in self.tab_keys:
            return
        was_unread = key in self.unread
        idx = self.tab_keys[key]
        self.unread.add(key)
        self.tabs.tabBar().setTabTextColor(idx, Qt.GlobalColor.red)
        if not was_unread and self.tabs.currentIndex() != idx:
            self._play_notification_sound()

    def _set_tab_normal(self, key):
        if key not in self.tab_keys:
            return
        idx = self.tab_keys[key]
        self.tabs.tabBar().setTabTextColor(idx, Qt.GlobalColor.black if self.current_theme == "light" else Qt.GlobalColor.white)

    def open_private_chat(self, callsign):
        callsign = self._normalize_callsign(callsign)
        if not callsign:
            return
        key = ("private", callsign)
        # Ein bewusst geschlossener Privat-Tab darf durch einen späteren
        # manuellen Klick wieder geöffnet werden.
        self.closed_private.pop(callsign.upper(), None)
        index = self._ensure_tab(key, callsign)
        self.tabs.setCurrentIndex(index)
        self.target_input.setText(callsign)
        self.status.setText(f"Privatchat geöffnet: {callsign}")

    @staticmethod
    def _normalize_callsign(value):
        match = CALLSIGN_RE.search(str(value).upper())
        if not match:
            return ""
        candidate = match.group(0)
        if candidate.isdigit():
            return ""
        return candidate

    # ---------- Message parsing ----------
    @staticmethod
    def _extract_message_blocks(page):
        """Extract normal message cards plus position/status cards.

        The MeshCom WebService does not use one single HTML class for every
        packet type. Normal text messages are usually inside ``class=message``,
        while position/status packets can be rendered in a different container.
        The old parser therefore silently dropped the latter.

        We keep the existing message parser and additionally collect the
        smallest DIV that contains both longitude and latitude information.
        This makes the client display the same position packets that another
        dashboard can already see on the very same WebService.
        """
        tag_re = re.compile(r"</?div\b[^>]*>", re.IGNORECASE)
        blocks = []

        # The MeshCom WebService response uses containers such as
        # ``message-row`` and ``message-bubble``. Older versions of this client
        # looked only for a class token named exactly ``message`` and therefore
        # missed the complete message stream. Extract each message-row instead.
        row_re = re.compile(
            r'<div\b[^>]*class=["\'][^"\']*\bmessage-row\b[^"\']*["\'][^>]*>',
            re.IGNORECASE,
        )
        for start_match in row_re.finditer(page):
            start = start_match.start()
            depth = 0
            end = None
            for tag in tag_re.finditer(page, start):
                raw = tag.group(0)
                if raw.lower().startswith("</div"):
                    depth -= 1
                    if depth == 0:
                        end = tag.end()
                        break
                else:
                    depth += 1
            if end:
                blocks.append(page[start:end])

        # Compatibility fallback for older WebService layouts that used a
        # standalone ``message`` class without ``message-row``.
        if not blocks:
            for start_match in re.finditer(r'<div\b[^>]*class=["\'][^"\']*\bmessage\b[^"\']*["\'][^>]*>', page, re.IGNORECASE):
                start = start_match.start()
                depth = 0
                end = None
                for tag in tag_re.finditer(page, start):
                    raw = tag.group(0)
                    if raw.lower().startswith("</div"):
                        depth -= 1
                        if depth == 0:
                            end = tag.end()
                            break
                    else:
                        depth += 1
                if end:
                    blocks.append(page[start:end])

        # Position/status cards may not have class=message. Find every pair of
        # German/English coordinate labels and then the smallest surrounding DIV
        # containing both values.
        coord_re = re.compile(
            r"(?:L(?:ä|ae)ngengrad|Breitengrad|Longitude|Latitude|\bLAT\b|\bLON\b)",
            re.IGNORECASE,
        )
        coord_positions = [m.start() for m in coord_re.finditer(page)]
        if len(coord_positions) >= 2:
            divs = []
            stack = []
            for tag in tag_re.finditer(page):
                raw = tag.group(0)
                if raw.startswith("</"):
                    if stack:
                        start = stack.pop()
                        divs.append((start, tag.end()))
                else:
                    stack.append(tag.start())
            existing = set(blocks)
            # Test nearby coordinate-label pairs; a real position card normally
            # contains both labels in the same DIV hierarchy.
            for i, first in enumerate(coord_positions):
                for second in coord_positions[i + 1:]:
                    if second - first > 12000:
                        break
                    lo, hi = sorted((first, second))
                    candidates = [(e - st, st, e) for st, e in divs if st <= lo and hi < e]
                    if not candidates:
                        continue
                    # Prefer the smallest coordinate-containing DIV that also
                    # contains the packet header. This keeps "Von: DB00HL-12"
                    # together with the coordinate lines when the WebService
                    # nests the GPS values inside a child DIV.
                    header_candidates = []
                    for size, st, e in candidates:
                        candidate_plain = MainWindow._plain(page[st:e]).lower()
                        if "von:" in candidate_plain or "from:" in candidate_plain or "msgid" in candidate_plain or "message id" in candidate_plain:
                            header_candidates.append((size, st, e))
                    _, st, e = min(header_candidates or candidates)
                    candidate = page[st:e]
                    plain = MainWindow._plain(candidate).lower()
                    if ("längengrad" in plain or "laengengrad" in plain or "longitude" in plain or "lon" in plain) and ("breitengrad" in plain or "latitude" in plain or "lat" in plain):
                        if candidate not in existing:
                            blocks.append(candidate)
                            existing.add(candidate)
                    break
        # Privatnachrichten können beim MeshCom-WebService in einem anderen
        # Container liegen als normale message-row-Karten. Deshalb suchen wir
        # zusätzlich direkt nach einem echten CALL1 > CALL2-Header und nehmen
        # den kleinsten umschließenden DIV. So kann eine rote Privat-Tab-Anzeige
        # nicht mehr entstehen, ohne dass der eigentliche Nachrichtentext in
        # den bereits extrahierten Blöcken vorhanden ist.
        private_header_re = re.compile(
            r'[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?\s*(?:>|&gt;)\s*'
            r'[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?',
            re.IGNORECASE,
        )
        div_ranges = []
        stack = []
        for tag in tag_re.finditer(page):
            raw = tag.group(0)
            if raw.lower().startswith('</div'):
                if stack:
                    st = stack.pop()
                    div_ranges.append((st, tag.end()))
            else:
                stack.append(tag.start())
        existing = set(blocks)
        for hm in private_header_re.finditer(page):
            candidates = [(e-st, st, e) for st, e in div_ranges if st <= hm.start() and hm.end() <= e]
            if candidates:
                _, st, e = min(candidates)
                candidate = page[st:e]
                plain = MainWindow._plain(candidate)
                if private_header_re.search(plain) and candidate not in existing:
                    blocks.append(candidate)
                    existing.add(candidate)
            else:
                # Fallback for unusual responses without a DIV wrapper.
                lo = max(0, hm.start() - 500)
                hi = min(len(page), hm.end() + 1500)
                candidate = page[lo:hi]
                if candidate not in existing:
                    blocks.append(candidate)
                    existing.add(candidate)

        return blocks

    @staticmethod
    def _plain(block):
        text = re.sub(r"<br\s*/?>", "\n", block, flags=re.IGNORECASE)
        text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(text)
        return re.sub(r"[ \t]+", " ", text).strip()

    @classmethod
    def _room_from_block(cls, block):
        match = ROOM_RE.search(block)
        return match.group(1) if match else ""

    @classmethod
    def _target_from_block(cls, block):
        match = TARGET_RE.search(block)
        return match.group(1).upper() if match else ""

    @classmethod
    def _private_participants(cls, block):
        """Return sender and destination for a genuine MeshCom direct message.

        MeshCom nodes can prepend several callsigns to the sender side, e.g.
        ``DL9ABC-1,DL1XYZ-1>DL1XYZ-1``.  The FIRST callsign is the sender.

        Parsing is deliberately done on the plain, HTML-decoded message text.
        This makes the detection independent of whether the node writes ``>``
        or ``&gt;`` and independent of the surrounding HTML links.  A numeric
        destination such as ``>262`` is not a private message.
        """
        plain = cls._plain(block).upper()
        if not plain:
            return []

        # Search the complete decoded message instead of partitioning at the
        # first '>'.  This is important because the dashboard may contain
        # timestamps, links and other HTML around the actual message header.
        match = DIRECT_HEADER_RE.search(plain)
        if not match:
            return []

        left_calls = CALLSIGN_RE.findall(match.group("left"))
        target = cls._normalize_callsign(match.group("right"))
        if not left_calls or not target:
            return []

        sender = cls._normalize_callsign(left_calls[0])
        if not sender:
            return []

        return [sender, target]

    @classmethod
    def _sender_from_private_block(cls, block):
        participants = cls._private_participants(block)
        return participants[0] if participants else ""

    @classmethod
    def _make_clickable(cls, block):
        # Dashboard-Links mit Rufzeichen werden auf interne MeshCom-Links umgebogen.
        # Danach werden zusätzlich noch plain-text-Rufzeichen anklickbar gemacht.
        protected = []

        def protect_anchor(match):
            # Dashboard-Links können mehrere Rufzeichen in EINEM <a>-Element
            # enthalten (z. B. "DL9ABC-1,DL1XYZ-1"). Dieses komplette Element
            # darf nicht nur mit dem ersten Rufzeichen verknüpft werden.
            # Stattdessen machen wir jedes enthaltene Rufzeichen einzeln
            # anklickbar, damit genau das angeklickte Rufzeichen den passenden
            # Privatchat öffnet.
            inner = match.group(2) or ""

            def link_callsigns(text):
                parts = re.split(r"(<[^>]+>)", text)
                for i in range(0, len(parts), 2):
                    def anchor_call(call_match):
                        call = cls._normalize_callsign(call_match.group(0))
                        return (
                            f'<a href="meshcom://call/{html.escape(call)}">'
                            f'{html.escape(call_match.group(0))}</a>'
                        ) if call else call_match.group(0)
                    parts[i] = CALLSIGN_RE.sub(anchor_call, parts[i])
                return "".join(parts)

            converted = link_callsigns(inner)
            protected.append(converted)
            return f"@@MESHCOM_ANCHOR_{len(protected)-1}@@"

        block = re.sub(r'<a\b([^>]*)>(.*?)</a>', protect_anchor, block, flags=re.IGNORECASE | re.DOTALL)

        def repl(match):
            text = match.group(0)
            if text.isdigit():
                return text
            return f'<a href="meshcom://call/{html.escape(text.upper())}">{html.escape(text)}</a>'

        # Plain-Text-Internetlinks anklickbar machen. Bereits vorhandene HTML-Tags
        # bleiben unangetastet. Satzzeichen am Ende werden nicht Teil des Links.
        URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)

        def link_url(match):
            raw = match.group(0)
            trailing = ""
            while raw and raw[-1] in ".,!?;:)\\]}":
                trailing = raw[-1] + trailing
                raw = raw[:-1]
            if not raw:
                return match.group(0)
            safe_url = html.escape(raw, quote=True)
            return f'<a href="{safe_url}">{html.escape(raw)}</a>{html.escape(trailing)}'

        parts = re.split(r"(<[^>]+>)", block)
        for i in range(0, len(parts), 2):
            # URLs zuerst verlinken. Die anschließende Rufzeichen-Erkennung läuft
            # nur noch außerhalb der erzeugten <a>-Tags.
            parts[i] = URL_RE.sub(link_url, parts[i])
        result_with_urls = "".join(parts)

        parts = re.split(r"(<[^>]+>)", result_with_urls)
        for i in range(0, len(parts), 2):
            parts[i] = CALLSIGN_RE.sub(repl, parts[i])
        result = "".join(parts)
        for i, anchor in enumerate(protected):
            result = result.replace(f"@@MESHCOM_ANCHOR_{i}@@", anchor)
        return result

    def _render_blocks(self, blocks):
        if not blocks:
            return "<html><body><p><b>Keine Nachrichten.</b></p></body></html>"
        return "<html><body>" + "\n".join(self._make_clickable(b) for b in blocks) + "</body></html>"

    def _room_blocks(self, blocks, room):
        return [b for b in blocks if self._room_from_block(b) == str(room)]

    def _private_blocks(self, blocks, callsign):
        # Private chats dürfen ausschließlich echte Direktnachrichten enthalten.
        # Entscheidend ist die explizite Direktverbindung CALL1>CALL2; dadurch
        # kann normaler Raumverkehr mit zufällig vorkommenden Rufzeichen niemals
        # in einen Privat-Tab rutschen.
        wanted = callsign.upper()
        result = []
        for block in blocks:
            participants = self._private_participants(block)
            if not participants:
                continue
            if wanted in participants:
                result.append(block)
        return result

    def _is_own_private_echo(self, block):
        """Erkennt das vom Node zurückgelieferte Echo einer eigenen Privatnachricht.

        Beim Senden eines Privatchats liefert der WebService die Nachricht wieder
        im Nachrichtenstrom aus. Ohne diese Prüfung würde der erste Teil des
        Headers fälschlich als neuer Absender behandelt und ein eigener Privat-
        Tab geöffnet. Wir unterdrücken deshalb nur das exakt zuletzt gesendete
        private Echo; die Nachricht bleibt im Tab „Alle“ sichtbar.
        """
        if not self.last_private_sent:
            return False
        target, text = self.last_private_sent
        participants = self._private_participants(block)
        if not participants:
            return False
        if self.own_callsign and participants[0].upper() == self.own_callsign.upper():
            return True
        # Der rechte Teil des Direkt-Headers ist das Ziel der eigenen Sendung.
        if participants[1].upper() != target.upper():
            return False
        plain = self._plain(block)
        return text.strip() and text.strip() in plain

    def _filter_blocks(self, blocks):
        if not self.filter_enabled.isChecked():
            return blocks
        rooms = self._rooms()
        if not rooms:
            return []
        return [b for b in blocks if self._room_from_block(b) in rooms]

    # ---------- Karte / Positionsdaten ----------
    @classmethod
    def _coordinates_from_block(cls, block):
        plain = cls._plain(block).upper().replace("°", " ")

        # Standard MeshCom/JSON-like textual forms.
        labelled = re.search(
            r"\b(?:LAT|LATITUDE)\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)\D+"
            r"(?:LON|LONG|LONGITUDE)\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)\b", plain
        )
        if labelled:
            lat = float(labelled.group(1).replace(",", "."))
            lon = float(labelled.group(2).replace(",", "."))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon

        # German MeshCom status cards can contain the coordinate labels in a
        # misleading order.  In the real dashboard response seen in testing
        # they can look like:
        #   "Längengrad: 52.0506 N"
        #   "Breitengrad: 8.6503 E"
        # Here N/S and E/W are authoritative: N/S is latitude, E/W is
        # longitude.  Parse the individual labelled lines first so unrelated
        # letters such as the N in another field cannot be selected by mistake.
        label_lines = re.split(r"[\n\r]+", plain)
        lat = lon = None
        for line in label_lines:
            line = line.strip()
            m = re.search(
                r"(?:LÄNGENGRAD|LAENGENGRAD|BREITENGRAD|LATITUDE|LONGITUDE)"
                r"\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)\s*([NSEW])\b",
                line,
                re.IGNORECASE,
            )
            if not m:
                continue
            value = float(m.group(1).replace(",", "."))
            direction = m.group(2).upper()
            if direction in {"N", "S"} and -90 <= value <= 90:
                lat = -abs(value) if direction == "S" else abs(value)
            elif direction in {"E", "W"} and -180 <= value <= 180:
                lon = -abs(value) if direction == "W" else abs(value)
        if lat is not None and lon is not None:
            return lat, lon

        # Fallback for layouts where the two coordinate lines are not separated
        # by HTML <br> tags.  Keep the direction tied to the number immediately
        # following each coordinate label.
        labelled_dir = re.findall(
            r"(?:LÄNGENGRAD|LAENGENGRAD|BREITENGRAD|LATITUDE|LONGITUDE)"
            r"\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)\s*([NSEW])\b",
            plain,
            re.IGNORECASE,
        )
        lat = lon = None
        for value_text, direction in labelled_dir:
            value = float(value_text.replace(",", "."))
            direction = direction.upper()
            if direction in {"N", "S"} and -90 <= value <= 90:
                lat = -abs(value) if direction == "S" else abs(value)
            elif direction in {"E", "W"} and -180 <= value <= 180:
                lon = -abs(value) if direction == "W" else abs(value)
        if lat is not None and lon is not None:
            return lat, lon

        # Labelled German/English values without compass letters. Here the
        # normal semantic labels are used as a fallback.
        lat_match = re.search(r"(?:BREITENGRAD|LATITUDE|\bLAT\b)\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)", plain)
        lon_match = re.search(r"(?:LÄNGENGRAD|LAENGENGRAD|LONGITUDE|\bLON\b)\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)", plain)
        if lat_match and lon_match:
            lat = float(lat_match.group(1).replace(",", "."))
            lon = float(lon_match.group(1).replace(",", "."))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon

        pair = re.search(
            r"(?<![A-Z0-9])(-?\d{1,3}(?:[.,]\d{3,8})?)\s*[,;]\s*"
            r"(-?\d{1,3}(?:[.,]\d{3,8})?)(?![A-Z0-9])", plain
        )
        if pair:
            lat = float(pair.group(1).replace(",", "."))
            lon = float(pair.group(2).replace(",", "."))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
        return None

    @classmethod
    def _timestamp_from_block(cls, block):
        """Return the timestamp carried by a MeshCom message/position card.

        Prefer the timestamp supplied by the WebService instead of the local
        refresh time. This is important because the map refreshes repeatedly;
        refreshing must never make every station appear to have been heard at
        the same moment.
        """
        # HTML datetime/data attributes and <time datetime="...">.
        attr_patterns = (
            r'(?:data-(?:timestamp|time|datetime)|datetime|timestamp)\s*=\s*[\"\']([^\"\']+)',
        )
        for pattern in attr_patterns:
            m = re.search(pattern, block, re.IGNORECASE)
            if m:
                value = html.unescape(m.group(1)).strip()
                # ISO date/time -> local display format.
                try:
                    iso = value.replace('Z', '+00:00')
                    dt = datetime.fromisoformat(iso)
                    return dt.astimezone().strftime('%H:%M:%S')
                except Exception:
                    hm = re.search(r'\b([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?\b', value)
                    if hm:
                        return hm.group(0) if len(hm.group(0).split(':')) == 3 else hm.group(0) + ':00'

        plain = cls._plain(block)
        # Prefer a full date/time if present.
        m = re.search(r'\b(?:20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}[ T]+)?([01]\d|2[0-3]):([0-5]\d)(?::([0-5]\d))?\b', plain)
        if m:
            return f"{m.group(1)}:{m.group(2)}:{m.group(3) or '00'}"
        return ''

    @classmethod
    def _station_position_from_block(cls, block):
        coords = cls._coordinates_from_block(block)
        if not coords:
            return None
        plain = cls._plain(block).upper()
        # Prefer the callsign explicitly following "Von:" / "From:" because
        # position cards may also contain a message ID or other callsigns.
        sender = re.search(r"(?:VON|FROM)\s*:\s*([A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?)", plain)
        calls = cls._normalize_callsign(sender.group(1)) if sender else ""
        if not calls:
            calls = cls._normalize_callsign(plain)
        return (calls, coords[0], coords[1]) if calls else None

    def _map_html(self, stations):
        import json
        station_json = json.dumps(stations, ensure_ascii=False)
        html_page = """<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>
<link rel='stylesheet' href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'><style>html,body,#map{height:100%;margin:0}</style></head>
<body><div id='map'></div><script src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'></script><script>
const initialStations=__STATIONS__;
const map=L.map('map').setView([51,10],6);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap-Mitwirkende'}).addTo(map);
const markerLayer=L.layerGroup().addTo(map);
let firstRender=true;
function esc(v){return String(v).replace(/[&<>]/g,'');}
function renderStations(stations){
  const hadStations=markerLayer.getLayers().length>0;
  markerLayer.clearLayers();
  stations.forEach(s=>{const m=L.marker([s.lat,s.lon]).addTo(markerLayer);const heard=s.last_heard?'<br><b>Zuletzt gehört:</b> '+esc(s.last_heard):'';
    m.bindPopup('<b>'+esc(s.callsign)+'</b><br>Breite: '+Number(s.lat).toFixed(6)+'<br>Länge: '+Number(s.lon).toFixed(6)+heard+(s.own?'<br><b>Eigene Station</b>':''));
  });
  setTimeout(()=>map.invalidateSize(),50);
  if(firstRender && !hadStations){
    const bounds=stations.map(s=>[s.lat,s.lon]);
    if(bounds.length===1) map.setView(bounds[0],10);
    else if(bounds.length>1) map.fitBounds(bounds,{padding:[30,30]});
  }
  firstRender=false;
}
window.updateStations=function(stations){renderStations(stations||[]);};
renderStations(initialStations);</script></body></html>"""
        return html_page.replace('__STATIONS__', station_json)

    def _map_load_finished(self, ok):
        self._map_ready = bool(ok)
        if self._map_ready:
            self._push_map_stations(self._map_pending_stations)

    def _push_map_stations(self, stations):
        if QWebEngineView is None or not hasattr(self, "map_view"):
            return
        self._map_pending_stations = list(stations or [])
        if not self._map_ready:
            return
        import json
        station_json = json.dumps(self._map_pending_stations, ensure_ascii=False)
        self.map_view.page().runJavaScript(
            f"if (typeof window.updateStations === 'function') window.updateStations({station_json});"
        )

    def _update_map(self):
        if QWebEngineView is None or not hasattr(self, "map_view"):
            return
        stations=[]
        for callsign,(lat,lon) in sorted(self.station_positions.items()):
            stations.append({"callsign":callsign,"lat":lat,"lon":lon,"own":callsign.upper()==self.own_callsign.upper(),"last_heard":self.station_last_heard.get(callsign.upper(),"")})
        if self.own_lat is not None and self.own_lon is not None:
            own_call=self.own_callsign
            stations=[s for s in stations if s["callsign"].upper()!=own_call.upper()]
            stations.insert(0,{"callsign":own_call,"lat":self.own_lat,"lon":self.own_lon,"own":True})
        # Die Karte wird nicht neu geladen. Die Stationsdaten werden jedoch
        # gepuffert, bis Leaflet/JavaScript nach setHtml() vollständig bereit ist.
        self._push_map_stations(stations)

    # ---------- Refresh ----------
    def update_messages(self):
        if self.refresh_in_progress:
            return
        self.refresh_in_progress = True
        try:
            page = self.mesh.get_messages()
            blocks = self._extract_message_blocks(page)
            if not blocks:
                # Keep compatibility with nodes that return the message HTML directly.
                blocks = [page] if page.strip() else []

            # Positions werden ausschließlich direkt über die eigene UDP-
            # Schnittstelle übernommen.
            for block in blocks:
                position = self._station_position_from_block(block)
                if position:
                    callsign, lat, lon = position
                    key = callsign.upper()
                    self.station_positions[key] = (lat, lon)
                    signature = hashlib.sha1(self._plain(block).encode("utf-8", errors="ignore")).hexdigest()
                    if self.station_last_heard_signature.get(key) != signature:
                        self.station_last_heard_signature[key] = signature
                        heard = self._timestamp_from_block(block)
                        if heard:
                            self.station_last_heard[key] = heard
            self._update_map()

            self._ensure_room_tabs()
            # Der HTTP-Nachrichtenstrom bleibt für Chat/Privatnachrichten zuständig.
            # UDP-Positionsdaten werden separat und in Echtzeit verarbeitet.
            display_blocks = blocks
            visible_blocks = self._filter_blocks(display_blocks)

            # Configured room tabs.
            for room in self._rooms():
                key = ("room", room)
                idx = self._ensure_tab(key, f"Raum {room}")
                room_blocks = self._room_blocks(blocks, room)
                self._update_tab_content(key, idx, room_blocks)

            # Bereits geöffnete Privat-Tabs weiter aktualisieren.
            # Neue Privat-Tabs entstehen NICHT mehr aus normalen Raum-Nachrichten.
            # Automatisch angelegt werden sie nur, wenn der betreffende Block keine
            # Raum-ID besitzt und damit tatsächlich wie eine Direktnachricht aussieht.
            private_targets = set()
            for block in blocks:
                # A private tab is created only for a real direct message.
                # The FIRST callsign of CALL1>CALL2 is the sender and is the
                # name of the automatic private-chat tab.
                participants = self._private_participants(block)
                if participants:
                    # Das eigene Node-Echo einer gerade gesendeten Privatnachricht
                    # darf keinen neuen Privat-Tab erzeugen. Eingehende Privat-
                    # nachrichten werden weiterhin ganz normal automatisch geöffnet.
                    if self._is_own_private_echo(block):
                        continue
                    sender = participants[0]
                    # Das eigene Rufzeichen darf niemals durch das vom Node
                    # zurückgelieferte Echo oder einen Header als neuer
                    # eingehender Privat-Chat geöffnet werden.
                    if self.own_callsign and sender.upper() == self.own_callsign.upper():
                        continue
                    if not CALLSIGN_RE.fullmatch(sender):
                        continue

                    sender_key = sender.upper()
                    closed_hash = self.closed_private.get(sender_key)
                    if closed_hash is not None:
                        # Nur den bereits gesehenen/geschlossenen Nachrichtenstand
                        # unterdrücken. Wenn sich der Inhalt inzwischen geändert hat,
                        # ist tatsächlich eine neue Nachricht eingetroffen: Tab wieder
                        # öffnen und den alten Schließ-Marker entfernen.
                        closed_rendered = self._render_blocks(self._private_blocks(blocks, sender))
                        closed_digest = hashlib.sha1(
                            closed_rendered.encode("utf-8", errors="ignore")
                        ).hexdigest()
                        if closed_digest == closed_hash:
                            continue
                        self.closed_private.pop(sender_key, None)
                    private_targets.add(sender)

            # Bereits vorhandene Privat-Tabs dürfen weiterlaufen.
            for key in list(self.tab_keys):
                if key[0] == "private":
                    private_targets.add(key[1].upper())

            for target in private_targets:
                key = ("private", target)
                is_new = key not in self.tab_keys
                idx = self._ensure_tab(key, target)
                private_blocks = self._private_blocks(blocks, target)
                self._update_tab_content(key, idx, private_blocks)
                if is_new and private_blocks and self.tabs.currentIndex() != idx:
                    self._set_tab_unread(key)

            # Tab „Alle“ wird ausschließlich aus dem AKTUELLEN WebService-
            # Nachrichtenstrom aufgebaut. Die Raum- und Privat-Tabs bleiben
            # davon vollständig getrennt. Das ist wichtig: Eine Nachricht darf
            # nicht einmal aus einem Raum-Tab und ein zweites Mal aus einem
            # Privat-Tab bzw. aus der lokalen Sofortanzeige übernommen werden.
            all_key = ("all", "all")
            all_index = self._ensure_tab(all_key, "Alle")

            def _all_identity(block):
                plain = self._plain(block)
                # MsgId ist die sauberste Identität einer MeshCom-Nachricht.
                msgid = re.search(r"\bMSGID\s*[:=]\s*([0-9A-F]+)", plain, re.IGNORECASE)
                if msgid:
                    return ("msgid", msgid.group(1).upper())
                # Fallback: normalisierter kompletter Inhalt. Der Zeitstempel
                # bleibt dabei erhalten, sodass zwei echte gleiche Texte zu
                # unterschiedlichen Zeiten nicht zusammengelegt werden.
                return ("text", re.sub(r"\s+", " ", plain).strip())

            # Jeder WebService-Block wird genau einmal übernommen.
            all_blocks = []
            seen_all = set()
            for block in blocks:
                key = _all_identity(block)
                if key in seen_all:
                    continue
                seen_all.add(key)
                all_blocks.append(block)

            # Zusätzlich bekannte UDP-Positionskarten übernehmen, aber ebenfalls
            # nur einmal. Die Positionsdaten selbst werden unabhängig davon in
            # station_positions für die Karte gepflegt.
            for block in self.udp_position_blocks:
                key = _all_identity(block)
                if key in seen_all:
                    continue
                seen_all.add(key)
                all_blocks.append(block)

            # Eine eigene lokale Kopie wird NICHT mehr zusätzlich angezeigt.
            # Der Hotspot liefert die gesendete Nachricht über den WebService
            # zurück. Genau diese eine Servermeldung ist die maßgebliche Anzeige
            # und verhindert die bisherige Doppelanzeige bei normalen UND privaten
            # Nachrichten.
            self.local_all_messages.clear()

            # Chronologisch sortieren. Dadurch stehen Nachrichten nach ihrem
            # tatsächlichen WebService-Zeitstempel und nicht nach dem Zeitpunkt
            # des lokalen Sendeklicks.
            all_blocks.sort(key=lambda b: self._timestamp_from_block(b) or "99:99:99")

            self._update_tab_content(all_key, all_index, all_blocks)

            # Scroll every chat to the newest message.
            for i in range(self.tabs.count()):
                view = self.tabs.widget(i)
                if isinstance(view, ChatView):
                    view.scroll_to_bottom()

            if self.filter_enabled.isChecked():
                rooms = self._rooms()
                self.status.setText("Nachrichten aktualisiert – Filter: " + (", ".join(rooms) if rooms else "keine Räume"))
            else:
                self.status.setText("Nachrichten aktualisiert – alle Räume")
        except Exception as exc:
            self.status.setText(f"Abruf fehlgeschlagen: {exc}")
        finally:
            self.refresh_in_progress = False

    def _update_tab_content(self, key, index, blocks):
        view = self.tabs.widget(index)
        if not isinstance(view, ChatView):
            return
        rendered = self._render_blocks(blocks)
        digest = hashlib.sha1(rendered.encode("utf-8", errors="ignore")).hexdigest()
        changed = self.tab_hashes.get(key) not in ("", digest) and self.tab_hashes.get(key) != digest
        self.tab_hashes[key] = digest
        view.setHtml(rendered)
        view.scroll_to_bottom()
        if changed and self.tabs.currentIndex() != index:
            self._set_tab_unread(key)

    # ---------- Send ----------
    def send(self):
        text = self.message_input.text().strip()
        target = self.target_input.text().strip()
        if not text:
            self.status.setText("Keine Nachricht eingegeben")
            return
        if len(text) > 149:
            self.status.setText("Nachricht darf maximal 149 Zeichen lang sein")
            return

        self.send_button.setEnabled(False)
        try:
            _answer, _url, method = self.mesh.send_message(text, target)
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.last_sent = text
            self.last_sent_time = timestamp
            self.last_private_sent = (target.upper(), text) if target and not target.isdigit() else None

            # Keine lokale Kopie mehr erzeugen. Die eigene Nachricht wird nach
            # der Hotspot-Rückmeldung aus demselben WebService-Strom wie alle
            # anderen Nachrichten angezeigt. Dadurch kann sie unter „Alle“ nicht
            # ein zweites Mal auftauchen.

            self.send_log.setText(f"Letzter Sendeauftrag {timestamp}: → {target} | {text} | HTTP {method} 200")
            self.status.setText("Sendeauftrag an den Hotspot übertragen – warte auf Node-Rückmeldung")
            self.message_input.clear()

            # Bei leerem Ziel bleibt der Tab „Alle“ aktiv.
            # Wichtig: Kein künstlicher Privat-Tab für ein leeres Ziel
            # und kein sofortiger Refresh, der das aktuelle Chatfenster
            # mit einer leeren Serverantwort überschreiben könnte.
            if target:
                if target.isdigit():
                    key = ("room", target)
                    idx = self._ensure_tab(key, f"Raum {target}")
                else:
                    key = ("private", target.upper())
                    # Wurde dieser Privat-Tab vorher bewusst geschlossen und
                    # wird jetzt wieder an dasselbe Ziel gesendet, soll der
                    # Tab sofort wieder erscheinen. Der alte Schließ-Marker
                    # darf den erneuten Versand nicht blockieren.
                    self.closed_private.pop(target.upper(), None)
                    idx = self._ensure_tab(key, target.upper())
                self.tabs.setCurrentIndex(idx)
                QTimer.singleShot(1500, self.update_messages)
        except Exception as exc:
            self.status.setText(f"Senden fehlgeschlagen: {exc}")
            self.send_log.setText("Letzter Sendeauftrag: FEHLER – " + str(exc))
        finally:
            self.send_button.setEnabled(True)

    def closeEvent(self, event):
        try:
            self._write_settings()
        finally:
            event.accept()

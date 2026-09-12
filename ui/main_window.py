import configparser
import hashlib
import math
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

from PySide6.QtCore import QTimer, Qt, QUrl, Signal, QPointF, QRectF, QTranslator, QLibraryInfo
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except Exception:
    QWebEngineView = None
try:
    from PySide6.QtMultimedia import QSoundEffect
except Exception:
    QSoundEffect = None
from PySide6.QtGui import QAction, QTextCursor, QDesktopServices, QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QFileDialog,
    QCheckBox,
    QColorDialog,
    QFormLayout,
    QAbstractItemView,
    QHeaderView,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSlider,
    QSizePolicy,
    QMainWindow,
    QMenu,
    QScrollArea,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QTableWidget,
    QTableWidgetItem,
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


from i18n import tr, set_language, ui_text

class BubbleWidget(QWidget):
    """Compact WhatsApp-style message bubble with a small inward tail."""
    def __init__(self, text, outgoing=False, parent=None):
        super().__init__(parent)
        self.outgoing = outgoing
        self.bg = QColor("#78d86b" if outgoing else "#4d98e8")
        self.border = QColor("#6bc65f" if outgoing else "#4186ce")
        self.label = QLabel()
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setWordWrap(True)
        self.label.setOpenExternalLinks(False)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)
        self.label.setStyleSheet("background: transparent; color: #081018; border: none;")
        self.label.linkActivated.connect(self._link_activated)
        layout = QVBoxLayout(self)
        if outgoing:
            layout.setContentsMargins(14, 9, 20, 9)
        else:
            layout.setContentsMargins(20, 9, 14, 9)
        layout.addWidget(self.label)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.setMinimumHeight(48)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def _link_activated(self, url):
        w = self.window()
        if hasattr(w, "_bubble_link_activated"):
            w._bubble_link_activated(url)

    def set_content(self, text, max_width):
        self.setFixedWidth(max_width)
        self.label.setMaximumWidth(max(120, max_width - 34))
        self.label.setText(text)
        self.label.adjustSize()
        self.adjustSize()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = self.rect().adjusted(8, 1, -8, -1)
        p.setPen(QPen(self.border, 1))
        p.setBrush(self.bg)
        p.drawRoundedRect(QRectF(r), 18, 18)
        if self.outgoing:
            tail = QPolygonF([
                QPointF(r.right() - 1, r.bottom() - 18),
                QPointF(self.width() - 1, r.bottom() - 11),
                QPointF(r.right() - 1, r.bottom() - 7),
            ])
        else:
            tail = QPolygonF([
                QPointF(r.left() + 1, r.bottom() - 18),
                QPointF(1, r.bottom() - 11),
                QPointF(r.left() + 1, r.bottom() - 7),
            ])
        p.drawPolygon(tail)
        p.end()
        super().paintEvent(event)


class ChatView(QScrollArea):
    callsignClicked = Signal(str)

    @staticmethod
    def _normalize_color(value):
        color = QColor(str(value or "#101722").strip())
        return color.name(QColor.NameFormat.HexRgb) if color.isValid() else "#101722"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chat_background = "#101722"
        self.chat_text_color = "#e6edf3"
        self._bubble_mode = False
        self._all_mode = False
        self._bubble_rows = []

        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._apply_scroll_style()

        # Normal room/private HTML view (kept for compatibility).
        self._html_view = QTextBrowser()
        self._html_view.setReadOnly(True)
        self._html_view.setOpenLinks(False)
        self._html_view.setOpenExternalLinks(False)
        self._html_view.anchorClicked.connect(self._anchor_clicked)
        self._html_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._html_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._apply_html_style()

        self._bubble_container = QWidget()
        self._bubble_layout = QVBoxLayout(self._bubble_container)
        self._bubble_layout.setContentsMargins(10, 8, 10, 8)
        self._bubble_layout.setSpacing(8)
        self.setWidget(self._html_view)

    def _apply_scroll_style(self):
        self.setStyleSheet(
            f"QScrollArea {{ background: {self.chat_background}; border: none; }} "
            "QScrollBar:vertical { width: 12px; }"
        )
        self.viewport().setStyleSheet(f"background: {self.chat_background};")

    def _apply_html_style(self):
        self._html_view.setStyleSheet(
            f"QTextBrowser {{ background: {self.chat_background}; color: {self.chat_text_color}; border: none; }}"
        )

    def set_chat_colors(self, background, text):
        """Apply chat colors without changing the actual message layout."""
        self.chat_background = self._normalize_color(background)
        self.chat_text_color = self._normalize_color(text)
        self._apply_scroll_style()
        self._apply_html_style()
        if hasattr(self, "_bubble_container"):
            self._bubble_container.setStyleSheet(f"background: {self.chat_background};")
        for browser in getattr(self, "_all_message_views", []):
            browser.setStyleSheet(
                f"QTextBrowser {{ background: {self.chat_background}; color: {self.chat_text_color}; border: none; }}"
            )
        self.viewport().update()
        self.update()

    def _anchor_clicked(self, url):
        value = url.toString().strip()
        if value.startswith("meshcom://call/"):
            self.callsignClicked.emit(value.rsplit("/", 1)[-1])
        elif value.startswith(("http://", "https://")):
            QDesktopServices.openUrl(url)

    def _bubble_link_activated(self, url):
        self._anchor_clicked(QUrl(str(url)))

    def set_chat_background(self, color):
        self.chat_background = self._normalize_color(color)
        self._apply_scroll_style()
        self._apply_html_style()
        if hasattr(self, "_bubble_container"):
            self._bubble_container.setStyleSheet(f"background: {self.chat_background};")
        for browser in getattr(self, "_all_message_views", []):
            browser.setStyleSheet(
                f"QTextBrowser {{ background: {self.chat_background}; color: {self.chat_text_color}; border: none; }}"
            )
        self.viewport().update()
        self.update()

    def set_all_html(self, html_text):
        """Display the complete 'Alle' document bottom-anchored with normal scrolling.

        The important point is that the QTextBrowser itself is NOT the scroll
        container here.  It is rendered at its real document height inside an
        outer QScrollArea.  A layout stretch puts short histories at the bottom;
        once the history is taller than the viewport, the outer scrollbar behaves
        like a normal chat scrollbar.
        """
        old_bar = self.verticalScrollBar()
        old_value = old_bar.value()
        old_max = old_bar.maximum()
        was_at_bottom = old_max <= 0 or old_value >= max(0, old_max - 8)

        self._all_mode = True
        self._bubble_mode = False
        self._all_message_views = []

        container = QWidget()
        container.setStyleSheet(f"background: {self.chat_background};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(0)

        # A single document keeps the existing 'Alle' rendering 1:1.
        browser = QTextBrowser()
        browser.setReadOnly(True)
        browser.setOpenLinks(False)
        browser.setOpenExternalLinks(False)
        browser.anchorClicked.connect(self._anchor_clicked)
        browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        browser.setStyleSheet(
            f"QTextBrowser {{ background: {self.chat_background}; color: {self.chat_text_color}; border: none; padding: 0; }}"
        )
        browser.setHtml(str(html_text))
        self._all_message_views.append(browser)
        layout.addStretch(1)
        layout.addWidget(browser, 0)
        self.setWidget(container)
        self._all_container = container
        self._all_layout = layout

        def finalize():
            if not self._all_mode or self.widget() is not container:
                return
            width = max(100, self.viewport().width() - 20)
            browser.setFixedWidth(width)
            doc = browser.document()
            doc.setTextWidth(max(80, width - 4))
            doc.adjustSize()
            # QTextDocument height is in pixels after the width is fixed.
            h = max(24, int(doc.size().height()) + 6)
            browser.setFixedHeight(h)
            layout.activate()
            # Ensure the outer content is at least the viewport height. The
            # stretch then moves even ONE message to the bottom.
            container.setMinimumHeight(max(self.viewport().height(), h + 16))
            container.updateGeometry()
            layout.activate()
            new_bar = self.verticalScrollBar()
            if was_at_bottom:
                new_bar.setValue(new_bar.maximum())
            else:
                new_bar.setValue(min(old_value, new_bar.maximum()))

        QTimer.singleShot(0, finalize)
        QTimer.singleShot(50, finalize)

    def setHtml(self, html_text, *args):
        # Normal HTML mode for compatibility with non-'Alle' views.
        self._all_mode = False
        self._bubble_mode = False
        bar = self._html_view.verticalScrollBar()
        old_value = bar.value()
        old_max = bar.maximum()
        was_at_bottom = old_max <= 0 or old_value >= max(0, old_max - 8)
        self._apply_html_style()
        self._html_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setWidget(self._html_view)
        self._html_view.setHtml(str(html_text))

        def restore():
            new_bar = self._html_view.verticalScrollBar()
            if was_at_bottom:
                new_bar.setValue(new_bar.maximum())
            else:
                new_bar.setValue(min(old_value, new_bar.maximum()))
        QTimer.singleShot(0, restore)

    def set_bubbles(self, items):
        """Render chat bubbles in one QTextDocument instead of QWidget rows.

        This deliberately avoids rebuilding/replacing a QWidget bubble tree.
        The QTextBrowser itself stays the permanent child of the QScrollArea;
        only its document is replaced when the actual rendered message list
        changes.  This keeps the first received message visible while avoiding
        the geometry churn caused by repeatedly replacing the bubble container.
        """
        self._all_mode = False
        self._bubble_mode = True

        browser = self._html_view
        old_bar = browser.verticalScrollBar()
        old_value = old_bar.value()
        old_max = old_bar.maximum()
        was_at_bottom = old_max <= 0 or old_value >= max(0, old_max - 8)

        self._apply_html_style()
        browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        browser.setReadOnly(True)
        browser.setOpenLinks(False)
        browser.setOpenExternalLinks(False)
        self.setWidget(browser)

        width = max(260, int(self.viewport().width() * 0.75))
        bubble_parts = []
        for item in items:
            content = str(item.get("html", ""))
            outgoing = bool(item.get("outgoing", False))
            if outgoing:
                bg = "#78d86b"
                border = "#6bc65f"
                align = "right"
                pad = "10px 18px 10px 14px"
            else:
                bg = "#4d98e8"
                border = "#4186ce"
                align = "left"
                pad = "10px 14px 10px 18px"
            bubble_parts.append(
                f"<div style='width:100%; margin:0 0 8px 0; text-align:{align};'>"
                f"<table cellspacing='0' cellpadding='0' style='margin:0 0 0 auto;'"
                f" align='{align}'><tr><td style='background:{bg}; border:1px solid {border};"
                f" border-radius:18px; padding:{pad}; color:#081018;'>"
                f"{content}</td></tr></table></div>"
            )

        if bubble_parts:
            html = (
                "<html><body style='margin:0; padding:8px 10px; background:"
                + self.chat_background
                + ";'>"
                + "".join(bubble_parts)
                + "</body></html>"
            )
        else:
            html = (
                "<html><body style='margin:0; padding:18px; background:"
                + self.chat_background
                + "; color:" + self.chat_text_color + ";'>"
                "Keine Nachrichten.</body></html>"
            )

        # Keep one QTextDocument alive.  There is no QWidget/layout teardown.
        browser.setHtml(html)
        doc = browser.document()
        doc.setTextWidth(max(100, self.viewport().width() - 20))

        def restore():
            if not self._bubble_mode or self.widget() is not browser:
                return
            bar = browser.verticalScrollBar()
            if was_at_bottom:
                bar.setValue(bar.maximum())
            else:
                bar.setValue(min(old_value, bar.maximum()))

        QTimer.singleShot(0, restore)

    def _update_bubble_container_height(self):
        if not self._bubble_mode:
            return
        self._bubble_layout.activate()
        needed = self._bubble_layout.sizeHint().height()
        viewport_h = max(0, self.viewport().height())
        self._bubble_container.setMinimumHeight(max(viewport_h, needed))
        self._bubble_container.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._all_mode and hasattr(self, "_all_container"):
            QTimer.singleShot(0, self._refresh_all_geometry)
        if self._bubble_mode:
            width = max(260, int(self.viewport().width() * 0.75))
            for bubble in self._bubble_rows:
                bubble.set_content(bubble.label.text(), width)
            self._update_bubble_container_height()

    def _refresh_all_geometry(self):
        if not self._all_mode or not getattr(self, "_all_message_views", None):
            return
        browser = self._all_message_views[0]
        if self.widget() is not self._all_container:
            return
        width = max(100, self.viewport().width() - 20)
        browser.setFixedWidth(width)
        doc = browser.document()
        doc.setTextWidth(max(80, width - 4))
        doc.adjustSize()
        browser.setFixedHeight(max(24, int(doc.size().height()) + 6))
        self._all_container.setMinimumHeight(max(self.viewport().height(), browser.height() + 16))
        self._all_layout.activate()

    def scroll_to_bottom(self):
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class MainWindow(QMainWindow):
    udpPacketReceived = Signal(dict)
    weatherUpdated = Signal(dict)
    @staticmethod
    def _normalize_chat_color(value):
        """Return a valid #RRGGBB color for chat settings."""
        try:
            color = QColor(str(value or "#101722").strip())
            if color.isValid():
                return color.name(QColor.NameFormat.HexRgb)
        except Exception:
            pass
        return "#101722"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"MeshCom-Guru v{VERSION}")
        self.resize(1100, 930)
        self.setMinimumSize(900, 930)

        settings = load_settings()
        self.language = settings.get("language", "de") if settings.get("language", "de") in ("de", "en") else "de"
        set_language(self.language)
        # Let Qt translate its own standard context menus (Undo/Copy/Paste/...).
        # This is safer than intercepting ContextMenu events with a global
        # event filter and avoids shutdown/segmentation-fault side effects.
        self._qt_translator = QTranslator(self)
        self._qt_translator_loaded = False
        self._apply_qt_translation(self.language)
        self.chat_background = self._normalize_chat_color(settings.get("chat_background", "#101722"))
        self.chat_text_color = self._normalize_chat_color(settings.get("chat_text_color", "#e6edf3"))
        self._all_chat_views = []
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
        # Verbindungsanzeige: Beginn der aktuell bestehenden HTTP-Verbindung.
        self.connection_online = False
        self.connection_since = None
        self.refresh_in_progress = False
        self.last_sent = None
        self.last_sent_time = None
        # Merkt die zuletzt von diesem Client gesendete Direktnachricht.
        # Der Node liefert das eigene Echo ebenfalls zurück; dieses Echo darf
        # keinen neuen Privat-Tab für das eigene Rufzeichen erzeugen.
        self.last_private_sent = None
        # Punkt 2: eigene Sendungen nur für die Sendebestätigung merken.
        self.outgoing_messages = []
        # Schnelltexte: aus settings.ini laden und dauerhaft speichern.
        self.quick_texts = self._load_quick_texts(settings)
        # Nur für den Gesamtstrom „Alle“: eigene Sendungen lokal merken.
        self.local_all_messages = []
        # Lokaler Nachrichtenpuffer: Der WebService liefert je nach Node/
        # Dashboard teilweise nur ein begrenztes Zeitfenster. Nachrichten, die
        # bereits einmal empfangen wurden, dürfen deshalb beim nächsten Refresh
        # nicht aus der lokalen Anzeige verschwinden. Die Darstellung wird bei
        # jedem Refresh aus diesem Puffer aufgebaut.
        self.message_cache = {}
        # Beim Programmstart werden die bereits vom WebService vorhandenen
        # Nachrichten nur als Startbestand gemerkt. Sie sollen nach einem
        # Neustart nicht wieder in den Raum-Tabs erscheinen. Erst Nachrichten,
        # die nach diesem ersten Abgleich neu eintreffen, werden übernommen.
        self.startup_message_identities = set()
        self.initial_message_sync_done = False
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
        # Monitor: reine Anzeige des bereits empfangenen UDP-Datenstroms.
        self.monitor_rows = []
        self.monitor_paused = False
        self.monitor_filter = "ALLE"
        self.monitor_search = ""
        self.monitor_autoscroll = True
        # MH-Liste: Most Recently Heard. Nur aus dem bereits empfangenen
        # UDP-Datenstrom aufgebaut; die bestehende POS-/Monitor-Verarbeitung
        # bleibt davon getrennt.
        self.mh_stations = {}
        self.udpPacketReceived.connect(self._handle_udp_packet)
        self.own_callsign = settings.get("own_callsign", "").strip().upper()
        try:
            self.own_lat = float(settings.get("own_lat", ""))
            self.own_lon = float(settings.get("own_lon", ""))
        except (TypeError, ValueError):
            self.own_lat = None
            self.own_lon = None

        # Verbindungssteuerung: WebService erst nach Klick auf "Verbinden".
        self.connected = False

        self._build_menu()
        self._build_ui(settings)
        self._apply_language_ui()
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
        # Keine automatische Verbindung beim Programmstart.
        # Der Benutzer entscheidet mit "Verbinden", wann der WebService abgefragt wird.

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

    @staticmethod
    def _monitor_value(packet, *names):
        for name in names:
            if name in packet and packet.get(name) not in (None, ""):
                return packet.get(name)
        return ""

    def _monitor_telemetry_data(self, packet, msg):
        data = packet.get("data")
        if isinstance(data, dict):
            return data
        if not msg:
            return {}
        candidates = [msg]
        start, end = msg.find("{"), msg.rfind("}")
        if start >= 0 and end > start:
            candidates.append(msg[start:end + 1])
        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
        return {}

    @staticmethod
    def _monitor_num(value, digits=1, suffix=""):
        if value in (None, ""):
            return ""
        try:
            return f"{float(value):.{digits}f}{suffix}"
        except (TypeError, ValueError):
            return f"{value}{suffix}"

    def _monitor_add_packet(self, packet):
        """Only display an already received UDP packet; never alter packet handling."""
        if self.monitor_paused:
            return
        ptype_raw = str(packet.get("type", packet.get("packet_type", "")) or "").strip().lower()
        msg = str(self._monitor_value(packet, "msg", "message") or "")
        if ptype_raw in {"ack", "acknowledgement", "delivery_ack"} or re.search(r":ack\d{1,6}\b", msg, re.I):
            ptype = "ACK"
        elif ptype_raw in {"msg", "message"}:
            ptype = "MSG"
        elif ptype_raw in {"pos", "position", "gps"}:
            ptype = "POS"
        elif ptype_raw in {"tel", "tele", "telemetry", "status"}:
            ptype = "TEL"
        else:
            ptype = ptype_raw.upper()[:8] or "UDP"

        src = self._udp_callsign(packet.get("src", "")) or str(packet.get("src", "") or "-")
        dst = str(packet.get("dst", packet.get("target", "")) or "-").strip()
        rssi = self._monitor_value(packet, "rssi", "RSSI", "signal")
        snr = self._monitor_value(packet, "snr", "SNR")

        if ptype == "MSG":
            detail = msg or "Nachricht"
            seq = re.search(r"\{(\d{1,6})\}?", detail)
            ack = re.search(r":ack(\d{1,6})\b", detail, re.I)
            if seq:
                detail = re.sub(r"\{\d{1,6}\}?", "", detail).strip()
                detail = f"#{seq.group(1)}  {detail}" if detail else f"#{seq.group(1)}"
            elif ack:
                detail = f"{src} :ack{ack.group(1)}"
        elif ptype == "ACK":
            ack = re.search(r":ack(\d{1,6})\b", msg, re.I)
            detail = f"{src} :ack{ack.group(1)}" if ack else (msg or "ACK")
        elif ptype == "POS":
            coords = self._udp_coordinate(packet)
            detail = f"{coords[0]:.6f}, {coords[1]:.6f}" if coords else (msg or "Position")
            alt = self._monitor_value(packet, "alt", "altitude", "height")
            batt = self._monitor_value(packet, "batt", "battery")
            extra = []
            if alt != "":
                extra.append(f"Höhe {self._monitor_num(alt, 0)} m")
            if batt != "":
                extra.append(f"Batt {self._monitor_num(batt, 0)} %")
            if extra:
                detail += "  ·  " + "  ·  ".join(extra)
        elif ptype == "TEL":
            data = self._monitor_telemetry_data(packet, msg)
            def val(key, *aliases):
                for k in (key, *aliases):
                    v = packet.get(k, data.get(k, ""))
                    if v not in (None, ""):
                        return v
                return ""
            parts = []
            temp = val("temp", "temperature", "temp1")
            hum = val("hum", "humidity")
            qfe = val("qfe")
            qnh = val("qnh")
            co2 = val("co2")
            gas = val("gas")
            hum0 = val("hum0")
            temp2 = val("temp2")
            batt = val("batt", "battery")
            volt = val("volt", "voltage")
            if temp != "": parts.append(f"Temperatur {self._monitor_num(temp, 1)} °C")
            if hum != "": parts.append(f"Luftfeuchte {self._monitor_num(hum, 1)} %")
            if qfe != "": parts.append(f"QFE {self._monitor_num(qfe, 1)} hPa")
            if qnh != "": parts.append(f"QNH {self._monitor_num(qnh, 1)} hPa")
            if co2 != "": parts.append(f"CO₂ {self._monitor_num(co2, 0)} ppm")
            if gas != "": parts.append(f"Gas {self._monitor_num(gas, 0)}")
            if hum0 != "": parts.append(f"Hum {self._monitor_num(hum0, 0)}")
            if temp2 != "": parts.append(f"Temp2 {self._monitor_num(temp2, 1)} °C")
            if batt != "": parts.append(f"Batt {self._monitor_num(batt, 0)} %")
            if volt != "": parts.append(f"Volt {self._monitor_num(volt, 2)} V")
            detail = "  ·  ".join(parts) or "Telemetry"
        else:
            detail = msg or json.dumps(packet, ensure_ascii=False, separators=(",", ":"))

        # Eine eigene gesendete Nachricht soll sofort im Monitor erscheinen.
        # Kommt kurz danach das EXTUDP-Echo vom Node, wird der lokale Eintrag
        # nur ergänzt statt doppelt angezeigt. Alle anderen Monitor-Pakete
        # bleiben unverändert.
        if ptype == "MSG":
            own = str(self.own_callsign or "").strip().upper()
            if own and str(src).strip().upper() == own:
                for existing in reversed(self.monitor_rows):
                    if existing.get("type") != "MSG" or existing.get("_local_send") is not True:
                        continue
                    if str(existing.get("src", "")).strip().upper() != own:
                        continue
                    existing_dst = str(existing.get("dst", "")).strip().upper()
                    current_dst = str(dst).strip().upper()
                    # Das EXTUDP-Echo kann als Ziel "*" oder ohne Ziel kommen.
                    # In diesem Fall trotzdem mit der direkt angezeigten eigenen
                    # Nachricht zusammenführen, damit sie nicht doppelt erscheint.
                    if existing_dst not in {"", "-", "*"} and current_dst not in {"", "-", "*", existing_dst}:
                        continue
                    if detail.replace("#", "", 1).strip().casefold().endswith(str(existing.get("_text", "")).strip().casefold()):
                        existing["detail"] = detail
                        existing["rssi"] = str(rssi) if rssi != "" else existing.get("rssi", "-")
                        existing["snr"] = str(snr) if snr != "" else existing.get("snr", "-")
                        self._render_monitor()
                        return

        self.monitor_rows.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": ptype,
            "src": str(src),
            "dst": dst,
            "rssi": str(rssi) if rssi != "" else "-",
            "snr": str(snr) if snr != "" else "-",
            "detail": detail,
        })
        self.monitor_rows = self.monitor_rows[-500:]
        self._render_monitor()

    def _render_monitor(self):
        if not hasattr(self, "monitor_table"):
            return
        rows = self.monitor_rows
        if self.monitor_filter != "ALLE":
            rows = [r for r in rows if r["type"] == self.monitor_filter]
        search = self.monitor_search.strip().lower()
        if search:
            rows = [r for r in rows if search in " ".join(str(r[k]) for k in ("time", "type", "src", "dst", "detail")).lower()]

        self.monitor_table.setRowCount(len(rows))
        badge_colors = {
            "MSG": "#2f79bd", "POS": "#2f8a5a", "TEL": "#2d8a8a",
            "ACK": "#7656c5", "UDP": "#566274",
        }
        for row_index, row in enumerate(rows):
            values = [row["time"], row["type"], row["src"], row["dst"], row["rssi"], row["snr"], row["detail"]]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.monitor_table.setItem(row_index, col, item)
            badge = self.monitor_table.item(row_index, 1)
            badge.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setForeground(QColor("#ffffff"))
            badge.setBackground(QColor(badge_colors.get(row["type"], "#566274")))
            for col in (4, 5):
                self.monitor_table.item(row_index, col).setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        self.monitor_count_label.setText(ui_text(f"{len(rows)} angezeigt · {len(self.monitor_rows)} gespeichert"))
        if self.monitor_autoscroll and rows:
            self.monitor_table.scrollToBottom()

    def _set_monitor_filter(self, value):
        self.monitor_filter = value
        self._render_monitor()

    def _set_monitor_search(self, text):
        self.monitor_search = text
        self._render_monitor()

    def _toggle_monitor_autoscroll(self, checked):
        self.monitor_autoscroll = checked
        if checked:
            self.monitor_table.scrollToBottom()

    def _toggle_monitor_pause(self):
        self.monitor_paused = not self.monitor_paused
        self.monitor_pause_button.setText(ui_text("▶ Weiter" if self.monitor_paused else "⏸ Pause"))

    def _clear_monitor(self):
        self.monitor_rows.clear()
        self._render_monitor()

    def _mh_distance_km(self, lat, lon):
        try:
            if self.own_lat is None or self.own_lon is None:
                return None
            r = 6371.0088
            p1 = math.radians(float(self.own_lat))
            p2 = math.radians(float(lat))
            dp = math.radians(float(lat) - float(self.own_lat))
            dl = math.radians(float(lon) - float(self.own_lon))
            a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
            return r * 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1 - a)))
        except (TypeError, ValueError):
            return None

    def _update_mh_from_packet(self, packet):
        """Update one MH station from an already received EXTUDP packet."""
        if not isinstance(packet, dict):
            return
        callsign = self._udp_callsign(packet.get("src", ""))
        if not callsign:
            return
        if callsign.upper() == str(self.own_callsign or "").upper():
            return

        # OE1XAR test/gateway entries are not part of the MH station list.
        if callsign.upper() in {"OE1XAR-33", "OE1XAR-62"}:
            return

        ptype = str(packet.get("type", packet.get("packet_type", "")) or "").strip().lower()
        if ptype not in {"msg", "message", "pos", "position", "gps", "tele", "tel", "telemetry", "status", "ack", "acknowledgement", "delivery_ack"}:
            return

        now = datetime.now().strftime("%H:%M:%S")
        row = self.mh_stations.setdefault(callsign, {
            "callsign": callsign, "lat": None, "lon": None,
            "rssi": None, "snr": None, "battery": None,
            "last_heard": now, "alt": None, "firmware": "",
        })
        row["last_heard"] = now

        rssi = self._monitor_value(packet, "rssi", "RSSI", "signal")
        snr = self._monitor_value(packet, "snr", "SNR")
        if rssi not in (None, ""):
            row["rssi"] = rssi
        if snr not in (None, ""):
            row["snr"] = snr

        coords = self._udp_coordinate(packet)
        if coords:
            row["lat"], row["lon"] = coords
        alt = self._monitor_value(packet, "alt", "altitude", "height")
        batt = self._monitor_value(packet, "batt", "battery")
        if alt not in (None, ""):
            row["alt"] = alt
        if batt not in (None, ""):
            row["battery"] = batt
        fw = self._monitor_value(packet, "firmware", "fw", "version")
        if fw not in (None, ""):
            row["firmware"] = str(fw)

        self._render_mh()

    @staticmethod
    def _mh_format_distance(km):
        if km is None:
            return "-"
        try:
            km = float(km)
        except (TypeError, ValueError):
            return "-"
        if km < 1:
            return f"{round(km * 1000)} m"
        return f"{km:.1f} km"

    @staticmethod
    def _mh_format_signal(value, suffix=""):
        if value in (None, ""):
            return "-"
        try:
            return f"{float(value):g}{suffix}"
        except (TypeError, ValueError):
            return str(value)

    def _update_statistics(self):
        """Aktualisiert die Sitzungsstatistik ohne zusätzliche Netzwerkabfragen."""
        if not hasattr(self, "statistics_summary"):
            return

        message_count = len(self.message_cache)
        node_count = len(self.mh_stations)
        position_count = len(self.station_positions)
        monitor_count = len(self.monitor_rows)

        private_count = 0
        room_counts = {}
        for block in self.message_cache.values():
            participants = self._private_participants(block)
            if participants:
                private_count += 1
                continue
            text = self._plain(block)
            m = re.search(r"\b(?:Raum|room)\s*[:#]?\s*(\d+)\b", text, re.I)
            if m:
                room = m.group(1)
                room_counts[room] = room_counts.get(room, 0) + 1

        self.statistics_summary.setText(
            f"{ui_text('Nachrichten:')} <b>{message_count}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"{ui_text('Nodes:')} <b>{node_count}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"{ui_text('Positionen:')} <b>{position_count}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"{ui_text('Privatnachrichten:')} <b>{private_count}</b><br>"
            f"{ui_text('Monitor-Einträge:')} <b>{monitor_count}</b>"
        )

        if room_counts:
            room_label = ui_text("Raum")
            parts = [f"{room_label} {room}: <b>{count}</b>" for room, count in sorted(room_counts.items(), key=lambda x: int(x[0]))]
            self.statistics_room_label.setText("<b>" + ui_text("Nachrichten nach Raum:") + "</b><br>" + " &nbsp;&nbsp; | &nbsp;&nbsp; ".join(parts))
        else:
            self.statistics_room_label.setText("<b>" + ui_text("Nachrichten nach Raum:") + "</b> " + ui_text("noch keine Daten"))

    def _render_mh(self):
        if not hasattr(self, "mh_table"):
            return
        rows = sorted(self.mh_stations.values(), key=lambda r: r.get("last_heard", ""), reverse=True)
        self.mh_table.setRowCount(len(rows))
        for i, station in enumerate(rows):
            distance = self._mh_distance_km(station.get("lat"), station.get("lon")) if station.get("lat") is not None else None
            values = [
                station.get("callsign", ""),
                self._mh_format_distance(distance),
                self._mh_format_signal(station.get("rssi"), " dBm"),
                self._mh_format_signal(station.get("snr"), " dB"),
                self._mh_format_signal(station.get("battery"), " %"),
                station.get("last_heard", "-"),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col in (1, 2, 3, 4):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.mh_table.setItem(i, col, item)
        if hasattr(self, "mh_count_label"):
            self.mh_count_label.setText(ui_text(f"{len(rows)} Station(en)"))

    def _clear_mh(self):
        self.mh_stations.clear()
        self._render_mh()

    def _handle_udp_packet(self, packet):
        status = packet.get("_status") if isinstance(packet, dict) else None
        if status:
            self.udp_status = status
            return
        if not isinstance(packet, dict):
            return
        self._monitor_add_packet(packet)
        self._update_mh_from_packet(packet)
        # Diagnose den direkten UDP-Empfang unabhängig von der Kartenanzeige.
        try:
            debug_file = Path(__file__).resolve().parent.parent / "data" / "udp_received.log"
            with debug_file.open("a", encoding="utf-8") as fh:
                fh.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + json.dumps(packet, ensure_ascii=False) + "\n")
        except Exception:
            pass
        ptype = str(packet.get("type", packet.get("packet_type", ""))).lower().strip()
        callsign = self._udp_callsign(packet.get("src", ""))

        # Punkt 2 – ausschließlich den EXTUDP-MSG-Strom für die Sendebestätigung
        # auswerten. POS/Koordinaten bleiben darunter unverändert.
        if ptype in {"msg", "message"}:
            packet_text = str(packet.get("msg", packet.get("message", "")) or "")
            src_text = str(packet.get("src", "") or "").upper()
            own_text = str(self.own_callsign or "").upper()

            # Eigenes Node-Echo: Nachricht{NNN} -> ✓
            seq_match = re.search(r"\{(\d{1,6})\}?", packet_text)
            if own_text and own_text in src_text and seq_match:
                clean_text = re.sub(r"\{\d{1,6}\}?", "", packet_text).strip()
                self._mark_outgoing_echo(clean_text, seq_match.group(1), packet.get("dst", ""))

            # Empfänger-ACK: CALL :ackNNN -> ✓✓
            ack_match = re.search(r":ack(\d{1,6})\b", packet_text, re.IGNORECASE)
            if ack_match:
                self._mark_outgoing_ack(ack_match.group(1))

            if seq_match or ack_match:
                self._refresh_visible_ack_states()

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
            self.status.setText(ui_text(f"Position empfangen: {callsign} {coords[0]:.6f}, {coords[1]:.6f} | {self.udp_status}"))
            return
        # Textpakete werden weiterhin über HTTP dargestellt; UDP dient hier
        # vor allem dazu, Positions-/Statuspakete in Echtzeit zu übernehmen.

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

        language_action = QAction("Sprache / Language …", self)
        language_action.triggered.connect(self.open_language_dialog)
        settings_menu.addAction(language_action)
        self.language_action = language_action

        sound_action = QAction("Sound-Einstellungen", self)
        sound_action.triggered.connect(self.open_sound_settings)
        settings_menu.addAction(sound_action)

        chat_bg_action = QAction("Chat-Farben …", self)
        chat_bg_action.triggered.connect(self._choose_chat_background)
        settings_menu.addAction(chat_bg_action)
        self.chat_bg_action = chat_bg_action

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
        # Verbindungsstatus links und Uhr/Datum rechts in derselben Zeile.
        # Alle drei Anzeigen bewusst gleich groß/fett, damit sie auch bei
        # kleiner Fensterbreite gut lesbar bleiben.
        self.connection_label = QLabel()
        self.connection_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.connection_label.setMinimumWidth(230)
        self.connection_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.connection_label.setStyleSheet("font-size: 12pt; font-weight: 700;")

        self.datetime_label = QLabel()
        self.datetime_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.datetime_label.setMinimumWidth(260)
        self.datetime_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.datetime_label.setStyleSheet("font-size: 12pt; font-weight: 700;")

        self.connect_button = QPushButton(ui_text("🔗 Verbinden"))
        self.connect_button.setFixedWidth(125)
        self.connect_button.setToolTip(ui_text("Mit dem MeshCom-WebService verbinden"))
        self.connect_button.clicked.connect(self.connect_mesh)

        self.disconnect_button = QPushButton(ui_text("⛓️ Trennen"))
        self.disconnect_button.setFixedWidth(110)
        self.disconnect_button.setToolTip(ui_text("Verbindung zum MeshCom-WebService trennen"))
        self.disconnect_button.clicked.connect(self.disconnect_mesh)
        self.disconnect_button.setEnabled(False)

        top_row = QHBoxLayout()
        top_row.addWidget(self.connection_label)
        top_row.addSpacing(8)
        top_row.addWidget(self.connect_button)
        top_row.addWidget(self.disconnect_button)
        top_row.addStretch(1)
        top_row.addWidget(self.datetime_label)
        self._set_connection_status(False)

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
        self.weather_city_input.setPlaceholderText(ui_text("Stadtname, z. B. Bielefeld"))
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

        # ---------- 📡 Monitor ----------
        # Eigenständige Anzeige des UDP-Datenstroms; die bestehende
        # Nachrichten-, POS-, Karten- und ACK-Verarbeitung bleibt unverändert.
        self.monitor_view = QWidget()
        monitor_layout = QVBoxLayout(self.monitor_view)
        monitor_layout.setContentsMargins(6, 6, 6, 6)
        monitor_toolbar = QHBoxLayout()

        self.monitor_pause_button = QPushButton("⏸ Pause")
        self.monitor_pause_button.setFixedWidth(92)
        self.monitor_pause_button.clicked.connect(self._toggle_monitor_pause)
        monitor_toolbar.addWidget(self.monitor_pause_button)

        monitor_clear_button = QPushButton("Leeren")
        monitor_clear_button.setFixedWidth(78)
        monitor_clear_button.clicked.connect(self._clear_monitor)
        monitor_toolbar.addWidget(monitor_clear_button)

        monitor_toolbar.addWidget(QLabel("Filter:"))
        self.monitor_filter_combo = QComboBox()
        self.monitor_filter_combo.addItems(["ALLE", "MSG", "POS", "TEL", "ACK"])
        self.monitor_filter_combo.setFixedWidth(78)
        self.monitor_filter_combo.currentTextChanged.connect(self._set_monitor_filter)
        monitor_toolbar.addWidget(self.monitor_filter_combo)

        self.monitor_search_edit = QLineEdit()
        self.monitor_search_edit.setPlaceholderText("Suchen …")
        self.monitor_search_edit.setMinimumWidth(130)
        self.monitor_search_edit.setMaximumWidth(190)
        self.monitor_search_edit.textChanged.connect(self._set_monitor_search)
        monitor_toolbar.addWidget(self.monitor_search_edit)

        self.monitor_autoscroll_check = QCheckBox("Auto-Scroll")
        self.monitor_autoscroll_check.setChecked(True)
        self.monitor_autoscroll_check.toggled.connect(self._toggle_monitor_autoscroll)
        monitor_toolbar.addWidget(self.monitor_autoscroll_check)
        monitor_toolbar.addStretch(1)
        self.monitor_count_label = QLabel("0 angezeigt · 0 gespeichert")
        monitor_toolbar.addWidget(self.monitor_count_label)
        monitor_toolbar.addWidget(QLabel("MSG / POS / TEL / ACK"))
        monitor_layout.addLayout(monitor_toolbar)

        self.monitor_table = QTableWidget(0, 7)
        self.monitor_table.setHorizontalHeaderLabels(["Zeit", "Typ", "Von", "Nach", "RSSI", "SNR", "Information"])
        self.monitor_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.monitor_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.monitor_table.setAlternatingRowColors(False)
        self.monitor_table.setWordWrap(False)
        self.monitor_table.verticalHeader().setVisible(False)
        self.monitor_table.setShowGrid(True)
        header = self.monitor_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.monitor_table.setMinimumHeight(170)
        monitor_layout.addWidget(self.monitor_table, 1)

        self.monitor_tab_index = self.tabs.insertTab(self.map_tab_index + 1, self.monitor_view, "📡 Monitor")
        self.tabs.tabBar().setTabButton(
            self.monitor_tab_index,
            self.tabs.tabBar().ButtonPosition.RightSide,
            None,
        )

        # ---------- 📋 MH – Most Recently Heard ----------
        self.mh_view = QWidget()
        mh_layout = QVBoxLayout(self.mh_view)
        mh_layout.setContentsMargins(6, 6, 6, 6)
        mh_toolbar = QHBoxLayout()
        self.mh_count_label = QLabel("0 Station(en)")
        mh_toolbar.addWidget(self.mh_count_label)
        mh_toolbar.addStretch(1)
        mh_clear_button = QPushButton("Leeren")
        mh_clear_button.setFixedWidth(78)
        mh_clear_button.clicked.connect(self._clear_mh)
        mh_toolbar.addWidget(mh_clear_button)
        mh_layout.addLayout(mh_toolbar)

        self.mh_table = QTableWidget(0, 6)
        self.mh_table.setHorizontalHeaderLabels(["Rufzeichen", "Entfernung", "RSSI", "SNR", "Batterie", "Zuletzt gehört"])
        self.mh_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.mh_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.mh_table.setAlternatingRowColors(False)
        self.mh_table.setWordWrap(False)
        self.mh_table.verticalHeader().setVisible(False)
        self.mh_table.setShowGrid(True)
        mh_header = self.mh_table.horizontalHeader()
        mh_header.setStretchLastSection(True)
        for col in range(6):
            mh_header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        mh_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.mh_table.setMinimumHeight(170)
        mh_layout.addWidget(self.mh_table, 1)

        self.mh_tab_index = self.tabs.insertTab(self.monitor_tab_index + 1, self.mh_view, "📋 MH")
        self.tabs.tabBar().setTabButton(
            self.mh_tab_index,
            self.tabs.tabBar().ButtonPosition.RightSide,
            None,
        )
        self._render_mh()

        # ---------- 📊 Statistik ----------
        # Fester Tab ohne Schließen-X. Die Statistik verwendet ausschließlich
        # Daten, die MeshCom-Guru bereits während der laufenden Sitzung kennt.
        self.statistics_view = QWidget()
        statistics_layout = QVBoxLayout(self.statistics_view)
        statistics_layout.setContentsMargins(12, 12, 12, 12)
        statistics_layout.setSpacing(10)

        stats_title = QLabel(ui_text("📊 MeshCom-Guru Statistik"))
        stats_title.setStyleSheet("font-size: 14pt; font-weight: 700;")
        statistics_layout.addWidget(stats_title)

        self.statistics_summary = QLabel()
        self.statistics_summary.setWordWrap(True)
        self.statistics_summary.setStyleSheet("font-size: 11pt;")
        statistics_layout.addWidget(self.statistics_summary)

        self.statistics_room_label = QLabel()
        self.statistics_room_label.setWordWrap(True)
        self.statistics_room_label.setStyleSheet("font-size: 10.5pt;")
        statistics_layout.addWidget(self.statistics_room_label)

        statistics_layout.addStretch(1)

        self.statistics_tab_index = self.tabs.insertTab(
            self.mh_tab_index + 1, self.statistics_view, ui_text("📊 Statistik")
        )
        # Statistik ist ein fester Tab und darf nicht geschlossen werden.
        self.tabs.tabBar().setTabButton(
            self.statistics_tab_index,
            self.tabs.tabBar().ButtonPosition.RightSide,
            None,
        )
        self._update_statistics()

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Nachricht eingeben …")
        self.message_input.setMaxLength(149)

        # Schnelltexte: auswählbar, bearbeitbar und um neue Einträge erweiterbar.
        self.quick_text_button = QPushButton("⚡ Schnelltexte")
        self.quick_text_button.setFixedWidth(120)
        self.quick_text_button.setToolTip("Schnelltext auswählen oder bearbeiten")
        self.quick_text_button.clicked.connect(self._open_quick_texts)

        # Emoji-Auswahl für Nachrichten. Die Auswahl ist bewusst lokal und
        # verändert die bestehende Sende-/Empfangslogik nicht.
        self.emoji_button = QPushButton("😊")
        self.emoji_button.setFixedWidth(46)
        self.emoji_button.setToolTip("Emoji einfügen")
        self.emoji_button.clicked.connect(self._toggle_emoji_picker)
        self._emoji_picker = None

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
        message_row.addWidget(self.quick_text_button)
        message_row.addWidget(self.emoji_button)
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

    def _load_quick_texts(self, settings):
        """Load persistent quick texts, with useful defaults on first start."""
        defaults = [
            "CQ CQ",
            "73",
            "Danke für das QSO",
            "Bin QRV",
            "QTH ...",
            "Kommt gut an",
            "Bis später",
            "Viele Grüße",
        ]
        values = []
        for i, default in enumerate(defaults, 1):
            value = str(settings.get(f"quick_text{i}", "")).strip()
            values.append(value or default)
        # Zusätzliche gespeicherte Einträge ab Nummer 9 laden.
        i = len(defaults) + 1
        while i <= 50:
            value = str(settings.get(f"quick_text{i}", "")).strip()
            if not value:
                break
            values.append(value[:149])
            i += 1
        return values

    def _open_quick_texts(self):
        """Show editable quick texts with insert, add and delete controls."""
        dialog = QDialog(self)
        dialog.setWindowTitle("⚡ Schnelltexte bearbeiten")
        dialog.setModal(True)
        dialog.setMinimumWidth(620)

        layout = QVBoxLayout(dialog)
        info = QLabel(
            "Schnelltexte hier bearbeiten. Mit „Einfügen“ wird der Text nur ins Nachrichtenfeld übernommen – nicht automatisch gesendet."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        rows_layout = QVBoxLayout()
        layout.addLayout(rows_layout)
        fields = []

        def add_row(text=""):
            if len(fields) >= 50:
                return
            row = QHBoxLayout()
            field = QLineEdit(str(text))
            field.setMaxLength(149)
            field.setPlaceholderText("Schnelltext eingeben …")
            insert_button = QPushButton("Einfügen")
            delete_button = QPushButton("Löschen")
            row.addWidget(field, 1)
            row.addWidget(insert_button)
            row.addWidget(delete_button)
            rows_layout.addLayout(row)
            fields.append(field)

            insert_button.clicked.connect(
                lambda checked=False, f=field: self._use_quick_text(f.text(), dialog)
            )

            def remove_row():
                if field not in fields:
                    return
                fields.remove(field)
                field.deleteLater()
                insert_button.deleteLater()
                delete_button.deleteLater()
                row.setEnabled(False)

            delete_button.clicked.connect(remove_row)

        for text in self.quick_texts:
            add_row(text)

        add_button = QPushButton("＋ Schnelltext hinzufügen")
        add_button.clicked.connect(lambda: add_row(""))
        layout.addWidget(add_button)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(lambda: self._save_quick_texts(fields, dialog))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        self._apply_language_ui()
        dialog.exec()

    def _use_quick_text(self, text, dialog=None):
        """Insert a quick text into the message field without sending it."""
        text = str(text or "").strip()[:149]
        if not text:
            return
        self.message_input.setText(text)
        self.message_input.setFocus()
        self.message_input.setCursorPosition(len(text))
        if dialog is not None:
            dialog.accept()

    def _save_quick_texts(self, fields, dialog):
        values = [field.text().strip()[:149] for field in fields if field.text().strip()]
        self.quick_texts = values
        self._write_settings()
        self.status.setText(ui_text("Schnelltexte gespeichert"))
        dialog.accept()

    def _toggle_emoji_picker(self):
        """Open/close the compact emoji picker above the message field."""
        if self._emoji_picker is not None and self._emoji_picker.isVisible():
            self._emoji_picker.close()
            return

        picker = QDialog(self, Qt.WindowType.Popup)
        picker.setWindowTitle("Emoji")
        picker.setModal(False)
        picker.setFixedWidth(440)
        picker.setMaximumHeight(315)

        emojis = [
            "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣",
            "😊", "😇", "🙂", "🙃", "😉", "😌", "😍", "🥰",
            "😘", "😎", "🤩", "🤔", "😐", "😏", "😢", "😭",
            "😡", "😱", "👍", "👎", "👏", "🙌", "🙏", "💪",
            "❤️", "💯", "🔥", "⭐", "🎉", "☀️", "☕", "🍺",
            "🚗", "🚲", "🏠", "📡", "📍", "🌍", "⛰️", "🐕",
        ]

        grid = QGridLayout(picker)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(5)
        grid.setVerticalSpacing(5)

        for i, emoji in enumerate(emojis):
            button = QPushButton(emoji)
            button.setFixedSize(50, 46)
            button.setStyleSheet("font-size: 23px; padding: 0px;")
            button.setToolTip(f"{emoji} einfügen")
            button.clicked.connect(lambda checked=False, value=emoji: self._insert_emoji(value))
            grid.addWidget(button, i // 8, i % 8)

        self._emoji_picker = picker
        picker.finished.connect(lambda _result: self._clear_emoji_picker())

        # Das Fenster erscheint direkt über der Eingabezeile.
        pos = self.emoji_button.mapToGlobal(self.emoji_button.rect().topLeft())
        x = max(0, pos.x() - picker.width() + self.emoji_button.width())
        y = max(0, pos.y() - picker.maximumHeight() - 6)
        picker.move(x, y)
        picker.show()

    def _insert_emoji(self, emoji):
        """Insert an emoji at the current cursor position."""
        if len(self.message_input.text()) + len(emoji) > 149:
            self.status.setText(ui_text("Emoji passt nicht mehr in die 149 Zeichen"))
            return
        self.message_input.insert(emoji)
        if self._emoji_picker is not None and self._emoji_picker.isVisible():
            self._emoji_picker.close()
        self.message_input.setFocus()

    def _clear_emoji_picker(self):
        self._emoji_picker = None

    def _load_filter_fields(self, settings):
        for i, field in enumerate(self.filter_inputs, 1):
            field.setText(settings.get(f"filter_room{i}", ""))
        self._ensure_room_tabs()

    def _set_connection_status(self, online):
        """Update the clearly visible connection status and online duration."""
        online = bool(online)
        now = datetime.now()
        if online and not self.connection_online:
            self.connection_since = now
        elif not online:
            self.connection_since = None
        self.connection_online = online
        self._update_connection_label(now)

    def _update_connection_label(self, now=None):
        if not hasattr(self, "connection_label"):
            return
        now = now or datetime.now()
        if self.connection_online and self.connection_since is not None:
            elapsed = max(0, int((now - self.connection_since).total_seconds()))
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.connection_label.setText(f"🟢 {ui_text('ONLINE  |  seit')} {duration}")
            self.connection_label.setStyleSheet("font-size: 12pt; font-weight: 700; color: #20e060;")
        else:
            self.connection_label.setText("🔴 " + ui_text("OFFLINE  |  keine Verbindung"))
            self.connection_label.setStyleSheet("font-size: 12pt; font-weight: 700; color: #ff3b30;")

    def _update_clock(self):
        now = datetime.now()
        self.datetime_label.setText(now.strftime("%d.%m.%Y  |  %H:%M:%S"))
        self.datetime_label.setStyleSheet("font-size: 12pt; font-weight: 700;")
        self._update_connection_label(now)

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

    # ---------- Chat-Farben ----------
    def _update_chat_color_preview(self, preview, background, text):
        background = self._normalize_chat_color(background)
        text = self._normalize_chat_color(text)
        preview.setStyleSheet(
            f"QTextBrowser {{ background: {background}; color: {text}; "
            "border: 1px solid #777; border-radius: 6px; padding: 8px; }}"
        )
        preview.setHtml(
            f"<div style='color:{text};'><b>16:25&nbsp;&nbsp;DB0ABC:</b> Hallo zusammen!</div>"
            f"<div style='color:{text}; margin-top:6px;'><b>16:26&nbsp;&nbsp;DL1ABC:</b> 73 und schönen Abend!</div>"
            f"<div style='color:{text}; margin-top:6px;'><b>16:27&nbsp;&nbsp;DB0ABC:</b> Dies ist die Vorschau.</div>"
        )

    def _choose_chat_background(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Chat-Farben")
        dialog.resize(520, 430)
        layout = QVBoxLayout(dialog)

        info = QLabel("Gemeinsame Farben für alle Räume und Chat-Ansichten:")
        layout.addWidget(info)

        preview = QTextBrowser(dialog)
        preview.setReadOnly(True)
        preview.setMinimumHeight(120)
        preview.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(preview)

        bg_row = QHBoxLayout()
        bg_label = QLabel("Chat-Hintergrund:")
        bg_preview = QLabel()
        bg_preview.setFixedSize(70, 30)
        bg_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bg_button = QPushButton("🎨 Farbe auswählen …")
        bg_row.addWidget(bg_label)
        bg_row.addWidget(bg_preview)
        bg_row.addWidget(bg_button, 1)
        layout.addLayout(bg_row)

        text_row = QHBoxLayout()
        text_label = QLabel("Schriftfarbe für „Alle“:")
        text_preview = QLabel()
        text_preview.setFixedSize(70, 30)
        text_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_button = QPushButton("✏️ Farbe auswählen …")
        text_row.addWidget(text_label)
        text_row.addWidget(text_preview)
        text_row.addWidget(text_button, 1)
        layout.addLayout(text_row)

        reset = QPushButton("🔄 Standard wiederherstellen")
        layout.addWidget(reset)

        def refresh():
            bg = self.chat_background
            fg = self.chat_text_color
            bg_preview.setText(bg)
            bg_preview.setStyleSheet(f"background:{bg}; color:{'#ffffff' if QColor(bg).lightness() < 160 else '#000000'}; border:1px solid #777; border-radius:5px;")
            text_preview.setText(fg)
            text_preview.setStyleSheet(f"background:{bg}; color:{fg}; border:1px solid #777; border-radius:5px;")
            self._update_chat_color_preview(preview, bg, fg)

        def pick_bg():
            color = QColorDialog.getColor(QColor(self.chat_background), dialog, "Chat-Hintergrundfarbe")
            if color.isValid():
                self._set_chat_colors_live(background=color.name(QColor.NameFormat.HexRgb))
                refresh()

        def pick_text():
            color = QColorDialog.getColor(QColor(self.chat_text_color), dialog, "Chat-Schriftfarbe")
            if color.isValid():
                self._set_chat_colors_live(text=color.name(QColor.NameFormat.HexRgb))
                refresh()

        def do_reset():
            self._set_chat_colors_live(background="#000000", text="#ffffff")
            refresh()

        bg_button.clicked.connect(pick_bg)
        text_button.clicked.connect(pick_text)
        reset.clicked.connect(do_reset)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        refresh()
        self._apply_language_ui()
        dialog.exec()

    def _set_chat_colors_live(self, background=None, text=None):
        if background is not None:
            self.chat_background = self._normalize_chat_color(background)
        if text is not None:
            self.chat_text_color = self._normalize_chat_color(text)
        self._write_settings()

        views = []
        for view in getattr(self, "_all_chat_views", []):
            if view is not None and view not in views:
                views.append(view)
        for i in range(self.tabs.count()):
            view = self.tabs.widget(i)
            if view is not None and hasattr(view, "set_chat_colors") and view not in views:
                views.append(view)
        for view in views:
            try:
                view.set_chat_colors(self.chat_background, self.chat_text_color)
            except Exception:
                pass
        self.status.setText(
            f"Chat-Farben geändert: Hintergrund {self.chat_background} (alle Chats), Schrift {self.chat_text_color} (nur „Alle“) – {len(views)} Ansichten"
        )

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
        section["chat_background"] = self.chat_background
        section["chat_text_color"] = self.chat_text_color
        section["language"] = self.language if getattr(self, "language", "de") in ("de", "en") else "de"
        section["sound_enabled"] = "1" if self.sound_enabled else "0"
        section["sound_driver"] = self.sound_driver
        section["sound_volume"] = str(self.sound_volume)
        section["sound_file"] = self.sound_file
        # Schnelltexte dauerhaft in settings.ini speichern.
        for i in range(1, 51):
            key = f"quick_text{i}"
            if key in section:
                del section[key]
        for i, text in enumerate(getattr(self, "quick_texts", []), 1):
            section[f"quick_text{i}"] = text[:149]
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

    def open_language_dialog(self):
        """Show a small, explicit Deutsch/English language selector."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("language_title"))
        layout = QVBoxLayout(dialog)
        label = QLabel(tr("language"))
        combo = QComboBox()
        combo.addItem(tr("german"), "de")
        combo.addItem(tr("english"), "en")
        combo.setCurrentIndex(0 if getattr(self, "language", "de") == "de" else 1)
        layout.addWidget(label)
        layout.addWidget(combo)
        button = QPushButton("OK")
        button.clicked.connect(dialog.accept)
        layout.addWidget(button)
        self._apply_language_ui()
        if dialog.exec():
            self._set_ui_language(combo.currentData())

    def _apply_qt_translation(self, language):
        app = QApplication.instance()
        if app is None:
            return
        if self._qt_translator_loaded:
            app.removeTranslator(self._qt_translator)
            self._qt_translator_loaded = False
        # English is Qt's source language, so no Qt translator is needed.
        if language != "de":
            return
        try:
            path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
            if self._qt_translator.load("qtbase_de", path):
                app.installTranslator(self._qt_translator)
                self._qt_translator_loaded = True
        except Exception:
            pass

    def _set_ui_language(self, language):
        """Save and immediately apply the selected UI language."""
        language = language if language in ("de", "en") else "de"
        self.language = language
        set_language(language)
        self._apply_qt_translation(language)
        self._write_settings()
        self._apply_language_ui()
        self.status.setText(tr("Einstellungen gespeichert"))

    def _apply_language_ui(self):
        """Translate visible static UI elements without touching user/received data."""
        try:
            # Menus and actions
            for action in self.findChildren(QAction):
                text = action.text()
                if text:
                    action.setText(ui_text(text))
                tip = action.toolTip()
                if tip:
                    action.setToolTip(ui_text(tip))
            for menu in self.findChildren(QMenu):
                if menu.title():
                    menu.setTitle(ui_text(menu.title()))
        except Exception:
            pass

        # Static widgets
        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QPushButton, QLabel, QCheckBox)):
                text = widget.text() if hasattr(widget, "text") else ""
                if text:
                    widget.setText(ui_text(text))
            if isinstance(widget, QLineEdit):
                ph = widget.placeholderText()
                if ph:
                    widget.setPlaceholderText(ui_text(ph))
            tip = widget.toolTip()
            if tip:
                widget.setToolTip(ui_text(tip))

        # Combo-box labels/items
        for combo in self.findChildren(QComboBox):
            for i in range(combo.count()):
                combo.setItemText(i, ui_text(combo.itemText(i)))

        # Tab labels: only static UI tabs are translated; private callsigns stay untouched.
        if hasattr(self, "tabs"):
            for i in range(self.tabs.count()):
                title = self.tabs.tabText(i)
                if title == "Alle" or title == "All":
                    self.tabs.setTabText(i, tr("Alle"))
                elif title.startswith("Raum ") or title.startswith("Room "):
                    num = title.split()[-1]
                    self.tabs.setTabText(i, ("Room " if self.language == "en" else "Raum ") + num)
                elif title == "Karte" or title == "Map":
                    self.tabs.setTabText(i, tr("Karte"))
                elif title == "📡 Monitor":
                    self.tabs.setTabText(i, tr("📡 Monitor"))
                elif title == "📋 MH":
                    self.tabs.setTabText(i, tr("📋 MH"))

            # Statistik-Tab muss beim Sprachwechsel sofort umbenannt werden.
            # Da der aktuelle Tab-Titel bereits "📊 Statistics" sein kann,
            # reicht eine reine Prüfung auf den deutschen Ausgangstext nicht.
            if hasattr(self, "statistics_view"):
                stats_idx = self.tabs.indexOf(self.statistics_view)
                if stats_idx >= 0:
                    self.tabs.setTabText(stats_idx, ui_text("📊 Statistik"))

        # Table headers
        if hasattr(self, "monitor_table"):
            self.monitor_table.setHorizontalHeaderLabels([ui_text(x) for x in ["Zeit", "Typ", "Von", "Nach", "RSSI", "SNR", "Information"]])
        if hasattr(self, "mh_table"):
            self.mh_table.setHorizontalHeaderLabels([ui_text(x) for x in ["Rufzeichen", "Entfernung", "RSSI", "SNR", "Batterie", "Zuletzt gehört"]])

    def save_all_settings(self):
        ip = self.ip_input.text().strip().rstrip("/")
        if not ip:
            self.status.setText(ui_text("Fehler: Keine Hotspot-IP eingetragen"))
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
            self.status.setText(ui_text("Fehler: Ungültige eigene Koordinaten"))
            return
        self.own_callsign = self._normalize_callsign(self.own_callsign_input.text())
        self.own_lat, self.own_lon = lat, lon
        self._write_settings()
        self.mesh = MeshCom(ip)
        self._set_connection_status(False)
        self._ensure_room_tabs()
        self._update_map()
        self.status.setText(ui_text("Einstellungen gespeichert"))

    def save_filter_settings(self):
        self._write_settings()
        self._ensure_room_tabs()
        self.update_messages()
        rooms = self._rooms()
        self.status.setText(ui_text("Filter gespeichert: " + (", ".join(rooms) if rooms else "keine Räume")))

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
            self.weather_values_label.setText(ui_text("Keine Wetterwerte in der WX-Information gefunden"))
            self.weather_status_label.setText(ui_text("Keine Hotspot-IP eingetragen"))
            return
        self._weather_fetch_in_progress = True
        self.weather_refresh_button.setEnabled(False)
        self.weather_status_label.setText(ui_text("WX-Information wird geladen …"))
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
            self.weather_values_label.setText(ui_text("Keine Wetterwerte in der WX-Information gefunden"))
            self.weather_status_label.setText(str(data["error"]))
            return
        self.weather_data = data
        self.weather_values_label.setText(
            f"{ui_text('Temperatur:')} {data.get('temperature', '–')} | "
            f"{ui_text('Luftfeuchte:')} {data.get('humidity', '–')} | "
            f"{ui_text('QFE:')} {data.get('qfe', '–')} | "
            f"{ui_text('QNH:')} {data.get('qnh', '–')}"
        )
        self.weather_status_label.setText(ui_text("WX-Information erfolgreich aus dem MeshCom-WebService gelesen"))

    def _send_weather(self):
        if not self.weather_data:
            self.status.setText(ui_text("Keine Wetterdaten vorhanden – zuerst Wetter aktualisieren"))
            return
        city = self.weather_city_input.text().strip()
        if not city:
            self.status.setText(ui_text("Bitte zuerst einen Stadtnamen eingeben"))
            return
        text = (
            f"{city}: {self.weather_data.get('temperature', '–')} | "
            f"Luftfeuchte {self.weather_data.get('humidity', '–')} | "
            f"QFE {self.weather_data.get('qfe', '–')} | "
            f"QNH {self.weather_data.get('qnh', '–')}"
        )
        if len(text) > 149:
            self.status.setText(ui_text("Wettermeldung ist länger als 149 Zeichen"))
            return
        # Wetterdaten immer an das Ziel des aktuell geöffneten Chats senden.
        # Dadurch gehen sie nicht mehr grundsätzlich an "alle":
        # Raum-Tab -> Raum, Privat-Tab -> Rufzeichen, Tab "Alle" -> leer/all.
        current_index = self.tabs.currentIndex()
        current_key = self._key_for_index(current_index)
        if current_key and current_key[0] in {"room", "private"}:
            weather_target = current_key[1]
        elif current_key and current_key[0] == "all":
            weather_target = ""
        else:
            # Fallback für sonstige Tabs (z. B. Karte): das bisherige
            # Eingabefeld verwenden, ohne das bestehende Sendeverhalten
            # anderer Nachrichten zu verändern.
            weather_target = self.target_input.text().strip()

        self.weather_send_button.setEnabled(False)
        try:
            _answer, _url, method = self.mesh.send_message(text, weather_target)
            timestamp = datetime.now().strftime("%H:%M:%S")
            display_target = weather_target if weather_target else "alle"
            self.send_log.setText(f"Letzter Wetter-Sendeauftrag {timestamp}: → {display_target} | {text} | HTTP {method} 200")
            if weather_target:
                self.status.setText(ui_text(f"Wetterdaten an {weather_target} übertragen"))
            else:
                self.status.setText(ui_text("Wetterdaten ohne Raumangabe an den Hotspot übertragen"))
            self._write_settings()
        except Exception as exc:
            self.status.setText(ui_text(f"Wetterdaten konnten nicht gesendet werden: {exc}"))
        finally:
            self.weather_send_button.setEnabled(True)

    # ---------- Hilfe / Info ----------
    def open_help(self):
        """Show the built-in MeshCom-Guru user guide in the selected language."""
        dialog = QDialog(self)
        is_en = False
        try:
            from i18n import get_language
            is_en = get_language() == "en"
        except Exception:
            pass
        dialog.setWindowTitle("MeshCom-Guru – User guide" if is_en else "MeshCom-Guru – Anleitung")
        dialog.resize(800, 680)
        layout = QVBoxLayout(dialog)
        view = QTextBrowser(dialog)
        view.setOpenExternalLinks(True)

        if is_en:
            guide = f"""
            <h2>MeshCom-Guru v{VERSION}</h2>
            <h3>Quick guide</h3>
            <h3>Connection and settings</h3>
            <p><b>Hotspot IP:</b> Enter the IP address of the MeshCom WebService.</p>
            <p><b>Room / Target:</b> Enter a room number such as 262 or a callsign for a private message.</p>
            <p><b>Own station / GPS:</b> Enter your own callsign and optionally latitude and longitude.</p>
            <p><b>Save settings:</b> Stores personal settings in <code>~/.MeshCom/settings.ini</code>.</p>
            <h3>Connection status</h3>
            <p>Use <b>Connect</b> to connect to the MeshCom WebService. <b>Disconnect</b> stops the connection and automatic message polling.</p>
            <h3>Statistics</h3>
            <p>The <b>Statistics</b> tab shows session counts for messages, nodes, positions, private messages, monitor entries and messages by room.</p>
            <h3>Language</h3>
            <p>Use <b>Settings → Language / Sprache …</b> to switch between German and English. The selection is stored and restored after restart.</p>
            <h3>Messages and rooms</h3>
            <p>The message filter supports up to <b>five rooms</b>. <b>Refresh</b> retrieves messages from the MeshCom WebService. <b>Send</b> transmits a message to the selected room or private target.</p>
            <p>Messages are limited to <b>149 characters</b>. The live counter shows the current length.</p>
            <p>Normal room chats use message bubbles. The <b>All</b> tab keeps its separate display.</p>
            <p><b>Bubble position:</b> The first and last visible messages are aligned from the bottom of the chat area. With only one or a few messages, the bubbles start at the bottom. When the chat contains more messages than fit on screen, normal scrolling is used; manual scrolling is not overridden by new messages.</p>
            <h3>Chat colors</h3>
            <p>Under <b>Settings → Chat colors …</b> you can choose a shared background for all chat views. The text color is applied only to <b>All</b>. Normal room bubbles keep their existing text colors.</p>
            <p><b>Restore defaults</b> sets the chat colors to black background and white text.</p>
            <h3>Input-field context menu</h3>
            <p>Right-click an input field to use standard commands such as Undo, Redo, Cut, Copy, Paste, Delete and Select All. These commands follow the selected interface language.</p>
            <h3>Private chat and delivery status</h3>
            <p>A freshly sent private message first shows <b>⏳</b>. Only a recognized recipient ACK changes the status to <b>✓✓</b>.</p>
            <h3>⚡ Quick texts</h3>
            <p>Quick texts can be inserted, edited, added and deleted. Inserting a quick text does not send it automatically.</p>
            <h3>😊 Emojis</h3>
            <p>The emoji picker inserts the selected emoji at the cursor position. The 149-character limit remains active.</p>
            <h3>📡 Monitor</h3>
            <p>The Monitor displays received MeshCom UDP packets on <b>port 1799</b>. Filters include <b>ALL, MSG, POS, TEL, ACK</b>, plus search, pause, auto-scroll and clear.</p>
            <h3>📋 MH – Most Recently Heard</h3>
            <p>MH lists recently heard stations with callsign, distance, RSSI, SNR, battery and last heard time where available.</p>
            <h3>🗺 Map and position data</h3>
            <p>Position data is processed through UDP 1799 and displayed on the OSM/Leaflet map.</p>
            <h3>🌤 Weather data</h3>
            <p>The WX display shows temperature, humidity, QFE and QNH when supplied by the WebService. It is intended for suitable weather hardware such as BME280/BMP280.</p>
            <h3>🔊 Sound and theme</h3>
            <p>Sound notifications and the light/dark theme can be configured in the settings.</p>
            <h3>Node Info</h3>
            <p><b>Open Node Info</b> opens the information of the connected MeshCom WebService.</p>
            <h3>Installation</h3>
            <p><b>Linux ZIP:</b> Extract the <code>MeshCom</code> folder and run <code>./run_linux.sh</code>.</p>
            <p><b>Windows:</b> Run <code>run_windows.bat</code>.</p>
            <p><b>Debian:</b> The package installs to <code>/usr/share/MeshCom</code>; personal settings remain in <code>~/.MeshCom/settings.ini</code>.</p>
            <h3>Help → About</h3><p>Shows version and program information.</p>
            """
        else:
            guide = f"""
            <h2>MeshCom-Guru v{VERSION}</h2>
            <h3>Kurzanleitung</h3>
            <h3>Verbindung und Einstellungen</h3>
            <p><b>Hotspot IP:</b> IP-Adresse des MeshCom-WebService eintragen.</p>
            <p><b>Raum / Ziel:</b> Eine Raumnummer wie 262 oder ein Rufzeichen für eine private Nachricht eintragen.</p>
            <p><b>Eigene Station / GPS:</b> Eigenes Rufzeichen sowie optional Breitengrad und Längengrad eintragen.</p>
            <p><b>Einstellungen speichern:</b> Speichert die persönlichen Einstellungen unter <code>~/.MeshCom/settings.ini</code>.</p>
            <h3>Verbindungsstatus</h3>
            <p>Mit <b>Verbinden</b> wird die Verbindung zum MeshCom-WebService hergestellt. <b>Trennen</b> beendet die Verbindung und die automatische Nachrichtenabfrage.</p>
            <h3>Statistik</h3>
            <p>Der Tab <b>Statistik</b> zeigt Sitzungszähler für Nachrichten, Nodes, Positionen, Privatnachrichten, Monitor-Einträge und Nachrichten nach Raum.</p>
            <h3>Sprache</h3>
            <p>Unter <b>Einstellungen → Sprache / Language …</b> kann zwischen Deutsch und English gewechselt werden. Die Auswahl wird gespeichert und nach dem Neustart wieder geladen.</p>
            <h3>Nachrichten und Räume</h3>
            <p>Der Nachrichtenfilter unterstützt bis zu <b>fünf Räume</b>. Mit <b>Aktualisieren</b> werden Nachrichten vom MeshCom-WebService abgerufen. Mit <b>Senden</b> wird eine Nachricht an den ausgewählten Raum oder das private Ziel übertragen.</p>
            <p>Nachrichten sind auf <b>149 Zeichen</b> begrenzt. Der Live-Zähler zeigt die aktuelle Länge.</p>
            <p>Normale Raum-Chats verwenden Nachrichten-Bubbles. Der Tab <b>Alle</b> behält seine eigene Darstellung.</p>
            <p><b>Position der Bubbles:</b> Die erste bzw. letzte sichtbare Nachricht wird am unteren Rand des Chatbereichs ausgerichtet. Bei nur einer oder wenigen Nachrichten beginnen die Bubbles unten. Sind mehr Nachrichten vorhanden als in den sichtbaren Bereich passen, steht normales Scrollen zur Verfügung; beim manuellen Hochscrollen wird die Position nicht durch neue Nachrichten überschrieben.</p>
            <h3>Chat-Farben</h3>
            <p>Unter <b>Einstellungen → Chat-Farben …</b> kann ein gemeinsamer Hintergrund für alle Chat-Ansichten gewählt werden. Die Schriftfarbe gilt nur für <b>Alle</b>. Die normalen Raum-Bubbles behalten ihre bisherigen Textfarben.</p>
            <p><b>Standard wiederherstellen</b> setzt die Chat-Farben auf schwarzen Hintergrund und weiße Schrift zurück.</p>
            <h3>Kontextmenü in Eingabefeldern</h3>
            <p>Mit der rechten Maustaste können in Eingabefeldern Standardbefehle wie Rückgängig, Wiederholen, Ausschneiden, Kopieren, Einfügen, Löschen und Alles auswählen verwendet werden. Die Begriffe folgen der gewählten Sprache.</p>
            <h3>Privat-Chat und Sendestatus</h3>
            <p>Eine frisch gesendete private Nachricht zeigt zunächst <b>⏳</b>. Erst ein erkannter Empfänger-ACK setzt den Status auf <b>✓✓</b>.</p>
            <h3>⚡ Schnelltexte</h3>
            <p>Schnelltexte können eingefügt, bearbeitet, ergänzt und gelöscht werden. Das Einfügen sendet den Text nicht automatisch.</p>
            <h3>😊 Emojis</h3>
            <p>Der Emoji-Picker fügt das ausgewählte Emoji an der Cursorposition ein. Das 149-Zeichen-Limit bleibt aktiv.</p>
            <h3>📡 Monitor</h3>
            <p>Der Monitor zeigt empfangene MeshCom-UDP-Pakete auf <b>Port 1799</b>. Filter: <b>ALLE, MSG, POS, TEL, ACK</b>, zusätzlich Suche, Pause, Auto-Scroll und Leeren.</p>
            <h3>📋 MH – Most Recently Heard</h3>
            <p>MH zeigt zuletzt gehörte Stationen mit Rufzeichen, Entfernung, RSSI, SNR, Batterie und letzter Empfangszeit, sofern vorhanden.</p>
            <h3>🗺 Karte und Positionsdaten</h3>
            <p>Positionsdaten werden über UDP 1799 verarbeitet und auf der OSM-/Leaflet-Karte dargestellt.</p>
            <h3>🌤 Wetterdaten</h3>
            <p>Die WX-Anzeige zeigt Temperatur, Luftfeuchte, QFE und QNH, sofern der WebService diese Werte liefert. Vorgesehen ist die Funktion für geeignete Wetterhardware wie BME280/BMP280.</p>
            <h3>🔊 Sound und Theme</h3>
            <p>Benachrichtigungston und Hell-/Dunkel-Theme können in den Einstellungen konfiguriert werden.</p>
            <h3>Node Info</h3>
            <p><b>Node Info aufrufen</b> öffnet die Informationen des verbundenen MeshCom-WebService.</p>
            <h3>Installation</h3>
            <p><b>Linux ZIP:</b> Den Projektordner <code>MeshCom</code> entpacken und <code>./run_linux.sh</code> starten.</p>
            <p><b>Windows:</b> <code>run_windows.bat</code> starten.</p>
            <p><b>Debian:</b> Das Paket installiert nach <code>/usr/share/MeshCom</code>; persönliche Einstellungen bleiben unter <code>~/.MeshCom/settings.ini</code>.</p>
            <h3>Hilfe → Info</h3><p>Zeigt Versions- und Programminformationen.</p>
            """
        view.setHtml(guide)
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
        self._apply_language_ui()
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
                self.status.setText(ui_text("Node Information im Standard-Browser geöffnet"))
            except Exception as exc:
                self.status.setText(ui_text(f"Node Info konnte nicht geöffnet werden: {exc}"))
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
        self._apply_language_ui()
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

        self._apply_language_ui()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.sound_enabled = enabled.isChecked()
            self.sound_driver = str(driver.currentData() or "auto")
            self.sound_volume = volume.value()
            self.sound_file = file_input.text().strip()
            self._prepare_sound()
            self._write_settings()
            self.status.setText(ui_text("Sound-Einstellungen gespeichert"))

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

        # These room tabs are created after the main UI is built (while the
        # saved filter settings are loaded). Apply the selected language here
        # too, so they do not remain with their German source labels.
        self._apply_language_ui()

    def _ensure_tab(self, key, title=None):
        if key in self.tab_keys:
            return self.tab_keys[key]
        view = ChatView()
        view.set_chat_colors(self.chat_background, self.chat_text_color)
        view._mesh_key = key
        # Keep a direct registry of every chat view.  This is intentionally
        # independent of the current tab index, so every room is updated
        # immediately when the common background color changes.
        if view not in self._all_chat_views:
            self._all_chat_views.append(view)
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
        # Merke den aktuellen Nachrichtenstand des geschlossenen Privat-Tabs.
        # WICHTIG: tab_hashes enthält bei normalen Privat-Tabs den Digest der
        # gerenderten Chat-Bubbles. Weiter unten wurde dagegen bisher der
        # Digest von _render_blocks() verglichen. Diese beiden Darstellungen
        # sind absichtlich unterschiedlich und konnten deshalb niemals gleich
        # sein. Ergebnis: Ein geschlossener Privat-Tab wurde beim nächsten
        # Refresh fälschlich wieder als "neue Nachricht" geöffnet.
        #
        # Für geschlossene Privat-Tabs verwenden wir deshalb auf beiden Seiten
        # exakt denselben Digest: den des privaten Nachrichtenblocks.
        closed_blocks = self._private_blocks(list(self.message_cache.values()), key[1])
        closed_rendered = self._render_blocks(closed_blocks)
        closed_hash = hashlib.sha1(
            closed_rendered.encode("utf-8", errors="ignore")
        ).hexdigest()
        self.tab_hashes.pop(key, None)
        self.unread.discard(key)
        self.closed_private[key[1].upper()] = closed_hash
        self._reindex_tabs()
        self.status.setText(ui_text(f"Privatchat geschlossen: {key[1]}"))

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
        self.status.setText(ui_text(f"Privatchat geöffnet: {callsign}"))

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
    def _normalized_plain(cls, block):
        """Return decoded visible text with harmless HTML-entity noise removed."""
        text = cls._plain(block)
        # Some WebService responses arrive double-escaped (e.g. &amp;#...;).
        # Decode a second time so semantically identical cards get the same key.
        for _ in range(2):
            decoded = html.unescape(text)
            if decoded == text:
                break
            text = decoded
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def _message_identity(cls, block):
        """Return a stable semantic identity for one received MeshCom message.

        The WebService can return the same message with slightly different HTML
        wrappers or entity escaping.  Using the complete HTML/visible block as a
        cache key therefore created duplicates.  Prefer MSGID; otherwise use the
        timestamp, sender/room header and actual visible message text.
        """
        plain = cls._normalized_plain(block)
        if not plain:
            return None
        match = re.search(r"\bMSGID\s*[:=]\s*([0-9A-F]+)", plain, re.IGNORECASE)
        if match:
            return ("msgid", match.group(1).upper())

        timestamp = cls._timestamp_from_block(block) or ""
        header = re.search(
            r"(?P<left>[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?(?:\s*,\s*[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?)*)"
            r"\s*>\s*(?P<target>\d{1,8})\b",
            plain, re.IGNORECASE,
        )
        if header:
            h = re.sub(r"\s+", "", header.group(0)).upper()
            body = plain[header.end():].strip()
            # Remove a repeated timestamp that may occur after the header.
            body = re.sub(
                r"^(?:20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}[ T]+)?[01]\d:[0-5]\d(?::[0-5]\d)?\s*",
                "", body, flags=re.IGNORECASE,
            )
            return ("room", timestamp, h, re.sub(r"\s+", " ", body).strip())

        # Direct/private message without a numeric room.
        direct = re.search(
            r"[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?\s*>\s*"
            r"[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?\b",
            plain, re.IGNORECASE,
        )
        if direct:
            return ("direct", timestamp, re.sub(r"\s+", "", direct.group(0)).upper(),
                    re.sub(r"\s+", " ", plain[direct.end():]).strip())

        return ("text", timestamp, plain)

    @classmethod
    def _room_from_block(cls, block):
        # Always parse the decoded visible text. Searching raw HTML can mistake
        # unrelated '>' characters or escaped markup for a room destination.
        plain = cls._normalized_plain(block)
        match = re.search(
            r"(?:[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?(?:\s*,\s*)?)+"
            r"\s*>\s*(\d{1,8})\b",
            plain, re.IGNORECASE,
        )
        return match.group(1) if match else ""

    @classmethod
    def _target_from_block(cls, block):
        plain = cls._normalized_plain(block)
        match = re.search(
            r">\s*([A-Z0-9]{1,8}(?:-[0-9]{1,2})?)\b",
            plain, re.IGNORECASE,
        )
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

    def _outgoing_target_matches(self, block, target):
        target = str(target or "").strip().upper()
        if not target:
            return True
        plain = self._normalized_plain(block)
        if re.search(rf"(?:NACH|TO)\s*[:=]\s*{re.escape(target)}(?:\s|$)", plain, re.IGNORECASE):
            return True
        return re.search(rf">\s*{re.escape(target)}(?:\s|$)", plain, re.IGNORECASE) is not None

    def _block_is_outgoing(self, block, outgoing):
        own = str(self.own_callsign or "").strip().upper()
        text = str(outgoing.get("text", "")).strip()
        if not own or not text:
            return False
        plain = self._normalized_plain(block)
        if own not in plain.upper() or text.casefold() not in plain.casefold():
            return False
        return self._outgoing_target_matches(block, outgoing.get("target", ""))

    def _mark_outgoing_echo(self, clean_text, seq, packet_target=""):
        for msg in reversed(self.outgoing_messages):
            if msg.get("status") != "pending":
                continue
            if clean_text and clean_text.casefold() != str(msg.get("text", "")).strip().casefold():
                continue
            expected = str(msg.get("target", "")).strip().upper()
            actual = str(packet_target or "").strip().upper()
            if expected and actual and expected != actual:
                if actual not in {"*", "ALL", "CQCQCQ"} or expected not in {"", "*", "ALL", "CQCQCQ"}:
                    continue
            msg["seq"] = str(seq)
            # In privaten Chats bleibt die Sanduhr auch nach dem eigenen
            # Node-Echo stehen. Erst ein echter Empfänger-ACK darf auf ✓✓
            # wechseln. In den normalen Räumen bleibt das bisherige Verhalten
            # mit ✓ nach dem Echo unverändert.
            target_type = str(msg.get("target", "")).strip()
            if target_type and not target_type.isdigit():
                msg["status"] = "pending"
            else:
                msg["status"] = "sent"
            return msg
        return None

    def _mark_outgoing_ack(self, seq):
        for msg in reversed(self.outgoing_messages):
            if str(msg.get("seq", "")) == str(seq):
                msg["status"] = "delivered"
                msg["ack"] = True
                return msg
        return None

    def _refresh_visible_ack_states(self):
        # Den bestehenden Nachrichten-Refresh verwenden, damit auch der
        # vorhandene „Alle“-Zusatzstrom (einschließlich POS/Koordinaten) exakt
        # so aufgebaut wird wie bisher. Keine eigene neue Chat-/POS-Logik.
        if not self.refresh_in_progress:
            self.update_messages()


    def _render_blocks(self, blocks):
        if not blocks:
            return "<html><body><p><b>Keine Nachrichten.</b></p></body></html>"
        rendered = []
        for block in blocks:
            content = self._make_clickable(block)
            # Nur bei einer tatsächlich eigenen Textnachricht einen Status
            # anhängen. POS-/Koordinatenblöcke bleiben 1:1 unangetastet.
            ack_html = ""
            for outgoing in reversed(self.outgoing_messages):
                if self._block_is_outgoing(block, outgoing):
                    symbols = {
                        "pending": "⏳",
                        "sent": "✓",
                        "delivered": "✓✓",
                    }
                    symbol = symbols.get(outgoing.get("status", "pending"), "")
                    if symbol:
                        ack_html = f' <span title="Sendestatus" style="font-weight:700;">{symbol}</span>'
                    break
            rendered.append(content + ack_html)
        return (
            "<html><body style='background:"
            + str(getattr(self, "chat_background", "#101722"))
            + ";color:"
            + str(getattr(self, "chat_text_color", "#e7edf5"))
            + ";font-family:sans-serif;margin:0;padding:6px 4px;'>"
            + "\n".join(rendered)
            + "</body></html>"
        )

    def _room_blocks(self, blocks, room):
        return [b for b in blocks if self._room_from_block(b) == str(room)]

    @classmethod
    def _all_display_identity(cls, block):
        """Return the normalized callsign and text used by the ``Alle`` tab.

        This duplicate check is intentionally used ONLY by ``Alle``.  The
        WebService may render the same message with different HTML entities
        before the callsign.  After decoding those entities, the callsign and
        visible message text can be compared independently by the caller.
        """
        plain = cls._normalized_plain(block)
        if not plain:
            return None

        header = re.search(
            r"(?P<left>[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?(?:\s*,\s*[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?)*)"
            r"\s*>\s*(?P<target>\d{1,8}|\*|ALL)(?=\s|$)",
            plain, re.IGNORECASE,
        )
        if header:
            # The FIRST callsign is the actual sender.  Ignore any harmless
            # icon/entity characters which the dashboard may place before it.
            sender_match = re.search(CALLSIGN_RE.pattern, header.group("left"), re.IGNORECASE)
            sender = cls._normalize_callsign(sender_match.group(0)) if sender_match else ""

            body = plain[header.end():].strip()
            body = re.sub(
                r"^(?:20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}[ T]+)?[01]\d:[0-5]\d(?::[0-5]\d)?\s*",
                "", body, flags=re.IGNORECASE,
            )
            body = re.sub(r"\s+", " ", body).strip()
            return (sender.upper(), body.casefold())

        # Position/status cards or unusual layouts without a normal room
        # header still get a stable text key.  They do not affect the room tabs.
        return ("", re.sub(r"\s+", " ", plain).strip().casefold())


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
            return [b for b in blocks if self._is_all_target(b)]
        # Bei aktivem Raumfilter bleiben die gespeicherten Räume sichtbar.
        # Zusätzlich müssen Nachrichten, die ausdrücklich an „Alle“
        # (>* bzw. >ALL) gerichtet sind, weiterhin im Tab „Alle“ erscheinen.
        return [
            b for b in blocks
            if self._room_from_block(b) in rooms or self._is_all_target(b)
        ]

    @classmethod
    def _is_all_target(cls, block):
        """Return True for messages explicitly addressed to the global 'Alle' target."""
        plain = cls._normalized_plain(block)
        return re.search(
            r"\s*>\s*(?:\*|ALL)(?=\s|$)", plain, re.IGNORECASE
        ) is not None

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
function formatDistance(km){
  if(km===null || km===undefined || !isFinite(km)) return '';
  if(km < 1) return Math.round(km*1000)+' m';
  return km.toFixed(1)+' km';
}
function renderStations(stations){
  const hadStations=markerLayer.getLayers().length>0;
  markerLayer.clearLayers();
  stations.forEach(s=>{const m=L.marker([s.lat,s.lon]).addTo(markerLayer);const heard=s.last_heard?'<br><b>Zuletzt gehört:</b> '+esc(s.last_heard):'';
    const distance=s.distance_km!==null && s.distance_km!==undefined ? formatDistance(Number(s.distance_km)) : '';
    const distanceText=distance && !s.own ? '<br><b>Entfernung:</b> '+esc(distance) : '';
    m.bindPopup('<b>'+esc(s.callsign)+'</b>'+distanceText+'<br>Breite: '+Number(s.lat).toFixed(6)+'<br>Länge: '+Number(s.lon).toFixed(6)+heard+(s.own?'<br><b>Eigene Station</b>':''));
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

        def distance_km(lat1, lon1, lat2, lon2):
            # Great-circle distance (Haversine), measured from the user's own
            # configured position to each station.
            try:
                r = 6371.0088
                p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
                dp = math.radians(float(lat2) - float(lat1))
                dl = math.radians(float(lon2) - float(lon1))
                a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
                return r * 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1 - a)))
            except Exception:
                return None

        stations=[]
        for callsign,(lat,lon) in sorted(self.station_positions.items()):
            distance = None
            if self.own_lat is not None and self.own_lon is not None:
                distance = distance_km(self.own_lat, self.own_lon, lat, lon)
            stations.append({"callsign":callsign,"lat":lat,"lon":lon,"own":callsign.upper()==self.own_callsign.upper(),"last_heard":self.station_last_heard.get(callsign.upper(),""),"distance_km":distance})
        if self.own_lat is not None and self.own_lon is not None:
            own_call=self.own_callsign
            stations=[s for s in stations if s["callsign"].upper()!=own_call.upper()]
            stations.insert(0,{"callsign":own_call,"lat":self.own_lat,"lon":self.own_lon,"own":True,"distance_km":0.0})
        # Die Karte wird nicht neu geladen. Die Stationsdaten werden jedoch
        # gepuffert, bis Leaflet/JavaScript nach setHtml() vollständig bereit ist.
        self._push_map_stations(stations)

    # ---------- Verbindung ----------
    def connect_mesh(self):
        """Test the configured WebService and start automatic refresh."""
        ip = self.ip_input.text().strip().rstrip("/")
        if not ip:
            self.status.setText(ui_text("Fehler: Keine Hotspot-IP eingetragen"))
            return

        try:
            self.mesh = MeshCom(ip)
            self.status.setText(ui_text("Verbinde mit MeshCom-WebService …"))
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)

            # Echter WebService-Abruf als Verbindungstest.
            self.mesh.get_messages()
            self.connected = True
            self._set_connection_status(True)
            self.status.setText(ui_text("Mit MeshCom-WebService verbunden"))
            self.update_messages()
        except Exception as exc:
            self.connected = False
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self._set_connection_status(False)
            self.status.setText(ui_text(f"Verbindung fehlgeschlagen: {exc}"))

    def disconnect_mesh(self):
        """Stop WebService polling and mark the connection offline."""
        self.connected = False
        self._set_connection_status(False)
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.status.setText(ui_text("Vom MeshCom-WebService getrennt"))

    # ---------- Refresh ----------
    def update_messages(self):
        if not self.connected:
            return
        if self.refresh_in_progress:
            return
        self.refresh_in_progress = True
        try:
            page = self.mesh.get_messages()
            self._set_connection_status(True)
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
            self._update_statistics()

            self._ensure_room_tabs()
            # Der HTTP-Nachrichtenstrom bleibt für Chat/Privatnachrichten zuständig.
            # UDP-Positionsdaten werden separat und in Echtzeit verarbeitet.
            #
            # WICHTIG: Nicht mehr nur den aktuellen WebService-Ausschnitt anzeigen.
            # Manche MeshCom-WebService-Antworten enthalten ältere Nachrichten
            # später nicht mehr. Ohne lokalen Puffer würden diese Nachrichten bei
            # jedem Refresh aus dem Chat verschwinden. Bereits bekannte Nachrichten
            # werden deshalb dauerhaft für die laufende Sitzung gehalten.
            # Beim ersten Abruf nach einem Programmstart wird der vom
            # WebService bereits vorhandene Bestand nur als Startbestand
            # registriert. Dadurch starten ALLE Raum-Tabs leer – genauso wie
            # Raum 10 bisher. Erst ab dem zweiten Abruf werden wirklich neue
            # Nachrichten in den lokalen Sitzungspuffer übernommen.
            if not self.initial_message_sync_done:
                for block in blocks:
                    identity = self._message_identity(block)
                    if identity:
                        self.startup_message_identities.add(identity)
                self.initial_message_sync_done = True
            else:
                for block in blocks:
                    identity = self._message_identity(block)
                    if identity and identity not in self.startup_message_identities:
                        self.message_cache[identity] = block

            self._update_statistics()
            cached_blocks = list(self.message_cache.values())
            cached_blocks.sort(key=lambda b: self._timestamp_from_block(b) or "99:99:99")

            # Configured room tabs.
            for room in self._rooms():
                key = ("room", room)
                idx = self._ensure_tab(key, f"Raum {room}")
                room_blocks = self._room_blocks(cached_blocks, room)
                self._update_tab_content(key, idx, room_blocks)

            # Bereits geöffnete Privat-Tabs weiter aktualisieren.
            # Neue Privat-Tabs entstehen NICHT mehr aus normalen Raum-Nachrichten.
            # Automatisch angelegt werden sie nur, wenn der betreffende Block keine
            # Raum-ID besitzt und damit tatsächlich wie eine Direktnachricht aussieht.
            private_targets = set()
            for block in cached_blocks:
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
                        closed_rendered = self._render_blocks(self._private_blocks(cached_blocks, sender))
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
                private_blocks = self._private_blocks(cached_blocks, target)
                self._update_tab_content(key, idx, private_blocks)
                if is_new and private_blocks and self.tabs.currentIndex() != idx:
                    self._set_tab_unread(key)

            # Tab „Alle“ basiert ebenfalls auf dem lokalen Nachrichtenpuffer.
            # Dadurch verschwinden Nachrichten nicht mehr nur deshalb, weil der
            # WebService sie bei einer späteren Abfrage nicht mehr zurückliefert.
            all_key = ("all", "all")
            all_index = self._ensure_tab(all_key, "Alle")
            # Der Raumfilter gilt auch für den Gesamt-Tab „Alle“:
            # - Filter AUS: unverändert alle bekannten Nachrichten anzeigen.
            # - Filter EIN: ausschließlich Nachrichten aus den gespeicherten Räumen
            #   anzeigen. Die übrigen Tabs und die eigentliche Nachrichtenablage
            #   bleiben davon unberührt.
            all_blocks = self._filter_blocks(cached_blocks)

            # Zusätzlich bekannte UDP-Positionskarten übernehmen, aber ebenfalls
            # nur einmal. Die Positionsdaten selbst werden unabhängig davon in
            # station_positions für die Karte gepflegt.
            seen_all = {self._message_identity(b) for b in all_blocks if self._message_identity(b)}
            for block in self.udp_position_blocks:
                # Bei aktivem Raumfilter dürfen auch diese Zusatzblöcke nur in
                # „Alle“ erscheinen, wenn sie einem gespeicherten Raum zugeordnet
                # werden können. Bei deaktiviertem Filter bleibt das bisherige
                # Verhalten vollständig erhalten.
                if (
                    self.filter_enabled.isChecked()
                    and self._room_from_block(block) not in self._rooms()
                    and not self._is_all_target(block)
                ):
                    continue
                key = self._message_identity(block)
                if key and key in seen_all:
                    continue
                if key:
                    seen_all.add(key)
                all_blocks.append(block)

            # Eine eigene lokale Kopie wird NICHT zusätzlich erzeugt. Eigene
            # Nachrichten kommen weiterhin über den normalen WebService zurück.
            self.local_all_messages.clear()

            # Nur für „Alle“: dieselbe Room-Nachricht kann vom WebService
            # in zwei HTML-Varianten geliefert werden (z. B. einmal mit einem
            # zusätzlichen HTML-Entity/Icon vor dem Rufzeichen). Diese Varianten
            # werden hier als identisch behandelt. Die Raum-Tabs werden bewusst
            # NICHT verändert.
            unique_all = []
            seen_all_pairs = set()
            seen_all_fallback = set()
            for block in all_blocks:
                # Die spezielle Dublettenprüfung darf NUR auf Nachrichten
                # angewendet werden, die selbst an „Alle“ gerichtet sind
                # (z. B. >* / >ALL). Nachrichten aus Raum-Tabs werden zwar
                # unter „Alle“ mit angezeigt, dürfen aber niemals mit dieser
                # Prüfung untereinander oder mit einer Alle-Nachricht
                # verglichen werden.
                plain_block = self._normalized_plain(block)
                all_target = re.search(
                    r"\s*>\s*(?:\*|ALL)(?=\s|$)", plain_block, re.IGNORECASE
                ) is not None
                if not all_target:
                    unique_all.append(block)
                    continue

                identity = self._all_display_identity(block)
                if identity is None:
                    unique_all.append(block)
                    continue

                callsign, text_key = identity

                # Vorgabe für „Alle“: Rufzeichen UND Nachrichtentext müssen
                # gemeinsam übereinstimmen, damit ein Eintrag als Duplikat
                # verworfen wird. Nur eines von beiden darf niemals genügen:
                # gleicher Rufname + anderer Text bleibt sichtbar und
                # anderer Rufname + gleicher Text bleibt ebenfalls sichtbar.
                # Bei „Alle“ kann derselbe Absender vom WebService mit
                # zusätzlichen Zeichen/HTML-Entities vor dem Rufzeichen
                # geliefert werden, z. B. „DO2QG-1>*“ und „✓ DO2QG-1>*“.
                # Deshalb reicht ein einfacher String-Schlüssel nicht immer.
                # Zwei Einträge gelten als Duplikat, wenn der normalisierte
                # Nachrichtentext gleich ist und das jeweils erkannte
                # Rufzeichen im anderen Rufzeichen-Feld enthalten ist.
                # Damit bleiben unterschiedliche Texte desselben Rufzeichens
                # sowie gleiche Texte verschiedener Rufzeichen sichtbar.
                if callsign and text_key:
                    duplicate = False
                    for old_callsign, old_text in seen_all_pairs:
                        if old_text != text_key:
                            continue
                        a = re.sub(r"[^A-Z0-9-]", "", callsign.upper())
                        b = re.sub(r"[^A-Z0-9-]", "", old_callsign.upper())
                        if a and b and (a in b or b in a):
                            duplicate = True
                            break
                    if duplicate:
                        continue
                    seen_all_pairs.add((callsign.upper(), text_key))
                else:
                    # Für ungewöhnliche Karten/Status-Blöcke ohne vollständige
                    # Rufzeichen+Text-Kombination weiterhin nur exakt identische
                    # Fallback-Daten unterdrücken.
                    fallback = (callsign.upper(), text_key)
                    if fallback in seen_all_fallback:
                        continue
                    seen_all_fallback.add(fallback)
                unique_all.append(block)
            all_blocks = unique_all

            # Chronologisch sortieren.
            all_blocks.sort(key=lambda b: self._timestamp_from_block(b) or "99:99:99")

            self._update_tab_content(all_key, all_index, all_blocks)

            if self.filter_enabled.isChecked():
                rooms = self._rooms()
                self.status.setText(ui_text("Nachrichten aktualisiert – Filter: " + (", ".join(rooms) if rooms else "keine Räume")))
            else:
                self.status.setText(ui_text("Nachrichten aktualisiert – alle Räume"))
        except Exception as exc:
            self.connected = False
            self._set_connection_status(False)
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.status.setText(ui_text(f"Abruf fehlgeschlagen: {exc}"))
        finally:
            self.refresh_in_progress = False


    @staticmethod
    def _chat_escape(value):
        return html.escape(str(value or ""), quote=True)

    @classmethod
    def _chat_field(cls, plain, label):
        m = re.search(rf"\b{re.escape(label)}\s*:\s*(.*?)(?=\s+\b(?:Von|From|Nach|To|RSSI|SNR|MsgId|MSGID|Batterie|Batt|Höhe|Breite|Länge|Firmware|Nachricht)\s*:|$)",
                      plain, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    @classmethod
    def _render_chat_blocks(cls, blocks, own_callsign="", outgoing_messages=None):
        """Render only normal room/private chats as modern message cards.

        This renderer is intentionally NOT used by 'Alle', 'Monitor', 'MH' or
        the map.  It only changes the presentation layer of normal chat tabs.
        """
        if not blocks:
            return """<html><head><meta charset="utf-8"></head>
            <body style="background:#101722;color:#e7edf5;font-family:sans-serif;">
            <div style="padding:18px;color:#aeb9c7;">Keine Nachrichten.</div></body></html>"""

        own = str(own_callsign or "").strip().upper()
        outgoing_messages = outgoing_messages or []
        cards = []

        for block in blocks:
            plain = cls._normalized_plain(block)
            if not plain:
                continue

            # Sender / destination.  Prefer explicit dashboard labels.
            room_header = re.search(
                r"(?P<left>[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?"
                r"(?:\s*,\s*[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?)*)"
                r"\s*>\s*(?P<right>\d{1,8})\b", plain, re.IGNORECASE)
            sender = ""
            target = ""
            if room_header:
                left_calls = CALLSIGN_RE.findall(room_header.group("left"))
                if left_calls:
                    sender = cls._normalize_callsign(left_calls[0]) or left_calls[0]
                target = room_header.group("right")
            else:
                vm = re.search(r"\b(?:Von|From)\s*:\s*([A-Z0-9][A-Z0-9,\- ]{1,30}?)(?=\s+\b(?:Nach|To)\s*:)", plain, re.IGNORECASE)
                sender = vm.group(1).strip() if vm else ""
                tm = re.search(r"\b(?:Nach|To)\s*:\s*([A-Z0-9*\-]{1,20})", plain, re.IGNORECASE)
                target = tm.group(1).strip() if tm else ""

                if not sender or not re.search(r"[A-Z]{1,3}[0-9]", sender, re.IGNORECASE):
                    participants = cls._private_participants(block)
                    if participants:
                        sender, target = participants[0], participants[1]

            # If the dashboard omits the labels, recover a normal CALL>target header.
            if not sender:
                hm = re.search(
                    r"(?P<left>[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?)\s*>\s*"
                    r"(?P<right>[A-Z0-9*\-]{1,20})",
                    plain, re.IGNORECASE)
                if hm:
                    sender, target = hm.group("left"), hm.group("right")

            sender = cls._normalize_callsign(sender) or sender
            target = target.strip()

            # Time and radio metadata.
            time_text = cls._timestamp_from_block(block)
            rssi = cls._chat_field(plain, "RSSI")
            snr = cls._chat_field(plain, "SNR")
            msgid = cls._chat_field(plain, "MsgId") or cls._chat_field(plain, "MSGID")
            batt = cls._chat_field(plain, "Batterie") or cls._chat_field(plain, "Batt")
            height = cls._chat_field(plain, "Höhe")
            lat = cls._chat_field(plain, "Breite")
            lon = cls._chat_field(plain, "Länge")
            firmware = cls._chat_field(plain, "Firmware")

            # Message text: take everything after the explicit Nachricht label.
            body = ""
            nm = re.search(r"(?:💬\s*)?Nachricht\s*:\s*(.*)$", plain, re.IGNORECASE)
            if nm:
                body = nm.group(1).strip()
            else:
                # Fallback for compact dashboard lines: remove known metadata,
                # leaving the actual message at the end.
                body = plain
                if sender:
                    body = re.sub(re.escape(sender), "", body, count=1, flags=re.IGNORECASE)
                body = re.sub(r"\b(?:Von|From|Nach|To|RSSI|SNR|MsgId|MSGID|Batterie|Batt|Höhe|Breite|Länge|Firmware|Nachricht)\s*:\s*[^|]+", " ", body, flags=re.IGNORECASE)
                body = re.sub(r"\s+", " ", body).strip()

            # Remove the repeated date/time which some WebService versions put
            # immediately before the message text.
            body = re.sub(
                r"^(?:20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}[ T]+)?[01]\d:[0-5]\d(?::[0-5]\d)?\s*",
                "", body, flags=re.IGNORECASE).strip()
            if not body:
                body = " "

            is_out = False
            for outgoing in reversed(outgoing_messages):
                if cls._block_is_outgoing_static(block, outgoing, own):
                    is_out = True
                    break
            if not is_out and own and sender.upper() == own and target:
                is_out = True

            status = ""
            for outgoing in reversed(outgoing_messages):
                text_o = str(outgoing.get("text", "")).strip()
                if is_out and text_o and text_o.casefold() == body.casefold():
                    status = {"pending":"⏳", "sent":"✓", "delivered":"✓✓"}.get(outgoing.get("status",""), "")
                    break

            # Keep all useful metadata that already exists in the message block.
            meta = []
            if rssi: meta.append(f"RSSI: {cls._chat_escape(rssi)}")
            if snr: meta.append(f"SNR: {cls._chat_escape(snr)}")
            if msgid: meta.append(f"MsgId: {cls._chat_escape(msgid)}")
            if batt: meta.append(f"Batterie: {cls._chat_escape(batt)}")
            if height: meta.append(f"Höhe: {cls._chat_escape(height)}")
            if lat: meta.append(f"Breite: {cls._chat_escape(lat)}")
            if lon: meta.append(f"Länge: {cls._chat_escape(lon)}")
            if firmware: meta.append(f"Firmware: {cls._chat_escape(firmware)}")

            icon = "✈" if is_out else "📡"
            bg = "#075f3f" if is_out else "#173a63"
            border = "#0a8055" if is_out else "#285a8e"
            align = "right" if is_out else "left"
            margin = "margin-left:12%;margin-right:2%;" if is_out else "margin-left:2%;margin-right:12%;"

            top = f"<b style='font-size:16px;'>{cls._chat_escape(time_text or '')}</b> &nbsp; <b>MSG</b> &nbsp;•&nbsp; <span>HTTP</span>"
            if status:
                top += f" &nbsp; <span style='font-weight:700;'>{status}</span>"

            # Tables are deliberately used here instead of flex/inline-block:
            # QTextDocument (used by QTextBrowser) supports tables reliably,
            # while modern CSS layout rules are only partially supported.
            card_align = "right" if is_out else "left"
            card_bg = bg
            card_border = border
            card = f"""
            <table width="88%" align="{card_align}" cellspacing="0" cellpadding="0"
                   style="margin:7px 0;">
              <tr>
                <td bgcolor="{card_bg}" style="border:1px solid {card_border};
                    padding:10px 14px 12px 14px;color:#eef5fb;">
                  <div style="font-size:13px;color:#e4edf6;">
                    <span style="font-size:22px;">{icon}</span>
                    &nbsp;{top}
                  </div>
                  <div style="margin-top:7px;font-size:14px;">
                    <b>Von:</b> {cls._chat_escape(sender or '-')}
                    &nbsp;&nbsp;&nbsp; <b>Nach:</b> {cls._chat_escape(target or '-')}
                  </div>
                  <div style="margin-top:4px;font-size:13px;color:#d7e2ec;">
                    {(' &nbsp;•&nbsp; '.join(meta)) if meta else 'RSSI: - &nbsp;&nbsp; SNR: -'}
                  </div>
                  <div style="margin-top:7px;font-size:14px;">
                    💬 <b>Nachricht:</b><br>
                    <span style="white-space:pre-wrap;">{cls._make_clickable(cls._chat_escape(body))}</span>
                  </div>
                </td>
              </tr>
            </table>"""
            cards.append(card)

        return """<html><head><meta charset="utf-8"></head>
        <body style="background:#101722;color:#e7edf5;font-family:sans-serif;margin:0;padding:6px 4px;">
        """ + "\n".join(cards) + "</body></html>"

    @staticmethod
    def _block_is_outgoing_static(block, outgoing, own):
        text = str(outgoing.get("text", "")).strip()
        if not own or not text:
            return False
        plain = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", block))).strip()
        if own not in plain.upper() or text.casefold() not in plain.casefold():
            return False
        expected = str(outgoing.get("target", "")).strip().upper()
        if not expected:
            return True
        # Numeric rooms and broadcast targets are represented in several ways
        # by the WebService; don't let that alter the card direction.
        actual_m = re.search(r"\b(?:Nach|To)\s*:\s*([A-Z0-9*\-]+)", plain, re.IGNORECASE)
        actual = actual_m.group(1).upper() if actual_m else ""
        if actual and actual != expected and actual not in {"*", "ALL", "CQCQCQ"}:
            return False
        return True

    def _update_tab_content(self, key, index, blocks):
        view = self.tabs.widget(index)
        if not isinstance(view, ChatView):
            return
        # Nur normale Raum- und Privat-Chats bekommen das neue Karten-Design.
        # 'Alle', 'Monitor', 'MH' und die Karte laufen weiterhin über ihre
        # bisherigen Darstellungen.
        if key[0] in ("room", "private"):
            # Build real QWidget bubbles from the already filtered blocks.
            # The existing message/POS collection remains untouched.
            unique = []
            seen = set()
            own = str(self.own_callsign or "").strip().upper()
            for block in blocks:
                ident = self._message_identity(block)
                if ident is not None and ident in seen:
                    continue
                if ident is not None:
                    seen.add(ident)
                plain = self._normalized_plain(block)
                if not plain:
                    continue
                # For room traffic the transport header is authoritative:
                # CALL1,CALL2>ROOM means CALL1 is the original sender.  Some
                # WebService layouts also expose a derived "Von:" field which
                # may contain the local/forwarding node instead.  Prefer the
                # transport header so a received message is never shown as
                # our own just because a relay node appears in "Von:".
                room_header = re.search(
                    r"(?P<left>[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?"
                    r"(?:\s*,\s*[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?)*)"
                    r"\s*>\s*(?P<right>\d{1,8})\b", plain, re.IGNORECASE)
                sender = ""
                target = ""
                # Private messages use the explicit direct-message transport
                # header as the authoritative source.  The FIRST callsign is
                # always the original sender; a relay/forwarding callsign must
                # never make a received private message look like our own.
                if key[0] == "private":
                    private_parts = self._private_participants(block)
                    if private_parts:
                        sender, target = private_parts[0], private_parts[1]
                if not sender and room_header:
                    left_calls = CALLSIGN_RE.findall(room_header.group("left"))
                    if left_calls:
                        sender = self._normalize_callsign(left_calls[0]) or left_calls[0]
                    target = room_header.group("right")
                else:
                    vm = re.search(r"\b(?:Von|From)\s*:\s*([A-Z0-9][A-Z0-9,\- ]{1,30}?)(?=\s+\b(?:Nach|To)\s*:)", plain, re.IGNORECASE)
                    sender = vm.group(1).strip() if vm else ""
                    tm = re.search(r"\b(?:Nach|To)\s*:\s*([A-Z0-9*\-]{1,20})", plain, re.IGNORECASE)
                    target = tm.group(1).strip() if tm else ""
                    if not sender:
                        parts = self._private_participants(block)
                        if parts:
                            sender, target = parts[0], parts[1]

                # Room messages returned by some MeshCom dashboards do not
                # contain the explicit "Von:/Nach:" labels used by private
                # messages.  Their header is instead simply CALLSIGN>ROOM.
                # Recover the same sender/target information here so normal
                # room tabs get exactly the same bubble layout and direction
                # handling as the working private-chat tab.  The "Alle" tab
                # is deliberately not affected because it uses the other
                # rendering branch below.
                if not sender:
                    hm = re.search(
                        r"(?P<left>[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?)\s*"
                        r">\s*(?P<right>\d{1,8})\b",
                        plain, re.IGNORECASE,
                    )
                    if hm:
                        sender = hm.group("left")
                        target = hm.group("right")

                sender = self._normalize_callsign(sender) or sender
                time_text = self._timestamp_from_block(block) or ""
                nm = re.search(r"(?:💬\s*)?Nachricht\s*:\s*(.*)$", plain, re.IGNORECASE)
                if nm:
                    body = nm.group(1).strip()
                else:
                    # Compact room cards can contain only:
                    # CALLSIGN>ROOM [date] time message
                    # Remove that transport header and timestamp so the
                    # bubble shows the same clean message text as private chat.
                    body = plain
                    if sender and target:
                        body = re.sub(
                            rf"^{re.escape(sender)}\s*>\s*{re.escape(str(target))}\b\s*",
                            "", body, count=1, flags=re.IGNORECASE,
                        ).strip()
                    body = re.sub(
                        r"^20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}[ T]+[01]\d:[0-5]\d(?::[0-5]\d)?\s*",
                        "", body, count=1, flags=re.IGNORECASE,
                    ).strip()
                body = re.sub(r"^(?:20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}[ T]+)?[01]\d:[0-5]\d(?::[0-5]\d)?\s*", "", body).strip()
                if not body:
                    body = " "
                outgoing = bool(own and sender.upper() == own)
                status = ""
                for outgoing_msg in reversed(self.outgoing_messages):
                    if outgoing and str(outgoing_msg.get("text", "")).strip().casefold() == body.casefold():
                        status = {"pending":"⏳", "sent":"✓", "delivered":"✓✓"}.get(outgoing_msg.get("status", ""), "")
                        break
                icon = "✈" if outgoing else "📡"
                icon_html = f"<span style='font-size:28px; line-height:32px; vertical-align:middle;'>{icon}</span>"
                status_html = (f" <span style='font-size:28px; font-weight:900; line-height:32px; vertical-align:middle;'>{status}</span>" if status else "")
                sender_html = self._chat_escape(sender or "-")
                target_html = self._chat_escape(target or "-")
                body_html = self._make_clickable(self._chat_escape(body))
                meta = []
                for label in ("RSSI", "SNR", "MsgId", "MSGID"):
                    val = self._chat_field(plain, label)
                    if val:
                        meta.append(f"{label}: {self._chat_escape(val)}")
                meta_html = " &nbsp;•&nbsp; ".join(meta)
                header = (f"<b>{icon_html} &nbsp;{self._chat_escape(time_text)}</b> &nbsp; "
                          f"<b>{sender_html}</b>{status_html}")
                html_msg = (f"<div style='font-size:13px;'>{header}</div>"
                            f"<div style='margin-top:4px;font-size:12px;'><b>Nach:</b> {target_html}"
                            f"{(' &nbsp;•&nbsp; ' + meta_html) if meta_html else ''}</div>"
                            f"<div style='margin-top:5px;font-size:14px;'><b>{body_html}</b></div>")
                unique.append({"html": html_msg, "outgoing": outgoing})
            # Keep a digest for both unread handling AND the rendered bubble
            # state.  update_messages() runs every 5 seconds.  Rebuilding the
            # complete QWidget bubble tree on every refresh forces Qt to remove
            # and recreate all message widgets, which can cause visible
            # flickering even when absolutely nothing in the chat changed.
            #
            # The rendered HTML also contains the send-status symbol (⏳/✓/✓✓),
            # so a real status change still triggers exactly one rebuild.
            digest_source = "\n".join(
                f"{item.get('outgoing', False)}\x1f{item.get('html', '')}"
                for item in unique
            )
            digest = hashlib.sha1(digest_source.encode("utf-8", errors="ignore")).hexdigest()
            old_digest = self.tab_hashes.get(key, "")
            changed = bool(old_digest) and old_digest != digest
            self.tab_hashes[key] = digest

            # IMPORTANT: do not recreate the bubbles when the refresh returned
            # exactly the same visual content.  This is the flicker fix.
            if old_digest != digest:
                view.set_bubbles(unique)
        else:
            rendered = self._render_blocks(blocks)
            digest = hashlib.sha1(rendered.encode("utf-8", errors="ignore")).hexdigest()
            changed = self.tab_hashes.get(key) not in ("", digest) and self.tab_hashes.get(key) != digest
            self.tab_hashes[key] = digest
            if key[0] == "all":
                view.set_all_html(rendered)
            else:
                view.setHtml(rendered)
        # ChatView keeps the current scroll position during refreshes and only
        # follows the newest message when the user was already at the bottom.
        if changed and self.tabs.currentIndex() != index:
            self._set_tab_unread(key)

    # ---------- Send ----------
    def _monitor_add_local_message(self, text, target):
        """Show the just-sent message immediately; later UDP echo is merged."""
        if not hasattr(self, "monitor_rows") or getattr(self, "monitor_paused", False):
            return
        self.monitor_rows.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": "MSG",
            "src": str(self.own_callsign or "-").strip() or "-",
            "dst": str(target or "-").strip() or "-",
            "rssi": "-",
            "snr": "-",
            "detail": str(text).strip(),
            "_local_send": True,
            "_text": str(text).strip(),
        })
        self.monitor_rows = self.monitor_rows[-500:]
        self._render_monitor()

    def send(self):
        if not self.connected:
            self.status.setText(ui_text("Bitte zuerst mit dem MeshCom-WebService verbinden"))
            return
        text = self.message_input.text().strip()
        target = self.target_input.text().strip()
        if not text:
            self.status.setText(ui_text("Keine Nachricht eingegeben"))
            return
        if len(text) > 149:
            self.status.setText(ui_text("Nachricht darf maximal 149 Zeichen lang sein"))
            return

        self.send_button.setEnabled(False)
        try:
            _answer, _url, method = self.mesh.send_message(text, target)
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.last_sent = text
            self.last_sent_time = timestamp
            self.last_private_sent = (target.upper(), text) if target and not target.isdigit() else None

            # Punkt 2: Sendeauftrag für ⏳/✓/✓✓ merken. Die eigentliche
            # Nachricht kommt weiterhin ausschließlich aus dem WebService.
            self.outgoing_messages.append({
                "text": text,
                "target": target,
                "time": timestamp,
                "seq": "",
                "status": "pending",
                "ack": False,
            })
            self.outgoing_messages = self.outgoing_messages[-100:]

            # Punkt 3 Monitor: eigene Nachricht sofort anzeigen.
            self._monitor_add_local_message(text, target)

            # Keine lokale Kopie mehr erzeugen. Die eigene Nachricht wird nach
            # der Hotspot-Rückmeldung aus demselben WebService-Strom wie alle
            # anderen Nachrichten angezeigt. Dadurch kann sie unter „Alle“ nicht
            # ein zweites Mal auftauchen.

            self.send_log.setText(f"Letzter Sendeauftrag {timestamp}: → {target} | {text} | HTTP {method} 200")
            self.status.setText(ui_text("Sendeauftrag an den Hotspot übertragen – warte auf Node-Rückmeldung"))
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
            self.status.setText(ui_text(f"Senden fehlgeschlagen: {exc}"))
            self.send_log.setText(ui_text("Letzter Sendeauftrag: FEHLER – ") + str(exc))
        finally:
            self.send_button.setEnabled(True)

    def closeEvent(self, event):
        # Stop the UDP listener before Qt tears down the window/application.
        # Keeping this shutdown path in one closeEvent avoids a second method
        # silently overriding the cleanup logic.
        self.udp_stop.set()
        if self.udp_socket is not None:
            try:
                self.udp_socket.close()
            except Exception:
                pass
        try:
            self._write_settings()
        finally:
            event.accept()

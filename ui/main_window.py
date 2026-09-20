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
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, QUrl, Signal, QPointF, QRectF, QTranslator, QLibraryInfo
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except Exception:
    QWebEngineView = None
try:
    from PySide6.QtWebEngineCore import QWebEnginePage
except Exception:
    QWebEnginePage = None
try:
    from PySide6.QtMultimedia import QSoundEffect
except Exception:
    QSoundEffect = None
from PySide6.QtGui import QAction, QActionGroup, QTextCursor, QDesktopServices, QColor, QPainter, QPen, QPolygonF, QPixmap, QIcon, QCursor
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
    QMessageBox,
    QScrollArea,
    QSplitter,
    QStackedWidget,
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
from core.backup_restore import create_backup, restore_backup
from core.update_checker import UpdateChecker
from version import VERSION

# WebKitGTK is used only on Linux. Windows keeps the proven QtWebEngine
# implementation for the Worldwide tab.
if platform.system().lower() == "linux":
    try:
        from ui.gtk_webkit_worldwide import GtkWebKitWorldwide, GTK_WEBKIT_AVAILABLE
    except Exception:
        GtkWebKitWorldwide = None
        GTK_WEBKIT_AVAILABLE = False
else:
    GtkWebKitWorldwide = None
    GTK_WEBKIT_AVAILABLE = False


CALLSIGN_RE = re.compile(r"\b[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?\b", re.IGNORECASE)
ROOM_RE = re.compile(r"(?:>|&gt;)\s*(\d{1,8})\b")
TARGET_RE = re.compile(r"(?:>|&gt;)\s*([A-Z0-9]{1,6}(?:-[0-9]{1,2})?)\b", re.IGNORECASE)
OWN_CALLSIGN = ""  # eigenes Rufzeichen kommt ausschließlich aus settings.ini


DIRECT_HEADER_RE = re.compile(
    r"(?P<left>(?:[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?\s*,?\s*)+)"
    r">\s*(?P<right>[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?)"
    r"(?=\s|$)",
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
    def __init__(self, text, outgoing=False, link_color="#062f6f", parent=None):
        super().__init__(parent)
        self.outgoing = outgoing
        self.link_color = str(link_color or "#062f6f")
        self.bg = QColor("#78d86b" if outgoing else "#4d98e8")
        self.border = QColor("#6bc65f" if outgoing else "#4186ce")
        self.label = QLabel()
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setWordWrap(True)
        self.label.setOpenExternalLinks(False)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)
        self.label.setStyleSheet("background: transparent; color: #081018; border: none;")
        self.label.linkActivated.connect(self._link_activated)
        self._content_html = ""
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
        self._content_html = str(text)
        # Force the user-selected color directly into every clickable link.
        # This avoids Qt theme/link defaults overriding the chosen color.
        def color_link(match):
            attrs = match.group(1) or ""
            style_match = re.search(r"\bstyle\s*=\s*([\"\'])(.*?)\1", attrs, re.I | re.S)
            if style_match:
                style = style_match.group(2)
                style = re.sub(r"(?:^|;)\s*color\s*:[^;]+;?", ";", style, flags=re.I)
                new_style = f"color:{self.link_color};" + style
                attrs = attrs[:style_match.start(2)] + new_style + attrs[style_match.end(2):]
            else:
                attrs += f' style="color:{self.link_color};"'
            return f"<a{attrs}>"
        text = re.sub(r"<a\b([^>]*)>", color_link, str(text), flags=re.I)
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
    callsignActionClicked = Signal(str, str)

    @staticmethod
    def _normalize_color(value):
        color = QColor(str(value or "#101722").strip())
        return color.name(QColor.NameFormat.HexRgb) if color.isValid() else "#101722"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chat_background = "#101722"
        self.chat_text_color = "#e6edf3"
        self.chat_link_color = "#062f6f"
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

    def set_chat_colors(self, background, text, link=None):
        """Apply chat colors without changing the actual message layout."""
        self.chat_background = self._normalize_color(background)
        self.chat_text_color = self._normalize_color(text)
        self.chat_link_color = self._normalize_color(link or self.chat_link_color)
        self._apply_scroll_style()
        self._apply_html_style()
        if hasattr(self, "_bubble_container"):
            self._bubble_container.setStyleSheet(f"background: {self.chat_background};")
        for bubble in self.findChildren(BubbleWidget):
            try:
                bubble.link_color = self.chat_link_color
                bubble.set_content(bubble._content_html, bubble.width())
            except Exception:
                pass
        for browser in getattr(self, "_all_message_views", []):
            browser.setStyleSheet(
                f"QTextBrowser {{ background: {self.chat_background}; color: {self.chat_text_color}; border: none; }}"
            )
        self.viewport().update()
        self.update()

    def _anchor_clicked(self, url):
        value = url.toString().strip()
        if value.startswith("meshcom://call/"):
            callsign = value.rsplit("/", 1)[-1]
            callsign = re.sub(r"[^A-Za-z0-9-]", "", callsign).upper()
            if not callsign:
                return

            # Nicht-modal öffnen: menu.exec() kann auf dem Raspberry Pi mit
            # der Qt/GTK-Integration einen blockierenden Event-Loop erzeugen.
            # popup() lässt den normalen Qt-Event-Loop weiterlaufen.
            menu = QMenu(self)
            private_action = menu.addAction(ui_text("Privat Chat"))
            mention_action = menu.addAction(f"@{callsign}")
            menu.addSeparator()
            qrz_action = menu.addAction("QRZ.com")

            private_action.triggered.connect(
                lambda _checked=False, c=callsign: self.callsignActionClicked.emit(c, "private")
            )
            mention_action.triggered.connect(
                lambda _checked=False, c=callsign: self.callsignActionClicked.emit(c, "mention")
            )
            qrz_action.triggered.connect(
                lambda _checked=False, c=callsign: self.callsignActionClicked.emit(c, "qrz")
            )

            # Referenz bis zum Schließen behalten; kein modaler Dialog.
            self._callsign_menu = menu
            menu.aboutToHide.connect(lambda: setattr(self, "_callsign_menu", None))
            menu.popup(QCursor.pos())
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
        browser.setHtml(f"<style>a {{ color: {self.chat_link_color}; }}</style>" + str(html_text))
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
        self._html_view.setHtml(f"<style>a {{ color: {self.chat_link_color}; }}</style>" + str(html_text))

        def restore():
            new_bar = self._html_view.verticalScrollBar()
            if was_at_bottom:
                new_bar.setValue(new_bar.maximum())
            else:
                new_bar.setValue(min(old_value, new_bar.maximum()))
        QTimer.singleShot(0, restore)

    def set_bubbles(self, items):
        """Display the same real bubble data used by room/private chats."""
        self._all_mode = False
        self._bubble_mode = True
        self._bubble_items = [dict(item) for item in (items or [])]
        old = self.verticalScrollBar()
        oldv = old.value()
        oldm = old.maximum()
        bottom = oldm <= 0 or oldv >= max(0, oldm - 8)
        container = QWidget()
        container.setStyleSheet(f"background:{self.chat_background};")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(8)
        self._bubble_rows = []
        for item in self._bubble_items:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            bubble = BubbleWidget(
                str(item.get('html', '')),
                bool(item.get('outgoing', False)),
                self.chat_link_color,
            )
            bubble.set_content(
                str(item.get('html', '')),
                max(260, int(self.viewport().width() * 0.75)),
            )
            self._bubble_rows.append(bubble)
            if item.get('outgoing', False):
                row.addStretch(1)
                row.addWidget(bubble, 0, Qt.AlignmentFlag.AlignRight)
            else:
                row.addWidget(bubble, 0, Qt.AlignmentFlag.AlignLeft)
                row.addStretch(1)
            lay.addLayout(row)
        lay.addStretch(1)
        self._bubble_container = container
        self._bubble_layout = lay
        self.setWidget(container)
        container.adjustSize()
        QTimer.singleShot(0, lambda: self.verticalScrollBar().setValue(
            self.verticalScrollBar().maximum() if bottom else min(oldv, self.verticalScrollBar().maximum())
        ))

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
    # MH-Liste: maximal 250 zuletzt gehörte Stationen im Speicher.
    MH_MAX_STATIONS = 250
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
        # Etwas breiteres Hauptfenster, damit die Onlinezeit und die
        # Dashboard-Kopfzeile vollständig sichtbar bleiben.
        self.resize(1634, 950)
        self.setMinimumSize(1434, 900)
        # Nach einem Restore darf closeEvent die gerade wiederhergestellten
        # Dateien nicht mit dem alten In-Memory-Zustand überschreiben.
        self._skip_settings_write_on_close = False

        settings = load_settings()
        self.language = settings.get("language", "de") if settings.get("language", "de") in ("de", "en", "it", "nl", "fr") else "de"
        set_language(self.language)
        # Let Qt translate its own standard context menus (Undo/Copy/Paste/...).
        # This is safer than intercepting ContextMenu events with a global
        # event filter and avoids shutdown/segmentation-fault side effects.
        self._qt_translator = QTranslator(self)
        self._qt_translator_loaded = False
        self._apply_qt_translation(self.language)
        self.chat_background = self._normalize_chat_color(settings.get("chat_background", "#101722"))
        self.chat_text_color = self._normalize_chat_color(settings.get("chat_text_color", "#e6edf3"))
        self.chat_link_color = self._normalize_chat_color(settings.get("chat_link_color", "#062f6f"))
        self._all_chat_views = []
        self.current_theme = settings.get("theme", "dark").strip().lower()
        self.layout_mode = settings.get("layout_mode", "classic").strip().lower()
        if self.layout_mode not in {"classic", "dashboard"}:
            self.layout_mode = "classic"
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
        # Verbindungsanzeige: Die Onlinezeit wird über automatische
        # Reconnects hinweg fortgeführt. Nur ein bewusstes manuelles
        # Trennen setzt die Gesamtzeit zurück.
        self.connection_online = False
        self.connection_since = None
        self.connection_elapsed = 0
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
        self.dashboard_current_key = ("all", "all")
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
        # Session counter for received telemetry packets. Kept separately from
        # the monitor buffer so clearing the monitor does not erase the statistic.
        self.telemetry_count = 0
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

        # Verbindungssteuerung:
        # - Kein automatisches Verbinden beim Programmstart.
        # - Nach einem manuellen Klick auf "Verbinden" bleibt die Verbindung
        #   für Auto-Reconnect freigegeben, auch wenn ein späterer Abruf
        #   vorübergehend fehlschlägt.
        # - "Trennen" deaktiviert Auto-Reconnect ausdrücklich.
        self.connected = False
        self.auto_reconnect_enabled = False
        self.reconnect_in_progress = False

        # Ergänzende Datensicherung / Update-Prüfung. Diese Helfer arbeiten
        # unabhängig von Empfang, Chat, Dashboard und MeshCom-Verbindung.
        self.update_checker = UpdateChecker(self)
        self.update_checker.result.connect(self._handle_update_check_result)

        self._build_menu()
        self._build_ui(settings)
        self._apply_language_ui()
        self._apply_theme(self.current_theme)
        self._load_filter_fields(settings)
        # Dashboard is built before the saved filter fields are loaded.
        # Rebuild its room-chat navigation now so the persistent five rooms
        # are the source of truth from the first screen.
        if hasattr(self, "dashboard_sidebar"):
            sidebar_layout = self.dashboard_sidebar.layout()
            self._dashboard_rebuild_room_buttons(sidebar_layout)
        self._set_weather_panel_visible(self.weather_enabled)
        self.weatherUpdated.connect(self._apply_weather_result)
        # Wenn Wetterdaten dauerhaft aktiviert sind, beim Start automatisch
        # eine frische WX-Information vom MeshCom-Node laden. Die kurze
        # Verzögerung stellt sicher, dass das Hauptfenster und die Verbindung
        # vollständig initialisiert sind.
        if self.weather_enabled:
            QTimer.singleShot(1500, self._refresh_weather)

        # Leise Update-Prüfung nach dem vollständigen Aufbau des Fensters.
        # Es wird niemals automatisch heruntergeladen oder installiert.
        QTimer.singleShot(3000, self._check_for_updates_silent)

        # Eigenständiger MeshCom-Positions-/Status-Empfang direkt per UDP.
        self._start_udp_listener(1799)

        # Watchdog: der UDP-Empfang darf nicht dauerhaft ausfallen, nur weil
        # der Hintergrund-Thread oder der Socket unerwartet beendet wurde.
        # Alle fünf Sekunden wird ausschließlich geprüft, ob der Listener
        # noch lebt; nur bei einem tatsächlich beendeten Thread wird er neu
        # gestartet. Die normale Monitor-/MH-Verarbeitung bleibt unverändert.
        self.udp_watchdog_timer = QTimer(self)
        self.udp_watchdog_timer.timeout.connect(self._ensure_udp_listener)
        self.udp_watchdog_timer.start(5000)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_messages)
        self.timer.start(5000)

        # Uhr und Datum auf der Oberfläche aktuell halten.
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()

        # Selbstheilungs-Watchdog für die eingebettete Weltweit-Webseite.
        # Die Seite wird NICHT regelmäßig neu geladen: Es wird nur geprüft,
        # ob der Chromium-Renderer noch antwortet. Erst wenn keine Antwort
        # mehr kommt oder der Renderer beendet wurde, wird die Ansicht neu
        # geladen und anschließend ACTIVITY wieder ausgewählt.
        self._worldwide_health_last_ok = time.monotonic()
        self._worldwide_health_pending = False
        self._worldwide_reload_pending = False
        self.worldwide_watchdog_timer = QTimer(self)
        self.worldwide_watchdog_timer.timeout.connect(self._worldwide_watchdog_tick)
        self.worldwide_watchdog_timer.start(15000)

        # Keine automatische Verbindung beim Programmstart.
        # Der Benutzer entscheidet mit "Verbinden", wann der WebService abgefragt wird.

    # ---------- MeshCom UDP-Schnittstelle ----------
    def _ensure_udp_listener(self):
        """Restart the UDP listener only if its worker thread really stopped."""
        thread = getattr(self, "udp_thread", None)
        if thread is not None and thread.is_alive():
            return
        # Ein alter Socket wird vom Worker in seinem finally-Block geschlossen.
        # Ein kurzer Neustartversuch hält den Monitor auch nach einem
        # vorübergehenden Socket-/Netzwerkfehler funktionsfähig.
        self.udp_status = "UDP 1799: Neustart des Empfangs …"
        try:
            self._start_udp_listener(1799)
        except Exception as exc:
            self.udp_status = f"UDP 1799 Neustart fehlgeschlagen: {exc}"

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
            if temp != "": parts.append(f"{ui_text('Temperatur')} {self._monitor_num(temp, 1)} °C")
            if hum != "": parts.append(f"{ui_text('Luftfeuchte')} {self._monitor_num(hum, 1)} %")
            if qfe != "": parts.append(f"QFE {self._monitor_num(qfe, 1)} hPa")
            if qnh != "": parts.append(f"QNH {self._monitor_num(qnh, 1)} hPa")
            if co2 != "": parts.append(f"CO₂ {self._monitor_num(co2, 0)} ppm")
            if gas != "": parts.append(f"Gas {self._monitor_num(gas, 0)}")
            if hum0 != "": parts.append(f"Hum {self._monitor_num(hum0, 0)}")
            if temp2 != "": parts.append(f"Temp2 {self._monitor_num(temp2, 1)} °C")
            if batt != "": parts.append(f"Batt {self._monitor_num(batt, 0)} %")
            if volt != "": parts.append(f"Volt {self._monitor_num(volt, 2)} V")
            detail = "  ·  ".join(parts) or ui_text("Telemetry")
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
                    # Only merge the echo with the exact local text.
                    # A suffix match can incorrectly consume a later message
                    # (for example "test" after "my test").
                    echo_text = re.sub(r"^#\d{1,6}\s*", "", str(detail)).strip()
                    if str(existing.get("_text", "")).strip().casefold() == echo_text.casefold():
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

        count_text = ui_text(f"{len(rows)} angezeigt · {len(self.monitor_rows)} gespeichert")
        self.monitor_count_label.setText(count_text)
        if hasattr(self, "dashboard_monitor_count_label"):
            self.dashboard_monitor_count_label.setText(count_text)
        if hasattr(self, "dashboard_monitor_filter_combo"):
            combo = self.dashboard_monitor_filter_combo
            current_data = combo.currentData()
            if current_data != self.monitor_filter:
                combo.blockSignals(True)
                idx = combo.findData(self.monitor_filter)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                combo.blockSignals(False)
        if hasattr(self, "dashboard_monitor_search_edit") and self.dashboard_monitor_search_edit.text() != self.monitor_search:
            self.dashboard_monitor_search_edit.blockSignals(True)
            self.dashboard_monitor_search_edit.setText(self.monitor_search)
            self.dashboard_monitor_search_edit.blockSignals(False)
        if hasattr(self, "dashboard_monitor_autoscroll_check") and self.dashboard_monitor_autoscroll_check.isChecked() != self.monitor_autoscroll:
            self.dashboard_monitor_autoscroll_check.blockSignals(True)
            self.dashboard_monitor_autoscroll_check.setChecked(self.monitor_autoscroll)
            self.dashboard_monitor_autoscroll_check.blockSignals(False)
        if self.monitor_autoscroll and rows:
            self.monitor_table.scrollToBottom()
        # Keep the dashboard copy live whenever the classic monitor changes.
        self._sync_dashboard_tables()

    def _set_monitor_filter(self, value):
        self.monitor_filter = value
        self._render_monitor()

    def _set_monitor_filter_index(self, index):
        sender = self.sender()
        value = sender.itemData(index) if sender is not None else None
        if not value and sender is not None:
            value = sender.itemText(index)
        self._set_monitor_filter(str(value or "ALLE"))

    def _set_monitor_search(self, text):
        self.monitor_search = text
        self._render_monitor()

    def _toggle_monitor_autoscroll(self, checked):
        self.monitor_autoscroll = checked
        if checked:
            self.monitor_table.scrollToBottom()

    def _toggle_monitor_pause(self):
        self.monitor_paused = not self.monitor_paused
        label = ui_text("▶ Weiter" if self.monitor_paused else "⏸ Pause")
        self.monitor_pause_button.setText(label)
        if hasattr(self, "dashboard_monitor_pause_button"):
            self.dashboard_monitor_pause_button.setText(label)

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
        """Update MH only from stations actually received over LoRa.

        EXTUDP uses ``src`` as a source/relay path and ``src_type`` to tell
        where the packet came from.  Packets with ``src_type=udp`` are
        server/gateway traffic and must not create a "heard" station.
        For LoRa packets the FIRST callsign in ``src`` is the original
        sender; later callsigns are relay hops and are therefore ignored.
        """
        if not isinstance(packet, dict):
            return

        src_type = str(packet.get("src_type", packet.get("source_type", "")) or "").strip().lower()
        # According to the MeshCom EXTUDP protocol, only these source types
        # represent packets received from the LoRa side.  In particular,
        # ``udp`` must never populate MH because it can contain gateway/server
        # traffic and relay paths that are not locally heard stations.
        if src_type not in {"lora", "node"}:
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
        now_ts = time.time()
        row = self.mh_stations.setdefault(callsign, {
            "callsign": callsign, "lat": None, "lon": None,
            "rssi": None, "snr": None, "battery": None,
            "last_heard": now, "last_heard_ts": now_ts, "alt": None, "firmware": "",
        })
        row["last_heard"] = now
        row["last_heard_ts"] = now_ts

        # Nur die 250 zuletzt gehörten Stationen behalten. Der älteste
        # Eintrag wird entfernt, sobald die Obergrenze überschritten wird.
        if len(self.mh_stations) > self.MH_MAX_STATIONS:
            oldest_callsign = min(
                self.mh_stations,
                key=lambda key: self.mh_stations[key].get("last_heard_ts", 0.0),
            )
            del self.mh_stations[oldest_callsign]

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
        telemetry_count = getattr(self, "telemetry_count", 0)
        monitor_count = len(self.monitor_rows)

        private_count = 0
        room_counts = {}
        for block in self.message_cache.values():
            participants = self._private_participants(block)
            if participants:
                private_count += 1
                continue
            # Die Raumzuordnung kommt aus dem echten MeshCom-Ziel im Header
            # (z. B. ``CALL>20``), nicht aus dem sichtbaren Wort "Raum".
            # Nachrichten ohne erkennbares numerisches Ziel bleiben in "Alle".
            room = self._room_from_block(block)
            room_key = room if room else "Alle"
            room_counts[room_key] = room_counts.get(room_key, 0) + 1

        self.statistics_summary.setText(
            f"{ui_text('Nachrichten:')} <b>{message_count}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"{ui_text('Nodes:')} <b>{node_count}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"{ui_text('Positionen:')} <b>{position_count}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"{ui_text('Telemetrie:')} <b>{telemetry_count}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"{ui_text('Privatnachrichten:')} <b>{private_count}</b><br>"
            f"{ui_text('Monitor-Einträge:')} <b>{monitor_count}</b>"
        )

        if room_counts:
            room_label = ui_text("Raum")
            parts = [f"{room_label} {room}: <b>{count}</b>" for room, count in sorted(room_counts.items(), key=lambda x: (x[0] != "Alle", int(x[0]) if x[0] != "Alle" else -1))]
            self.statistics_room_label.setText("<b>" + ui_text("Nachrichten nach Raum:") + "</b><br>" + " &nbsp;&nbsp; | &nbsp;&nbsp; ".join(parts))
        else:
            self.statistics_room_label.setText("<b>" + ui_text("Nachrichten nach Raum:") + "</b> " + ui_text("noch keine Daten"))

        # Dashboard statistics are a live view of the same session counters.
        if hasattr(self, "dashboard_statistics_label"):
            self._sync_dashboard_tables()

    def _render_mh(self):
        if not hasattr(self, "mh_table"):
            return
        rows = sorted(self.mh_stations.values(), key=lambda r: (r.get("last_heard_ts", 0.0), r.get("last_heard", "")), reverse=True)
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
        # Keep the dashboard MH table live as stations are updated.
        self._sync_dashboard_tables()

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
        ptype = str(packet.get("type", packet.get("packet_type", ""))).lower().strip()
        if ptype in {"tel", "tele", "telemetry", "status"}:
            self.telemetry_count += 1
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

        export_action = QAction("Chat exportieren …", self)
        export_action.triggered.connect(self._export_current_chat)
        file_menu.addAction(export_action)
        self.export_chat_action = export_action

        backup_action = QAction(ui_text("Datensicherung erstellen …"), self)
        backup_action.triggered.connect(self._create_backup_from_menu)
        file_menu.addAction(backup_action)
        self.backup_action = backup_action

        restore_action = QAction(ui_text("Datensicherung wiederherstellen …"), self)
        restore_action.triggered.connect(self._restore_backup_from_menu)
        file_menu.addAction(restore_action)
        self.restore_action = restore_action
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

        # Darstellung: Zwischen der bisherigen klassischen Oberfläche und
        # dem neuen Dashboard kann jederzeit umgeschaltet werden. Beide
        # Ansichten verwenden dieselben vorhandenen Funktionen/Daten.
        display_menu = settings_menu.addMenu("Darstellung")
        self.classic_layout_action = QAction("Klassisch", self)
        self.classic_layout_action.setCheckable(True)
        self.dashboard_layout_action = QAction("Dashboard", self)
        self.dashboard_layout_action.setCheckable(True)
        layout_group = QActionGroup(self)
        layout_group.setExclusive(True)
        layout_group.addAction(self.classic_layout_action)
        layout_group.addAction(self.dashboard_layout_action)
        display_menu.addAction(self.classic_layout_action)
        display_menu.addAction(self.dashboard_layout_action)
        self.classic_layout_action.triggered.connect(lambda: self._set_layout_mode("classic"))
        self.dashboard_layout_action.triggered.connect(lambda: self._set_layout_mode("dashboard"))
        self.display_menu = display_menu

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

        help_menu.addSeparator()
        update_action = QAction(ui_text("Nach Update suchen …"), self)
        update_action.triggered.connect(self._check_for_updates_manual)
        help_menu.addAction(update_action)
        self.update_action = update_action

    # ---------- Ergänzende Datensicherung / Update-Prüfung ----------
    def _create_backup_from_menu(self):
        default_name = f"MeshCom-Guru_Backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.zip"
        path, _ = QFileDialog.getSaveFileName(
            self,
            ui_text("Datensicherung erstellen"),
            str(Path.home() / default_name),
            "MeshCom-Guru Backup (*.zip);;ZIP-Dateien (*.zip);;Alle Dateien (*)",
        )
        if not path:
            return
        if not path.lower().endswith(".zip"):
            path += ".zip"

        ok, result = create_backup(path)
        if ok:
            QMessageBox.information(
                self,
                ui_text("Datensicherung"),
                ui_text("Datensicherung erfolgreich erstellt: ") + result,
            )
        else:
            QMessageBox.critical(
                self,
                ui_text("Datensicherung"),
                ui_text("Datensicherung fehlgeschlagen: ") + result,
            )

    def _restore_backup_from_menu(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            ui_text("Datensicherung wiederherstellen"),
            str(Path.home()),
            "MeshCom-Guru Backup (*.zip);;ZIP-Dateien (*.zip);;Alle Dateien (*)",
        )
        if not path:
            return

        answer = QMessageBox.question(
            self,
            ui_text("Datensicherung wiederherstellen"),
            ui_text(
                "Die persönlichen Einstellungen aus dem Backup werden in ~/.MeshCom "
                "wiederhergestellt. Nicht zum Backup gehörende Dateien werden nicht gelöscht. "
                "Nach der Wiederherstellung ist ein Neustart von MeshCom-Guru erforderlich. "
                "Fortfahren?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        ok, result = restore_backup(path)
        if ok:
            # Die wiederhergestellten Werte sofort aus der neuen settings.ini
            # laden, damit auch die laufende Oberfläche den Backup-Stand kennt.
            self._reload_restored_settings()
            restart = QMessageBox.question(
                self,
                ui_text("Datensicherung"),
                ui_text("Datensicherung erfolgreich wiederhergestellt. MeshCom-Guru jetzt beenden, damit die Einstellungen beim nächsten Start übernommen werden?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if restart == QMessageBox.StandardButton.Yes:
                # Beim anschließenden Beenden darf closeEvent NICHT den alten
                # In-Memory-Zustand erneut in settings.ini schreiben.
                self._skip_settings_write_on_close = True
                QApplication.quit()
        else:
            QMessageBox.critical(
                self,
                ui_text("Datensicherung"),
                ui_text("Wiederherstellung fehlgeschlagen: ") + result,
            )

    def _reload_restored_settings(self):
        """Synchronize restored settings into the currently running UI.

        The restore itself writes the files to ~/.MeshCom. This method only
        updates the existing widgets/state; it deliberately does not call
        _write_settings(), so the restored backup remains authoritative.
        """
        settings = load_settings()
        try:
            self.language = settings.get("language", "de") if settings.get("language", "de") in ("de", "en", "it", "nl", "fr") else "de"
            set_language(self.language)
            if hasattr(self, "ip_input"):
                self.ip_input.setText(settings.get("ip", ""))
            if hasattr(self, "target_input"):
                self.target_input.setText(settings.get("target", ""))
            if hasattr(self, "own_callsign_input"):
                self.own_callsign_input.setText(self._normalize_callsign(settings.get("own_callsign", "")))
            if hasattr(self, "own_lat_input"):
                self.own_lat_input.setText(settings.get("own_lat", ""))
            if hasattr(self, "own_lon_input"):
                self.own_lon_input.setText(settings.get("own_lon", ""))
            if hasattr(self, "filter_enabled"):
                self.filter_enabled.setChecked(settings.get("filter_enabled", "0") == "1")
            if hasattr(self, "dashboard_hotspot_input"):
                self.dashboard_hotspot_input.setText(settings.get("ip", ""))
            if hasattr(self, "dashboard_room_input"):
                self.dashboard_room_input.setText(settings.get("target", ""))
            if hasattr(self, "dashboard_callsign_input"):
                self.dashboard_callsign_input.setText(self._normalize_callsign(settings.get("own_callsign", "")))
            if hasattr(self, "dashboard_lat_input"):
                self.dashboard_lat_input.setText(settings.get("own_lat", ""))
            if hasattr(self, "dashboard_lon_input"):
                self.dashboard_lon_input.setText(settings.get("own_lon", ""))

            self.own_callsign = self._normalize_callsign(settings.get("own_callsign", ""))
            try:
                self.own_lat = float(settings.get("own_lat", "").replace(",", ".")) if settings.get("own_lat", "") else None
                self.own_lon = float(settings.get("own_lon", "").replace(",", ".")) if settings.get("own_lon", "") else None
            except (TypeError, ValueError):
                self.own_lat = self.own_lon = None

            self.quick_texts = self._load_quick_texts(settings)
            self._load_filter_fields(settings)
            self._apply_language_ui()
            self.status.setText(ui_text("Datensicherung geladen – Neustart erforderlich"))
        except Exception as exc:
            self.status.setText(ui_text("Backup geladen, Oberfläche wird beim Neustart vollständig übernommen: ") + str(exc))

    def _check_for_updates_silent(self):
        """Check in the background and only notify when a newer release exists."""
        self._update_check_manual = False
        self.update_checker.check_async(VERSION)

    def _check_for_updates_manual(self):
        """Manual update check; also reports when the installed version is current."""
        self._update_check_manual = True
        self.update_checker.check_async(VERSION)

    def _handle_update_check_result(self, result):
        manual = bool(getattr(self, "_update_check_manual", False))
        self._update_check_manual = False

        if not result.get("ok"):
            if manual:
                QMessageBox.warning(
                    self,
                    ui_text("Nach Update suchen"),
                    ui_text("Die GitHub-Release-Prüfung konnte nicht durchgeführt werden: ")
                    + str(result.get("error", "")),
                )
            return

        current = result.get("current", VERSION)
        latest = result.get("latest", current)
        url = result.get("url", "https://github.com/Angonikro/MeshCom-Guru/releases/latest")

        if result.get("update_available"):
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Information)
            box.setWindowTitle(ui_text("Update verfügbar"))
            box.setText(
                ui_text("Eine neue MeshCom-Guru-Version ist verfügbar.")
                + f"\n\n{ui_text('Installiert')}: v{current}\n"
                + f"{ui_text('Neu')}: v{latest}"
            )
            open_button = box.addButton(ui_text("GitHub Release öffnen"), QMessageBox.ButtonRole.AcceptRole)
            box.addButton(QMessageBox.StandardButton.Close)
            box.exec()
            if box.clickedButton() is open_button:
                QDesktopServices.openUrl(QUrl(url))
        elif manual:
            QMessageBox.information(
                self,
                ui_text("Nach Update suchen"),
                ui_text("Du verwendest bereits die aktuelle Version.")
                + f"\n\n{ui_text('Installiert')}: v{current}",
            )

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

        # Schaltflächenzeile der klassischen Ansicht. Diese wurde beim
        # Dashboard-Umbau versehentlich nicht mehr angelegt.
        settings_buttons = QHBoxLayout()
        settings_buttons.addWidget(self.save_button, 1)
        settings_buttons.addWidget(self.node_info_button, 1)

        self.filter_enabled = QCheckBox("Raumfilter aktiv")
        self.filter_enabled.setChecked(settings.get("filter_enabled", "0") == "1")
        self.filter_enabled.toggled.connect(self._filter_toggled)

        self.filter_inputs = []
        filter_row = QHBoxLayout()
        for i in range(5):
            field = QLineEdit()
            field.setPlaceholderText(ui_text("Raum") + f" {i + 1}")
            field.setMaxLength(10)
            # Gespeicherte Räume beim Programmstart wiederherstellen.
            field.setText(settings.get(f"filter_room{i + 1}", ""))
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

        # Im Dashboard darf nur ein Map-WebEngine aktiv sein. Die klassische
        # Ansicht bekommt deshalb im Dashboard-Modus zunächst nur einen
        # leichten Platzhalter. Beim Umschalten wird die echte WebEngine
        # dynamisch erzeugt. Das verhindert mehrere Chromium-Prozesse auf
        # Raspberry Pi und reduziert die Absturzgefahr deutlich.
        self._map_ready = False
        self._map_pending_stations = []
        if self.layout_mode == "classic":
            self._create_classic_map_view()
        else:
            self.map_view = QLabel("Karte ist im Dashboard aktiv.")
            self.map_view.setMinimumHeight(300)
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
        self.monitor_pause_button.setFixedWidth(130)
        self.monitor_pause_button.clicked.connect(self._toggle_monitor_pause)
        monitor_toolbar.addWidget(self.monitor_pause_button)

        monitor_clear_button = QPushButton("Leeren")
        monitor_clear_button.setFixedWidth(116)
        monitor_clear_button.clicked.connect(self._clear_monitor)
        monitor_toolbar.addWidget(monitor_clear_button)

        monitor_toolbar.addWidget(QLabel("Filter:"))
        self.monitor_filter_combo = QComboBox()
        self.monitor_filter_combo.addItem(ui_text("Alle"), "ALLE")
        self.monitor_filter_combo.addItems(["MSG", "POS", "TEL", "ACK"])
        self.monitor_filter_combo.setCurrentIndex(max(0, self.monitor_filter_combo.findData(self.monitor_filter)))
        self.monitor_filter_combo.setFixedWidth(78)
        self.monitor_filter_combo.currentIndexChanged.connect(self._set_monitor_filter_index)
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
        # Monitor-Nachrichten dürfen nicht abgeschnitten werden.  Die
        # Information-Spalte bekommt den verfügbaren Rest der Breite; lange
        # Nachrichten werden innerhalb der Zelle umgebrochen und die
        # Zeilenhöhe automatisch angepasst.  Dadurch bleibt der komplette
        # Nachrichtentext sichtbar, auch bei schmaleren Fenstern.
        self.monitor_table.setWordWrap(True)
        self.monitor_table.verticalHeader().setVisible(False)
        self.monitor_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.monitor_table.setShowGrid(True)
        self.monitor_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        header = self.monitor_table.horizontalHeader()
        header.setStretchLastSection(False)
        for col in range(6):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        for col, width in {0: 70, 1: 50, 2: 108, 3: 108, 4: 55, 5: 55}.items():
            self.monitor_table.setColumnWidth(col, width)
        self.monitor_table.setColumnWidth(6, 420)
        self.monitor_table.setMinimumWidth(700)
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
        statistics_view_layout = QVBoxLayout(self.statistics_view)
        statistics_view_layout.setContentsMargins(0, 0, 0, 0)

        statistics_scroll = QScrollArea()
        statistics_scroll.setWidgetResizable(True)
        statistics_scroll.setFrameShape(QFrame.Shape.NoFrame)
        statistics_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        statistics_content = QWidget()
        statistics_layout = QVBoxLayout(statistics_content)
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
        statistics_scroll.setWidget(statistics_content)
        statistics_view_layout.addWidget(statistics_scroll)

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

        # ---------- 🌐 Weltweit ----------
        # Zusätzlicher Tab direkt neben der Karte. Die vorhandene Logik
        # bleibt unverändert; die ÖVSV-Seite übernimmt ihre eigene Aktualisierung.
        if self.layout_mode == "classic":
            self._create_classic_worldwide_view()
        else:
            self.worldwide_view = QLabel("Weltweit ist im Dashboard aktiv.")
        self.worldwide_tab_index = self.tabs.insertTab(
            self.map_tab_index + 1, self.worldwide_view, ui_text("🌐 Weltweit")
        )
        self.tabs.tabBar().setTabButton(
            self.worldwide_tab_index,
            self.tabs.tabBar().ButtonPosition.RightSide,
            None,
        )

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
        self._emoji_target = None

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

        self.message_label = QLabel("Nachricht:")
        self.classic_message_panel = QWidget()
        classic_message_layout = QVBoxLayout(self.classic_message_panel)
        classic_message_layout.setContentsMargins(0, 0, 0, 0)
        classic_message_layout.setSpacing(4)
        classic_message_layout.addWidget(self.message_label)

        message_row = QHBoxLayout()
        message_row.addWidget(self.message_input, 1)
        message_row.addWidget(self.quick_text_button)
        message_row.addWidget(self.emoji_button)
        message_row.addWidget(self.message_counter)
        classic_message_layout.addLayout(message_row)

        classic_message_buttons = QWidget()
        classic_buttons_layout = QHBoxLayout(classic_message_buttons)
        classic_buttons_layout.setContentsMargins(0, 0, 0, 0)
        classic_buttons_layout.addWidget(self.send_button)
        classic_buttons_layout.addWidget(self.update_button)
        classic_message_layout.addWidget(classic_message_buttons)
        classic_message_layout.addWidget(self.send_log)
        classic_message_layout.addWidget(self.status)
        self.classic_message_buttons = classic_message_buttons

        # Die klassische Oberfläche ist ein kompletter Seiteninhalt.
        # Dadurch wird beim Dashboard-Modus wirklich die gesamte klassische
        # Oberfläche ausgeblendet und nicht nur der Tab-Bereich.
        classic_view = QWidget()
        classic_view.setObjectName("ClassicView")
        classic_view_layout = QVBoxLayout(classic_view)
        classic_view_layout.setContentsMargins(0, 0, 0, 0)
        classic_view_layout.setSpacing(4)
        classic_view_layout.addLayout(top_row)
        classic_view_layout.addLayout(form)
        classic_view_layout.addLayout(settings_buttons)
        classic_view_layout.addLayout(filter_box)
        classic_view_layout.addWidget(self.weather_panel)
        classic_view_layout.addWidget(self.tabs, 1)
        classic_view_layout.addWidget(self.classic_message_panel)
        self.classic_view = classic_view

        # Ein einziger Stack für die komplette Arbeitsfläche.
        self.layout_stack = QStackedWidget()
        self.layout_stack.addWidget(self.classic_view)

        # Dashboard erst beim ersten Umschalten erzeugen. Das vermeidet beim
        # normalen Start zusätzliche WebEngine-Instanzen.
        self.dashboard_view = None

        self._apply_layout_mode(self.layout_mode, save=False)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.layout_stack, 1)
        self.setCentralWidget(central)

    def _create_classic_map_view(self):
        """Create the classic map WebEngine only when classic mode is active."""
        if QWebEngineView is None:
            self.map_view = QLabel(
                "Kartenansicht benötigt PySide6-WebEngine.\nBitte requirements.txt erneut installieren."
            )
            self.map_view.setMinimumHeight(300)
            return
        self.map_view = QWebEngineView()
        self.map_view.setMinimumHeight(300)
        self.map_view.loadFinished.connect(self._map_load_finished)
        self.map_view.setHtml(self._map_html([]), QUrl("https://meshcom-guru.local/"))

    def _create_classic_worldwide_view(self):
        """Use WebKitGTK on Linux; keep QtWebEngine on Windows."""
        if platform.system().lower() == "linux" and GtkWebKitWorldwide is not None and GTK_WEBKIT_AVAILABLE:
            self.worldwide_view = GtkWebKitWorldwide("https://meshcom.oevsv.at/#")
            return
        if QWebEngineView is None:
            self.worldwide_view = QLabel(
                "Weltweit benötigt QtWebEngine.\nBitte requirements.txt erneut installieren."
            )
            return
        self.worldwide_view = QWebEngineView()
        self.worldwide_view.loadFinished.connect(self._worldwide_load_finished)
        self.worldwide_view.renderProcessTerminated.connect(self._worldwide_render_terminated)
        self.worldwide_view.setUrl(QUrl("https://meshcom.oevsv.at/#"))

    def _set_webengine_lifecycle(self, view, active):
        """Reduce Chromium RAM for inactive map/worldwide views without deleting widgets.

        The connection, chat widgets and their signals are deliberately not touched.
        If the installed Qt version does not expose lifecycle control, this is a no-op.
        """
        if QWebEngineView is None or QWebEnginePage is None:
            return
        if not isinstance(view, QWebEngineView):
            return
        try:
            page = view.page()
            state_enum = getattr(QWebEnginePage, "LifecycleState", None)
            if state_enum is None:
                return
            state = getattr(state_enum, "Active" if active else "Discarded", None)
            if state is not None:
                page.setLifecycleState(state)
        except (AttributeError, RuntimeError, TypeError):
            # Older PySide6/Qt builds may not provide lifecycle control.
            pass

    def _release_classic_webviews(self):
        """Release classic Chromium views before dashboard mode creates its pair."""
        if not hasattr(self, "tabs"):
            return
        for attr, index, title in (("worldwide_view", self.worldwide_tab_index, ui_text("🌐 Weltweit")),
                                   ("map_view", self.map_tab_index, "Karte")):
            widget = getattr(self, attr, None)
            if QWebEngineView is not None and isinstance(widget, QWebEngineView):
                self.tabs.removeTab(index)
                try:
                    widget.stop()
                except Exception:
                    pass
                widget.setParent(None)
                widget.deleteLater()
                placeholder = QLabel("Weltweit ist im Dashboard aktiv." if attr == "worldwide_view" else "Karte ist im Dashboard aktiv.")
                if attr == "map_view":
                    placeholder.setMinimumHeight(300)
                new_index = self.tabs.insertTab(index, placeholder, title)
                self.tabs.tabBar().setTabButton(new_index, self.tabs.tabBar().ButtonPosition.RightSide, None)
                setattr(self, attr, placeholder)
        QApplication.processEvents()

    def _ensure_classic_webviews(self):
        """Replace dashboard placeholders with the two classic WebEngines."""
        if not hasattr(self, "tabs"):
            return
        for attr, index, title, creator in (("worldwide_view", self.worldwide_tab_index, ui_text("🌐 Weltweit"), self._create_classic_worldwide_view),
                                             ("map_view", self.map_tab_index, "Karte", self._create_classic_map_view)):
            widget = getattr(self, attr, None)
            if QWebEngineView is not None and not isinstance(widget, QWebEngineView):
                self.tabs.removeTab(index)
                creator()
                new_index = self.tabs.insertTab(index, getattr(self, attr), title)
                self.tabs.tabBar().setTabButton(new_index, self.tabs.tabBar().ButtonPosition.RightSide, None)
        QApplication.processEvents()

    def _release_dashboard_view(self):
        """Release dashboard Chromium views before returning to classic mode."""
        if self.dashboard_view is None:
            return
        self.layout_stack.removeWidget(self.dashboard_view)
        self.dashboard_view.setParent(None)
        self.dashboard_view.deleteLater()
        self.dashboard_view = None
        QApplication.processEvents()

    def _apply_layout_mode(self, mode, save=True):
        """Switch between classic UI and dashboard without losing the active target.

        Beim Ansichtswechsel wird die aktuell sichtbare Oberfläche zuerst als
        Quelle verwendet und in ~/.MeshCom/settings.ini gespeichert. Erst danach
        wird die andere Oberfläche aktiviert und die INI neu eingelesen.
        Besonders wichtig: Das Dashboard-Ziel kommt aus dashboard_current_key und
        niemals aus einem der filter_room-Felder.
        """
        mode = mode if mode in {"classic", "dashboard"} else "classic"
        old_mode = getattr(self, "layout_mode", "classic")
        if not hasattr(self, "dashboard_view") or not hasattr(self, "layout_stack"):
            self.layout_mode = mode
            return

        switching = old_mode != mode

        # VOR dem Umschalten die tatsächlich aktive Oberfläche speichern.
        # Dashboard: dashboard_current_key ist die maßgebliche Auswahl.
        # Dadurch kann ein filter_room5=26298 niemals als target übernommen werden.
        if switching and save:
            if old_mode == "dashboard":
                current_key = getattr(self, "dashboard_current_key", None)
                if current_key is not None:
                    if current_key[0] in ("room", "private"):
                        current_target = str(current_key[1]).strip()
                    else:
                        current_target = ""
                    self.target_input.setText(current_target)
                    if hasattr(self, "dashboard_room_input"):
                        self.dashboard_room_input.setText(current_target)
            # Klassisch benutzt bewusst den bereits synchronisierten
            # target_input; dort funktioniert die Speicherung bereits korrekt.
            self._write_settings()

        self.layout_mode = mode

        # Jetzt erst die gerade gespeicherten Werte aus ~/.MeshCom/settings.ini
        # einlesen. Die neue Oberfläche startet damit mit dem zuvor aktiven Ziel.
        fresh_settings = load_settings()
        fresh_ip = fresh_settings.get("ip", "").strip().rstrip("/")
        fresh_target = fresh_settings.get("target", "").strip()
        fresh_callsign = self._normalize_callsign(fresh_settings.get("own_callsign", ""))
        fresh_lat = fresh_settings.get("own_lat", "").strip()
        fresh_lon = fresh_settings.get("own_lon", "").strip()
        if hasattr(self, "ip_input"):
            self.ip_input.setText(fresh_ip)
        if hasattr(self, "target_input"):
            self.target_input.setText(fresh_target)
        if hasattr(self, "own_callsign_input"):
            self.own_callsign_input.setText(fresh_callsign)
        if hasattr(self, "own_lat_input"):
            self.own_lat_input.setText(fresh_lat)
        if hasattr(self, "own_lon_input"):
            self.own_lon_input.setText(fresh_lon)
        self.own_callsign = fresh_callsign
        try:
            self.own_lat = float(fresh_lat.replace(",", ".")) if fresh_lat else None
            self.own_lon = float(fresh_lon.replace(",", ".")) if fresh_lon else None
        except (TypeError, ValueError):
            self.own_lat = self.own_lon = None

        if mode == "dashboard":
            # Beim Wechsel aus der klassischen Ansicht immer die aktuell
            # sichtbaren klassischen Eingabefelder in das Dashboard spiegeln.
            # Das Dashboard bleibt als Widget bestehen und kann daher sonst
            # veraltete GPS-/Rufzeichen-/Raum-Werte anzeigen.
            if self.dashboard_view is None:
                self.dashboard_view = self._build_dashboard_view()
                self.layout_stack.addWidget(self.dashboard_view)
            else:
                if hasattr(self, "dashboard_callsign_input"):
                    self.dashboard_callsign_input.setText(self.own_callsign_input.text())
                if hasattr(self, "dashboard_hotspot_input"):
                    self.dashboard_hotspot_input.setText(self.ip_input.text())
                if hasattr(self, "dashboard_room_input"):
                    self.dashboard_room_input.setText(self.target_input.text())
                if hasattr(self, "dashboard_lat_input"):
                    self.dashboard_lat_input.setText(self.own_lat_input.text())
                if hasattr(self, "dashboard_lon_input"):
                    self.dashboard_lon_input.setText(self.own_lon_input.text())
            self.layout_stack.setCurrentWidget(self.dashboard_view)
        else:
            if hasattr(self, "dashboard_callsign_input"):
                self.dashboard_callsign_input.setText(self.own_callsign_input.text())
            if hasattr(self, "dashboard_hotspot_input"):
                self.dashboard_hotspot_input.setText(self.ip_input.text())
            if hasattr(self, "dashboard_room_input"):
                self.dashboard_room_input.setText(self.target_input.text())
            if hasattr(self, "dashboard_lat_input"):
                self.dashboard_lat_input.setText(self.own_lat_input.text())
            if hasattr(self, "dashboard_lon_input"):
                self.dashboard_lon_input.setText(self.own_lon_input.text())
            # The classic page may have been initialized while Dashboard was
            # the saved layout. In that case map/worldwide are placeholders.
            # Materialize the real WebEngine views before showing the classic
            # page so both tabs work after switching layouts.
            self._ensure_classic_webviews()
            self.layout_stack.setCurrentWidget(self.classic_view)
            self._restore_classic_connection_controls()

            # Dashboard-WebEngines bleiben als Widgets erhalten, werden aber
            # im klassischen Modus aus dem Chromium-Lebenszyklus genommen.
            # Dadurch sinkt der RAM-Verbrauch, ohne Chat oder Verbindung zu
            # zerstören. Beim nächsten Dashboard-Wechsel werden sie reaktiviert.
            self._set_webengine_lifecycle(getattr(self, "dashboard_map_view", None), False)
            self._set_webengine_lifecycle(getattr(self, "dashboard_worldwide_view", None), False)

        if mode == "dashboard":
            # Die klassischen WebEngines sind im Dashboard unsichtbar und
            # werden deshalb ebenfalls in den ressourcenschonenden Zustand
            # versetzt. Die Tabs/Widgets selbst bleiben bestehen.
            self._set_webengine_lifecycle(getattr(self, "map_view", None), False)
            self._set_webengine_lifecycle(getattr(self, "worldwide_view", None), False)
            self._set_webengine_lifecycle(getattr(self, "dashboard_map_view", None), True)
            self._set_webengine_lifecycle(getattr(self, "dashboard_worldwide_view", None), True)

        # Ein Ansichtswechsel darf niemals den laufenden Verbindungszustand
        # verändern. self.connected ist die maßgebliche Quelle; die Labels
        # werden nur synchronisiert.
        if getattr(self, "connected", False):
            self._set_connection_status(True)
        else:
            self._sync_classic_connection_controls()
            self._dashboard_sync_header()

        if hasattr(self, "classic_layout_action"):
            self.classic_layout_action.setChecked(mode == "classic")
        if hasattr(self, "dashboard_layout_action"):
            self.dashboard_layout_action.setChecked(mode == "dashboard")
        # Beim echten Ansichtswechsel wurde die Quelloberfläche bereits VOR
        # dem Umschalten gespeichert. Ein zweites Speichern hier würde die frisch
        # geladene Zielauswahl wieder mit einem alten Feld überschreiben.
        if save and not switching:
            self._write_settings()

    def _restore_classic_connection_controls(self):
        """Keep the classic connection buttons permanently bound to the handlers."""
        if not hasattr(self, "connect_button"):
            return

        try:
            self.connect_button.clicked.disconnect()
        except (TypeError, RuntimeError):
            pass
        self.connect_button.clicked.connect(self.connect_mesh)

        if hasattr(self, "disconnect_button"):
            try:
                self.disconnect_button.clicked.disconnect()
            except (TypeError, RuntimeError):
                pass
            self.disconnect_button.clicked.connect(self.disconnect_mesh)

        online = bool(getattr(self, "connected", False))
        self.connect_button.setEnabled(not online)
        if hasattr(self, "disconnect_button"):
            self.disconnect_button.setEnabled(online)

    def _sync_classic_connection_controls(self):
        if not hasattr(self, "connect_button"):
            return
        try:
            online = bool(getattr(self, "connected", False))
            self.connect_button.setEnabled(not online)
            self.disconnect_button.setEnabled(online)
        except RuntimeError:
            pass

    def _set_layout_mode(self, mode):
        self._apply_layout_mode(mode, save=True)
        label = "Dashboard aktiviert" if mode == "dashboard" else "Klassische Ansicht aktiviert"
        self.status.setText(ui_text(label))

    def _dashboard_sync_header(self):
        if not hasattr(self, "dashboard_status_label"):
            return
        online = bool(getattr(self, "connection_online", False))
        self.dashboard_status_label.setText("🟢 ONLINE | verbunden" if online else "🔴 OFFLINE | keine Verbindung")

    def _dashboard_connect(self):
        """Use the exact same Connect button/signal path as the classic UI."""
        if hasattr(self, "dashboard_hotspot_input"):
            ip = self.dashboard_hotspot_input.text().strip()
            if ip:
                self.ip_input.setText(ip)
        # Do not alter the current room/private target here. Connecting only
        # needs the hotspot IP. Call the established connection method directly.
        self.connect_mesh()

    def _dashboard_disconnect(self):
        """Disconnect directly; do not depend on the hidden classic button."""
        self.disconnect_mesh()
        self._dashboard_sync_header()

    def _build_dashboard_view(self):
        """Build the dashboard as a real cockpit layout.

        The dashboard is only a presentation layer. Existing classic tabs,
        message handling, send logic, map data and the embedded Worldwide
        HTML page remain the sources of truth.
        """
        root = QWidget()
        root.setObjectName("DashboardRoot")
        root.setMinimumSize(1100, 620)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(6, 6, 6, 6)
        root_layout.setSpacing(6)

        # Dashboard-Kopf: bewusst komplett eigenständig. Die klassische
        # Oberfläche ist außerhalb des Dashboard-Widgets und wird beim
        # Umschalten ausgeblendet.
        dash_header = QFrame()
        dash_header.setObjectName("DashboardHeader")
        dash_header_container = QVBoxLayout(dash_header)
        dash_header_container.setContentsMargins(8, 6, 8, 6)
        dash_header_container.setSpacing(5)

        # Erste Reihe: Status, Rufzeichen, Verbindung und Hotspot-IP.
        # Das Rufzeichen ist bewusst direkt sichtbar und editierbar.
        dash_header_layout = QHBoxLayout()
        dash_header_layout.setContentsMargins(0, 0, 0, 0)
        dash_header_layout.setSpacing(5)
        dash_header_container.addLayout(dash_header_layout)

        antenna = QLabel()
        antenna.setFixedSize(64, 64)
        antenna_path = Path(__file__).resolve().parent.parent / "icons" / "antenna_blue.svg"
        antenna_icon = QIcon(str(antenna_path))
        if not antenna_icon.isNull():
            antenna.setPixmap(antenna_icon.pixmap(58, 58))
        antenna.setToolTip(ui_text("MeshCom-Guru"))
        dash_header_layout.addWidget(antenna, 0, Qt.AlignmentFlag.AlignVCenter)

        title_box = QVBoxLayout()
        title_label = QLabel(ui_text("MeshCom-Guru"))
        title_label.setObjectName("DashboardTitle")
        subtitle = QLabel(ui_text("Dashboard"))
        subtitle.setObjectName("DashboardSubtitle")
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle)
        title_box.setContentsMargins(0, 0, 0, 0)
        # Titelbereich kompakt halten, damit der Online-Status weiter links
        # stehen kann. Die Uhr bekommt einen eigenen festen Bereich und
        # wird dadurch beim Verschieben des Status nicht verdrängt.
        title_container = QWidget()
        title_container.setLayout(title_box)
        title_container.setFixedWidth(110)
        dash_header_layout.addWidget(title_container, 0)

        self.dashboard_status_label = QLabel(ui_text("🔴 OFFLINE | keine Verbindung"))
        self.dashboard_status_label.setObjectName("DashboardStatus")
        self.dashboard_status_label.setMinimumWidth(190)
        self.dashboard_status_label.setStyleSheet("font-size: 12pt; font-weight: 800;")
        dash_header_layout.addWidget(self.dashboard_status_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self.dashboard_clock_label = QLabel()
        self.dashboard_clock_label.setObjectName("DashboardClock")
        self.dashboard_clock_label.setMinimumWidth(150)
        self.dashboard_clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.dashboard_clock_label.setStyleSheet("font-size: 15pt; font-weight: 900;")
        dash_header_layout.addWidget(self.dashboard_clock_label, 0, Qt.AlignmentFlag.AlignVCenter)

        # Rufzeichen direkt in der ersten Reihe.
        dash_header_layout.addWidget(QLabel(ui_text("Rufzeichen:")))
        self.dashboard_callsign_input = QLineEdit(self.own_callsign_input.text())
        self.dashboard_callsign_input.setPlaceholderText(ui_text("eigenes Rufzeichen"))
        self.dashboard_callsign_input.setClearButtonEnabled(True)
        self.dashboard_callsign_input.setMaxLength(12)
        self.dashboard_callsign_input.setMinimumWidth(150)
        self.dashboard_callsign_input.setMaximumWidth(190)
        dash_header_layout.addWidget(self.dashboard_callsign_input)

        dashboard_connect = QPushButton(ui_text("🔗 Verbinden"))
        dashboard_connect.clicked.connect(self._dashboard_connect)
        self.dashboard_connect_button = dashboard_connect
        dash_header_layout.addWidget(dashboard_connect)
        dashboard_disconnect = QPushButton(ui_text("⚯ Trennen"))
        dashboard_disconnect.clicked.connect(self._dashboard_disconnect)
        self.dashboard_disconnect_button = dashboard_disconnect
        dashboard_disconnect.setEnabled(False)
        dash_header_layout.addWidget(dashboard_disconnect)

        dash_header_layout.addWidget(QLabel(ui_text("Hotspot IP:")))
        self.dashboard_hotspot_input = QLineEdit(self.ip_input.text())
        self.dashboard_hotspot_input.setPlaceholderText("http://192.168.x.x")
        self.dashboard_hotspot_input.setMinimumWidth(170)
        dash_header_layout.addWidget(self.dashboard_hotspot_input)
        dash_header_layout.addStretch(1)

        # Zweite Reihe: Raum/Ziel, Node-Info, GPS und zentraler Speichern-Knopf.
        dashboard_control_row = QHBoxLayout()
        dashboard_control_row.setContentsMargins(0, 0, 0, 0)
        dashboard_control_row.setSpacing(5)
        dash_header_container.addLayout(dashboard_control_row)

        dashboard_control_row.addWidget(QLabel(ui_text("Raum / Ziel:")))
        self.dashboard_room_input = QLineEdit(self.target_input.text())
        self.dashboard_room_input.setPlaceholderText(ui_text("Raum oder Ziel"))
        self.dashboard_room_input.setMinimumWidth(150)
        self.dashboard_room_input.setMaximumWidth(220)
        self.dashboard_room_input.editingFinished.connect(
            lambda: self.target_input.setText(self.dashboard_room_input.text().strip())
        )
        dashboard_control_row.addWidget(self.dashboard_room_input)

        dashboard_node_info = QPushButton(ui_text("ℹ Node Info"))
        dashboard_node_info.setToolTip(ui_text("Node Information des verbundenen MeshCom-WebService anzeigen"))
        dashboard_node_info.clicked.connect(self.open_node_info)
        dashboard_control_row.addWidget(dashboard_node_info)

        dashboard_control_row.addWidget(QLabel(ui_text("GPS Eingabe:")))
        self.dashboard_lat_input = QLineEdit(self.own_lat_input.text())
        self.dashboard_lat_input.setPlaceholderText(ui_text("51.93"))
        self.dashboard_lat_input.setMinimumWidth(82)
        self.dashboard_lat_input.setMaximumWidth(100)
        dashboard_control_row.addWidget(self.dashboard_lat_input)

        self.dashboard_lon_input = QLineEdit(self.own_lon_input.text())
        self.dashboard_lon_input.setPlaceholderText(ui_text("8.88"))
        self.dashboard_lon_input.setMinimumWidth(82)
        self.dashboard_lon_input.setMaximumWidth(100)
        dashboard_control_row.addWidget(self.dashboard_lon_input)

        dashboard_gps_save = QPushButton(ui_text("📍 GPS speichern"))
        dashboard_gps_save.clicked.connect(self._dashboard_save_coordinates)
        dashboard_control_row.addWidget(dashboard_gps_save)

        dashboard_settings_save = QPushButton(ui_text("⚙ Einstellungen speichern"))
        dashboard_settings_save.setToolTip(ui_text("Persönliche Einstellungen dauerhaft speichern"))
        dashboard_settings_save.clicked.connect(self.save_all_settings)
        self.dashboard_settings_save_button = dashboard_settings_save
        dashboard_control_row.addWidget(dashboard_settings_save, 1)

        # Wetter bleibt als eigene Zeile unter den beiden Kopfzeilen.
        root_layout.addWidget(dash_header)

        weather_box = QFrame()
        weather_box.setObjectName("DashboardWeather")
        weather_row = QHBoxLayout(weather_box)
        weather_row.setContentsMargins(8, 3, 8, 3)
        weather_row.setSpacing(5)

        weather_row.addWidget(QLabel(ui_text("🌤 Wetter")))
        self.dashboard_weather_city = QLineEdit(self.weather_city_input.text())
        self.dashboard_weather_city.setPlaceholderText(ui_text("Stadt"))
        self.dashboard_weather_city.setMinimumWidth(105)
        self.dashboard_weather_city.setMaximumWidth(145)
        self.dashboard_weather_city.editingFinished.connect(
            lambda: self.weather_city_input.setText(self.dashboard_weather_city.text().strip())
        )
        weather_row.addWidget(self.dashboard_weather_city)

        self.dashboard_weather_values = QLabel(ui_text("Warte auf WX-Information …"))
        self.dashboard_weather_values.setWordWrap(False)
        weather_row.addWidget(self.dashboard_weather_values, 1)

        dash_weather_refresh = QPushButton(ui_text("⟳ Wetter aktualisieren"))
        dash_weather_refresh.clicked.connect(self._dashboard_refresh_weather)
        weather_row.addWidget(dash_weather_refresh)

        dash_weather_send = QPushButton(ui_text("➤ Wetter senden"))
        dash_weather_send.clicked.connect(self._dashboard_send_weather)
        weather_row.addWidget(dash_weather_send)

        root_layout.addWidget(weather_box)

        # Keine zweite Tab-Leiste im Dashboard: Alle wichtigen Bereiche sind
        # bereits gleichzeitig sichtbar (Räume/Private links, Chat Mitte,
        # Karte/Weltweit rechts, Monitor/MH/Statistik unten).

        # Main area: fixed initial widths matching the supplied reference.
        # Sidebar stays unchanged; chat gets the space taken from the right column.
        main_split = QSplitter(Qt.Orientation.Horizontal)
        main_split.setChildrenCollapsible(False)
        main_split.setHandleWidth(5)

        sidebar = QFrame()
        sidebar.setObjectName("DashboardSidebar")
        self.dashboard_sidebar = sidebar
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(8, 8, 8, 8)
        side_layout.setSpacing(5)

        # Räume stehen im Dashboard ganz oben und sind wirklich verwaltbar.
        # Der Plus-Button öffnet die vorhandenen fünf Raumfilter-Felder der
        # klassischen Ansicht; dadurch werden keine parallelen Raumdaten
        # eingeführt und die bestehende Logik bleibt die einzige Datenquelle.
        room_head = QHBoxLayout()
        title = QLabel(ui_text("📻 Räume"))
        title.setStyleSheet("font-size: 12pt; font-weight: 700;")
        title.setFixedWidth(78)
        room_head.setSpacing(5)
        room_head.addWidget(title)
        add_room = QPushButton(ui_text("＋ Raum hinzufügen"))
        add_room.setFixedWidth(155)
        add_room.setMinimumHeight(30)
        add_room.setToolTip(ui_text("Räume hinzufügen / bearbeiten"))
        add_room.clicked.connect(self._dashboard_manage_rooms)
        room_head.addWidget(add_room)
        side_layout.addLayout(room_head)

        # Raumfilter im Dashboard direkt sichtbar und bedienbar.
        self.dashboard_filter_check = QCheckBox(ui_text("☑ Raumfilter aktiv"))
        self.dashboard_filter_check.setChecked(self.filter_enabled.isChecked())
        self.dashboard_filter_check.toggled.connect(self._dashboard_filter_toggled)
        side_layout.addWidget(self.dashboard_filter_check)

        self.dashboard_room_buttons = []
        self._dashboard_rebuild_room_buttons(side_layout)

        self.dashboard_room_chat_buttons = []
        private_title = QLabel(ui_text("👤 Private Chats"))
        private_title.setStyleSheet("font-size: 11pt; font-weight: 700;")
        side_layout.addWidget(private_title)

        # Private Chats bekommen einen eigenen Scrollbereich. So können viele
        # private Unterhaltungen nicht mehr die Karte/Worldwide bzw. den
        # unteren Monitor/MH/Statistik-Bereich nach unten drücken. Qt zeigt
        # die vertikale Scrollleiste nur bei Bedarf an.
        self.dashboard_private_scroll = QScrollArea()
        self.dashboard_private_scroll.setWidgetResizable(True)
        self.dashboard_private_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.dashboard_private_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.dashboard_private_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.dashboard_private_scroll_content = QWidget()
        self.dashboard_private_scroll_layout = QVBoxLayout(
            self.dashboard_private_scroll_content
        )
        self.dashboard_private_scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.dashboard_private_scroll_layout.setSpacing(5)
        self.dashboard_private_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.dashboard_private_scroll.setWidget(self.dashboard_private_scroll_content)
        side_layout.addWidget(self.dashboard_private_scroll, 1)
        self._dashboard_rebuild_private_buttons(side_layout)

        # Kein zusätzlicher Stretch unterhalb der privaten Chats: Der
        # Scrollbereich erhält den verfügbaren Platz und scrollt bei Bedarf.
        main_split.addWidget(sidebar)

        # Real chat renderer. It receives the same HTML/bubble data as the
        # classic chat, so the existing bubble design is not redesigned here.
        chat_frame = QFrame()
        chat_frame.setObjectName("DashboardPanel")
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(8, 8, 8, 8)
        chat_layout.setSpacing(5)
        chat_title = QLabel(ui_text("💬 Alle – Nachrichten aus deinen Räumen"))
        chat_title.setStyleSheet("font-size: 12pt; font-weight: 700;")
        self.dashboard_chat_title = chat_title
        chat_layout.addWidget(chat_title)

        self.dashboard_chat_view = ChatView()
        self.dashboard_chat_view.set_chat_colors(
            self.chat_background, self.chat_text_color, self.chat_link_color
        )
        # Dashboard verwendet exakt dieselbe ChatView-Linkverarbeitung wie
        # die klassische Ansicht. Rufzeichen-Links werden dadurch intern an
        # open_private_chat weitergereicht; http/https-Links bleiben bei der
        # gemeinsamen ChatView-Verarbeitung und öffnen den Systembrowser.
        self.dashboard_chat_view.callsignActionClicked.connect(self._handle_callsign_action)
        self._all_chat_views.append(self.dashboard_chat_view)
        chat_layout.addWidget(self.dashboard_chat_view, 1)

        dash_message = QHBoxLayout()
        dash_message.setSpacing(5)
        self.dashboard_message_input = QLineEdit()
        self.dashboard_message_input.setPlaceholderText(ui_text("Nachricht eingeben …"))
        self.dashboard_message_input.setMaxLength(149)
        self.dashboard_message_input.returnPressed.connect(self._dashboard_send)
        dash_message.addWidget(self.dashboard_message_input, 1)
        dashboard_quick = QPushButton(ui_text("⚡ Schnelltexte"))
        dashboard_quick.setToolTip(ui_text("Schnelltext auswählen oder bearbeiten"))
        dashboard_quick.clicked.connect(self._open_quick_texts)
        dash_message.addWidget(dashboard_quick)
        self.dashboard_emoji_button = QPushButton("😊")
        self.dashboard_emoji_button.setFixedWidth(42)
        self.dashboard_emoji_button.clicked.connect(self._dashboard_insert_emoji)
        dash_message.addWidget(self.dashboard_emoji_button)

        # Dashboard-Zeichenzähler für das Nachrichtenfeld.
        self.dashboard_message_counter = QLabel("0/149")
        self.dashboard_message_counter.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.dashboard_message_counter.setMinimumWidth(48)
        self.dashboard_message_counter.setToolTip(ui_text("Maximal 149 Zeichen"))
        self.dashboard_message_input.textChanged.connect(
            self._update_dashboard_message_counter
        )
        dash_message.addWidget(self.dashboard_message_counter)

        chat_layout.addLayout(dash_message)
        main_split.addWidget(chat_frame)

        # Right column: map and the real embedded Worldwide HTML page.
        right_split = QSplitter(Qt.Orientation.Vertical)
        right_split.setChildrenCollapsible(False)
        right_split.setHandleWidth(5)

        map_frame = QFrame()
        map_frame.setObjectName("DashboardPanel")
        map_frame.setMinimumHeight(260)
        map_layout = QVBoxLayout(map_frame)
        map_layout.setContentsMargins(8, 8, 8, 8)
        map_layout.setSpacing(4)
        map_title = QLabel(ui_text("📍 Karte – Stationen in deiner Umgebung"))
        map_title.setStyleSheet("font-size: 12pt; font-weight: 700;")
        map_layout.addWidget(map_title)
        self.dashboard_map_view = QWebEngineView() if QWebEngineView is not None else QLabel("Karte benötigt PySide6-WebEngine.")
        if QWebEngineView is not None:
            self.dashboard_map_ready = False
            self.dashboard_map_pending = []
            self.dashboard_map_view.loadFinished.connect(self._dashboard_map_load_finished)
            self.dashboard_map_view.setHtml(self._map_html([]), QUrl("https://meshcom-guru.local/dashboard/"))
        map_layout.addWidget(self.dashboard_map_view, 1)
        right_split.addWidget(map_frame)

        ww_frame = QFrame()
        ww_frame.setObjectName("DashboardPanel")
        # Keep enough space for the real WebKit page immediately after startup.
        # Without a minimum size the native GTK/X11 child can collapse until
        # the user moves the splitter manually.
        ww_frame.setMinimumHeight(230)
        ww_layout = QVBoxLayout(ww_frame)
        ww_layout.setContentsMargins(8, 8, 8, 8)
        ww_layout.setSpacing(4)
        ww_title = QLabel("🌐 Weltweit – MeshCom Activity (integrierte HTML-Seite)")
        ww_title.setStyleSheet("font-size: 12pt; font-weight: 700;")
        ww_layout.addWidget(ww_title)
        # Worldwide deliberately uses WebKitGTK. The OSM map above remains
        # the existing QtWebEngine map and is not changed.
        if platform.system().lower() == "linux" and GtkWebKitWorldwide is not None and GTK_WEBKIT_AVAILABLE:
            self.dashboard_worldwide_view = GtkWebKitWorldwide("https://meshcom.oevsv.at/#")
        elif QWebEngineView is not None:
            self.dashboard_worldwide_view = QWebEngineView()
            self.dashboard_worldwide_view.loadFinished.connect(self._dashboard_worldwide_load_finished)
            self.dashboard_worldwide_view.renderProcessTerminated.connect(self._worldwide_render_terminated)
            self.dashboard_worldwide_view.setUrl(QUrl("https://meshcom.oevsv.at/#"))
        else:
            self.dashboard_worldwide_view = QLabel(
                "Weltweit benötigt QtWebEngine.\nBitte requirements.txt erneut installieren."
            )
        self.dashboard_worldwide_view.setMinimumSize(100, 190)
        self.dashboard_worldwide_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        ww_layout.addWidget(self.dashboard_worldwide_view, 1)
        right_split.addWidget(ww_frame)
        right_split.setStretchFactor(0, 55)
        right_split.setStretchFactor(1, 45)
        # Explicit initial sizes are applied after the dashboard has received
        # its real height; this prevents Worldwide from starting almost flat.
        def _initial_right_split_sizes(rs=right_split):
            h = rs.height()
            if h > 0:
                handle = rs.handleWidth()
                available = max(1, h - handle)
                ww_h = max(230, int(available * 0.42))
                map_h = max(260, available - ww_h)
                if map_h + ww_h > available:
                    map_h = max(1, available - ww_h)
                rs.setSizes([map_h, ww_h])
        QTimer.singleShot(0, _initial_right_split_sizes)
        QTimer.singleShot(250, _initial_right_split_sizes)
        QTimer.singleShot(750, _initial_right_split_sizes)
        main_split.addWidget(right_split)

        # Fixed initial layout matching the reference screenshot:
        # rooms ≈ 220 px, chat ≈ 525 px, right column ≈ 635 px.
        # Do not use stretch factors here: they would undo the intended split.
        main_split.setSizes([220, 482, 678])
        root_layout.addWidget(main_split, 1)

        # Bottom information strip: Monitor 50 %, MH 30 %, Statistics 20 %.
        bottom_split = QSplitter(Qt.Orientation.Horizontal)
        bottom_split.setChildrenCollapsible(False)
        bottom_split.setHandleWidth(5)

        self.dashboard_monitor_table = QTableWidget(0, 7)
        self.dashboard_monitor_table.setHorizontalHeaderLabels([
            ui_text("Zeit"), ui_text("Typ"), ui_text("Rufzeichen"), ui_text("Ziel"),
            "RSSI", "SNR", ui_text("Information")
        ])
        self.dashboard_monitor_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.dashboard_monitor_table.setWordWrap(True)
        self.dashboard_monitor_table.verticalHeader().setVisible(False)
        # Do not squeeze the Information column into a tiny sliver.  If the
        # dashboard panel is narrower, the user can scroll horizontally.
        self.dashboard_monitor_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        dashboard_monitor_header = self.dashboard_monitor_table.horizontalHeader()
        dashboard_monitor_header.setStretchLastSection(False)
        for col in range(7):
            dashboard_monitor_header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        for col, width in {0: 70, 1: 50, 2: 108, 3: 108, 4: 55, 5: 55, 6: 420}.items():
            self.dashboard_monitor_table.setColumnWidth(col, width)
        # Dashboard-Monitor: dieselben Bedienfunktionen wie im klassischen Monitor,
        # aber ausschließlich in der vorhandenen Monitor-Fläche. Die übrigen
        # Dashboard-Panels und deren Größen/Positionen bleiben unverändert.
        monitor_panel = QFrame()
        monitor_panel.setObjectName("DashboardPanel")
        monitor_panel_layout = QVBoxLayout(monitor_panel)
        monitor_panel_layout.setContentsMargins(6, 6, 6, 6)
        monitor_panel_layout.setSpacing(3)
        monitor_panel_layout.addWidget(QLabel(ui_text("📡 Monitor – Live")))
        dashboard_monitor_toolbar = QHBoxLayout()
        dashboard_monitor_toolbar.setSpacing(4)

        self.dashboard_monitor_pause_button = QPushButton(ui_text("⏸ Pause"))
        self.dashboard_monitor_pause_button.setFixedWidth(120)
        self.dashboard_monitor_pause_button.clicked.connect(self._toggle_monitor_pause)
        dashboard_monitor_toolbar.addWidget(self.dashboard_monitor_pause_button)

        self.dashboard_monitor_clear_button = QPushButton(ui_text("Leeren"))
        self.dashboard_monitor_clear_button.setFixedWidth(108)
        self.dashboard_monitor_clear_button.clicked.connect(self._clear_monitor)
        dashboard_monitor_toolbar.addWidget(self.dashboard_monitor_clear_button)

        dashboard_monitor_toolbar.addWidget(QLabel(ui_text("Filter:")))
        self.dashboard_monitor_filter_combo = QComboBox()
        self.dashboard_monitor_filter_combo.addItem(tr("Alle"), "ALLE")
        self.dashboard_monitor_filter_combo.addItems(["MSG", "POS", "TEL", "ACK"])
        self.dashboard_monitor_filter_combo.setCurrentIndex(max(0, self.dashboard_monitor_filter_combo.findData(self.monitor_filter)))
        self.dashboard_monitor_filter_combo.setFixedWidth(70)
        self.dashboard_monitor_filter_combo.currentIndexChanged.connect(self._set_monitor_filter_index)
        dashboard_monitor_toolbar.addWidget(self.dashboard_monitor_filter_combo)

        self.dashboard_monitor_search_edit = QLineEdit()
        self.dashboard_monitor_search_edit.setPlaceholderText(ui_text("Suchen …"))
        self.dashboard_monitor_search_edit.setMinimumWidth(90)
        self.dashboard_monitor_search_edit.setMaximumWidth(150)
        self.dashboard_monitor_search_edit.textChanged.connect(self._set_monitor_search)
        dashboard_monitor_toolbar.addWidget(self.dashboard_monitor_search_edit)

        self.dashboard_monitor_autoscroll_check = QCheckBox(ui_text("Auto-Scroll"))
        self.dashboard_monitor_autoscroll_check.setChecked(self.monitor_autoscroll)
        self.dashboard_monitor_autoscroll_check.toggled.connect(self._toggle_monitor_autoscroll)
        dashboard_monitor_toolbar.addWidget(self.dashboard_monitor_autoscroll_check)
        dashboard_monitor_toolbar.addStretch(1)
        self.dashboard_monitor_count_label = QLabel(ui_text("0 angezeigt · 0 gespeichert"))
        dashboard_monitor_toolbar.addWidget(self.dashboard_monitor_count_label)
        monitor_panel_layout.addLayout(dashboard_monitor_toolbar)
        monitor_panel_layout.addWidget(self.dashboard_monitor_table, 1)
        bottom_split.addWidget(monitor_panel)

        self.dashboard_mh_table = QTableWidget(0, 4)
        self.dashboard_mh_table.setHorizontalHeaderLabels([
            ui_text("Rufzeichen"), ui_text("Entfernung"), "RSSI", "SNR"
        ])
        self.dashboard_mh_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.dashboard_mh_table.verticalHeader().setVisible(False)
        # Four compact columns always fit into the MH panel. There is no useful
        # horizontal overflow here, so do not show a second scroll bar.
        self.dashboard_mh_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        mh_header = self.dashboard_mh_table.horizontalHeader()
        mh_header.setStretchLastSection(True)
        mh_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        mh_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        mh_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        mh_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.dashboard_mh_table.setColumnWidth(1, 82)
        self.dashboard_mh_table.setColumnWidth(2, 78)
        self.dashboard_mh_table.setColumnWidth(3, 58)
        # MH-Leiste bleibt in derselben vorhandenen Fläche; nur der zusätzliche
        # Leeren-Button wird neben dem Titel eingeblendet.
        mh_panel = QFrame()
        mh_panel.setObjectName("DashboardPanel")
        mh_panel_layout = QVBoxLayout(mh_panel)
        mh_panel_layout.setContentsMargins(6, 6, 6, 6)
        mh_panel_layout.setSpacing(3)
        mh_title_row = QHBoxLayout()
        mh_title_row.setSpacing(4)
        mh_title = QLabel(ui_text("📋 Stations / MH – Letzte Stationen"))
        mh_title.setStyleSheet("font-size: 11pt; font-weight: 700;")
        mh_title_row.addWidget(mh_title)
        mh_title_row.addStretch(1)
        self.dashboard_mh_clear_button = QPushButton(ui_text("Leeren"))
        self.dashboard_mh_clear_button.setFixedWidth(70)
        self.dashboard_mh_clear_button.clicked.connect(self._clear_mh)
        mh_title_row.addWidget(self.dashboard_mh_clear_button)
        mh_panel_layout.addLayout(mh_title_row)
        mh_panel_layout.addWidget(self.dashboard_mh_table, 1)
        bottom_split.addWidget(mh_panel)

        stats_panel = QFrame()
        stats_panel.setObjectName("DashboardPanel")
        stats_layout = QVBoxLayout(stats_panel)
        stats_layout.setContentsMargins(8, 8, 8, 8)
        stats_title = QLabel(ui_text("📊 Statistik"))
        stats_title.setStyleSheet("font-size: 12pt; font-weight: 700;")
        stats_layout.addWidget(stats_title)
        # Statistik im Dashboard bekommt einen eigenen Scrollbereich.
        # So bleiben alle Sitzungs- und Raumzeilen auch im normalen Fenstermodus
        # erreichbar, ohne die feste Höhe des unteren Bereichs zu verändern.
        statistics_scroll = QScrollArea()
        statistics_scroll.setWidgetResizable(True)
        statistics_scroll.setFrameShape(QFrame.Shape.NoFrame)
        statistics_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        statistics_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        statistics_content = QWidget()
        statistics_content_layout = QVBoxLayout(statistics_content)
        statistics_content_layout.setContentsMargins(0, 0, 0, 0)
        statistics_content_layout.setSpacing(0)

        self.dashboard_statistics_label = QLabel(ui_text("Noch keine Sitzungsdaten"))
        self.dashboard_statistics_label.setWordWrap(True)
        self.dashboard_statistics_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        statistics_content_layout.addWidget(self.dashboard_statistics_label)
        statistics_content_layout.addStretch(1)
        statistics_scroll.setWidget(statistics_content)
        stats_layout.addWidget(statistics_scroll, 1)
        bottom_split.addWidget(stats_panel)
        bottom_split.setMinimumHeight(155)
        bottom_split.setFixedHeight(185)
        # The Monitor gets more room so its Information column can be read.
        # Stations / MH is intentionally a little narrower.
        bottom_split.setStretchFactor(0, 50)
        bottom_split.setStretchFactor(1, 30)
        bottom_split.setStretchFactor(2, 20)
        bottom_split.setSizes([620, 320, 250])
        root_layout.addWidget(bottom_split, 0)
        return root

    def _dashboard_update_chat_button(self, key, button=None):
        """Update unread/active appearance of one dashboard room/private entry."""
        if button is None:
            # Die sichtbaren Dashboard-Räume liegen in dashboard_room_buttons.
            # Private Chats liegen in dashboard_private_buttons.
            # "Alle" ist ein eigener Button und keine Raum-Zeile.
            for collection_name in (
                "dashboard_room_buttons",
                "dashboard_room_chat_buttons",
                "dashboard_private_buttons",
            ):
                for name, candidate in getattr(self, collection_name, []):
                    candidate_key = (
                        "private", str(name)
                    ) if collection_name == "dashboard_private_buttons" else (
                        "room", str(name)
                    )
                    if candidate_key == key:
                        button = candidate
                        break
                if button is not None:
                    break

            # "Alle" hat keine Liste mit (name, button), sondern eine
            # einzelne Referenz. Genau wie in der klassischen Ansicht soll
            # dieser Eintrag ebenfalls rot werden, wenn er ungelesen ist.
            if button is None and key == ("all", "all"):
                button = getattr(self, "dashboard_all_button", None)

        if button is None:
            return
        active = getattr(self, "dashboard_current_key", None) == key
        unread = key in getattr(self, "unread", set())
        if active:
            button.setStyleSheet("font-weight: 700; border: 1px solid #4aa3ff;")
        elif unread:
            button.setStyleSheet("font-weight: 700; color: #ff4d4d; border: 1px solid #ff4d4d;")
        else:
            button.setStyleSheet("")

    def _dashboard_rebuild_private_buttons(self, side_layout):
        """Keep the dashboard private-chat list synchronized with real private tabs."""
        private_layout = getattr(
            self, "dashboard_private_scroll_layout", side_layout
        )

        # Remove complete private-chat rows so the X buttons cannot accumulate.
        while private_layout.count():
            item = private_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            child_layout = item.layout()
            if child_layout is not None:
                while child_layout.count():
                    child_item = child_layout.takeAt(0)
                    child_widget = child_item.widget()
                    if child_widget is not None:
                        child_widget.setParent(None)
                        child_widget.deleteLater()

        self.dashboard_private_buttons = []
        self.dashboard_private_empty_label = None

        private_keys = [key for key in self.tab_keys if key[0] == "private"]
        private_keys.sort(key=lambda key: str(key[1]).upper())

        if private_keys:
            for key in private_keys:
                row = QWidget()
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(3)

                b = QPushButton(str(key[1]))
                b.setMinimumHeight(30)
                b.setProperty("dashboardNav", True)
                b.clicked.connect(
                    lambda _=False, k=key: self._dashboard_select_chat(k)
                )

                close_btn = QPushButton("✕")
                close_btn.setFixedSize(30, 30)
                close_btn.setToolTip(ui_text("Privatchat schließen"))
                close_btn.setStyleSheet(
                    "QPushButton { color: #ff4d4d; font-size: 17px; font-weight: 900; "
                    "border: 1px solid #6b7280; border-radius: 5px; padding: 0; "
                    "background: #202938; } "
                    "QPushButton:hover { color: #ffffff; border-color: #ff4d4d; "
                    "background: #3a2630; }"
                )
                close_btn.clicked.connect(
                    lambda _=False, k=key: self._dashboard_close_private_chat(k)
                )

                row_layout.addWidget(b, 1)
                row_layout.addWidget(close_btn)
                private_layout.addWidget(row)
                self.dashboard_private_buttons.append((str(key[1]), b))
                self._dashboard_update_chat_button(key, b)
        else:
            empty = QLabel(ui_text("Noch keine privaten Chats"))
            empty.setObjectName("DashboardNoPrivateChats")
            private_layout.addWidget(empty)
            self.dashboard_private_empty_label = empty

    def _dashboard_close_private_chat(self, key):
        """Close a private chat from the Dashboard X button."""
        index = self.tab_keys.get(key)
        if index is not None:
            self._close_tab(index)
            if (
                hasattr(self, "dashboard_current_key")
                and self.dashboard_current_key == key
            ):
                self.dashboard_current_key = ("all", "all")
                all_index = self.tab_keys.get(("all", "all"))
                if all_index is not None:
                    self.tabs.setCurrentIndex(all_index)
        self._dashboard_rebuild_private_buttons(self.dashboard_sidebar.layout())

    def _dashboard_rebuild_room_buttons(self, side_layout):
        """Build one clean dashboard room list from the saved room settings."""
        # Remove every widget created by the old room-list implementations.
        # This is deliberately done from both collections so a rebuild cannot
        # leave a second copy of the same rooms behind.
        for collection_name in ("dashboard_room_buttons", "dashboard_room_chat_buttons"):
            for _, widget in getattr(self, collection_name, []):
                try:
                    side_layout.removeWidget(widget)
                except Exception:
                    pass
                widget.setParent(None)
                widget.deleteLater()
            setattr(self, collection_name, [])

        old_all = getattr(self, "dashboard_all_button", None)
        if old_all is not None:
            try:
                side_layout.removeWidget(old_all)
            except Exception:
                pass
            old_all.setParent(None)
            old_all.deleteLater()
            self.dashboard_all_button = None

        rooms = []
        for room in self._rooms():
            room = str(room).strip()
            if room and room not in rooms:
                rooms.append(room)
        rooms = rooms[:5]

        # The filter checkbox stays above the room list.  Room selection and
        # filter activation are intentionally independent.
        if hasattr(self, "dashboard_filter_check"):
            insert_at = side_layout.indexOf(self.dashboard_filter_check) + 1
        else:
            insert_at = 0

        # "Alle" steht bewusst direkt unter dem Raumfilter und damit vor
        # den einzelnen Räumen. Es bleibt ein eigener Chat-Eintrag und ist
        # niemals Teil der gespeicherten Raumliste.
        all_key = ("all", "all")
        all_button = QPushButton("💬 Alle")
        all_button.setMinimumHeight(30)
        all_button.setProperty("dashboardNav", True)
        all_button.setProperty("chatKey", all_key)
        all_button.clicked.connect(
            lambda _=False, k=all_key: self._dashboard_select_chat(k)
        )
        side_layout.insertWidget(insert_at, all_button)
        self.dashboard_all_button = all_button
        self._dashboard_update_chat_button(all_key, all_button)
        insert_at += 1

        self.dashboard_room_buttons = []
        for room in rooms:
            key = ("room", room)
            button = QPushButton(f"#  {room}")
            button.setMinimumHeight(30)
            button.setProperty("dashboardNav", True)
            button.setProperty("chatKey", key)
            button.clicked.connect(
                lambda _=False, k=key: self._dashboard_select_chat(k)
            )
            side_layout.insertWidget(insert_at, button)
            insert_at += 1
            self.dashboard_room_buttons.append((room, button))
            self._dashboard_update_chat_button(key, button)

        if hasattr(self, "dashboard_filter_check"):
            self.dashboard_filter_check.blockSignals(True)
            self.dashboard_filter_check.setChecked(self.filter_enabled.isChecked())
            self.dashboard_filter_check.blockSignals(False)

    def _dashboard_filter_toggled(self, enabled):
        self.filter_enabled.blockSignals(True)
        self.filter_enabled.setChecked(bool(enabled))
        self.filter_enabled.blockSignals(False)
        self._filter_toggled(bool(enabled))

    def _dashboard_manage_rooms(self):
        """Edit the same five room filters used by the classic UI."""
        dialog = QDialog(self)
        dialog.setWindowTitle(ui_text("Räume verwalten"))
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(ui_text("Bis zu 5 Räume eingeben. Die Räume werden auch im klassischen Filter verwendet.")))
        fields = []
        for i in range(5):
            row = QHBoxLayout()
            row.addWidget(QLabel(ui_text(f"Raum {i + 1}:")))
            field = QLineEdit(self.filter_inputs[i].text().strip())
            field.setMaxLength(10)
            row.addWidget(field, 1)
            layout.addLayout(row)
            fields.append(field)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        # Erst die Felder übernehmen, dann die bestehende Speicherfunktion
        # verwenden. Anschließend wird die Dashboard-Auswahl unmittelbar aus
        # den tatsächlich sichtbaren Feldern neu aufgebaut.
        for i, field in enumerate(fields):
            self.filter_inputs[i].setText(field.text().strip())
        # Beim Speichern von Räumen den bisherigen Filterzustand beibehalten.
        self.save_filter_settings()
        if hasattr(self, "dashboard_sidebar"):
            self._dashboard_rebuild_room_buttons(self.dashboard_sidebar.layout())

    def _dashboard_refresh_weather(self):
        if hasattr(self, "dashboard_weather_city"):
            self.weather_city_input.setText(self.dashboard_weather_city.text().strip())
        self._refresh_weather()

    def _dashboard_send_weather(self):
        if hasattr(self, "dashboard_weather_city"):
            self.weather_city_input.setText(self.dashboard_weather_city.text().strip())
        self._send_weather()

    def _dashboard_table_panel(self, title, table):
        frame = QFrame()
        frame.setObjectName("DashboardPanel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 6, 6, 6)
        label = QLabel(title)
        label.setStyleSheet("font-size: 11pt; font-weight: 700;")
        layout.addWidget(label)
        layout.addWidget(table, 1)
        return frame

    def _dashboard_focus(self, widget):
        if widget is not None:
            widget.setFocus()

    def _dashboard_select_chat(self, key):
        index = self.tab_keys.get(key)
        if index is None:
            if key[0] == "room":
                self._ensure_tab(key, self._room_tab_title(key[1]))
                index = self.tab_keys.get(key)
            elif key[0] == "all":
                self._ensure_tab(key, "Alle")
                index = self.tab_keys.get(key)
            else:
                return
        self.tabs.setCurrentIndex(index)

        # Die Auswahl im Dashboard muss dieselbe Zielauswahl wie in der
        # klassischen Ansicht benutzen. Dadurch sendet der vorhandene
        # send()-Code weiterhin exakt an den ausgewählten Raum.
        if key[0] == "room":
            # Raum auswählen und Filter aktivieren bleiben getrennt.
            self.target_input.setText(str(key[1]))
            if hasattr(self, "dashboard_room_input"):
                self.dashboard_room_input.setText(str(key[1]))
        elif key[0] == "private":
            self.target_input.setText(str(key[1]))
            if hasattr(self, "dashboard_room_input"):
                self.dashboard_room_input.setText(str(key[1]))
        elif key[0] == "all":
            # "Alle" hat bewusst kein Sendeziel. Beim Wechsel aus einem
            # Raum darf der zuletzt gewählte Raum deshalb nicht im Feld
            # "Raum / Ziel" stehen bleiben. Dashboard und klassische Ansicht
            # müssen sich hier identisch verhalten.
            self.target_input.clear()
            if hasattr(self, "dashboard_room_input"):
                self.dashboard_room_input.clear()

        self.dashboard_current_key = key
        self.unread.discard(key)
        self._set_tab_normal(key)
        self._dashboard_update_chat_button(key)
        self._dashboard_set_chat_from_key(key)

    def _dashboard_set_chat_from_key(self, key):
        index = self.tab_keys.get(key)
        if index is None or not hasattr(self, "dashboard_chat_view"):
            return
        view = self.tabs.widget(index)
        if not isinstance(view, ChatView):
            return
        if key[0] in ("room", "private"):
            # Room/private tabs use the real bubble widgets.  Reuse their exact
            # bubble data instead of copying the hidden QTextBrowser, which is
            # empty while a tab is in bubble mode.
            self.dashboard_chat_view.set_bubbles(getattr(view, "_bubble_items", []))
            if key[0] == "room":
                title = ui_text("💬 Raum #{key[1]}").replace("{key[1]}", str(key[1]))
            else:
                title = ui_text("👤 Privat – {key[1]}").replace("{key[1]}", str(key[1]))
            if hasattr(self, "dashboard_chat_title"):
                self.dashboard_chat_title.setText(title)
        else:
            self.dashboard_chat_view.set_all_html(
                self._render_blocks(self._filter_blocks(list(self.message_cache.values())))
            )
            if hasattr(self, "dashboard_chat_title"):
                self.dashboard_chat_title.setText(ui_text("💬 Alle – Nachrichten aus deinen Räumen"))

    def _dashboard_send(self):
        text = self.dashboard_message_input.text().strip()
        if not text:
            return
        self.message_input.setText(text)
        self.send()
        self.dashboard_message_input.clear()

    def _dashboard_insert_emoji(self):
        # Im Dashboard immer das Dashboard-Feld als Ziel verwenden.
        # Dadurch kann kein Inhalt aus dem klassischen Nachrichtenfeld
        # (z. B. ein zuvor verwendetes Emoji) übernommen werden.
        if hasattr(self, "dashboard_message_input"):
            self.dashboard_message_input.setFocus()
        self._toggle_emoji_picker()

    def _use_dashboard_quick_text(self, text):
        self.message_input.setText(str(text))
        self.dashboard_message_input.setText(str(text))

    def _dashboard_save_coordinates(self):
        """Save the own station coordinates entered directly in the dashboard."""
        try:
            lat_text = self.dashboard_lat_input.text().strip().replace(",", ".")
            lon_text = self.dashboard_lon_input.text().strip().replace(",", ".")
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

        self.own_lat, self.own_lon = lat, lon
        self.own_lat_input.setText("" if lat is None else str(lat))
        self.own_lon_input.setText("" if lon is None else str(lon))
        self._write_settings()
        self._update_map()
        self.status.setText(ui_text("Eigene GPS-Koordinaten gespeichert"))

    def _dashboard_map_load_finished(self, ok):
        self.dashboard_map_ready = bool(ok)
        if self.dashboard_map_ready:
            self._push_dashboard_map_stations(self.dashboard_map_pending)

    def _push_dashboard_map_stations(self, stations):
        if QWebEngineView is None or not hasattr(self, "dashboard_map_view"):
            return
        self.dashboard_map_pending = list(stations or [])
        if not self.dashboard_map_ready:
            return
        station_json = json.dumps(self.dashboard_map_pending, ensure_ascii=False)
        self.dashboard_map_view.page().runJavaScript(
            f"if (typeof window.updateStations === 'function') window.updateStations({station_json});"
        )

    def _dashboard_worldwide_load_finished(self, ok):
        self._worldwide_health_pending = False
        if not ok or QWebEngineView is None:
            return
        self._worldwide_health_last_ok = time.monotonic()
        self.dashboard_worldwide_view.page().runJavaScript(
            """(function(){const els=Array.from(document.querySelectorAll('a,button,[role=button],input'));const el=els.find(e=>((e.innerText||e.textContent||e.value||e.title||'')+'').trim().toUpperCase()==='ACTIVITY');if(el){el.click();return true;}const loose=els.find(e=>((e.innerText||e.textContent||e.value||e.title||'')+'').trim().toUpperCase().includes('ACTIVITY'));if(loose){loose.click();return true;}return false;})();"""
        )

    def _dashboard_worldwide_render_terminated(self, termination_status, exit_code):
        """Recover automatically if Chromium's Worldwide renderer dies."""
        self._worldwide_health_pending = False
        self._worldwide_reload_pending = True
        QTimer.singleShot(1000, self._reload_dashboard_worldwide)

    def _worldwide_render_terminated(self, termination_status, exit_code):
        """Recover automatically if the classic Worldwide renderer dies."""
        self._worldwide_health_pending = False
        self._worldwide_reload_pending = True
        QTimer.singleShot(1000, self._reload_classic_worldwide)

    def _reload_dashboard_worldwide(self):
        if QWebEngineView is None or not hasattr(self, "dashboard_worldwide_view"):
            return
        if not isinstance(self.dashboard_worldwide_view, QWebEngineView):
            return
        self._worldwide_reload_pending = False
        self._worldwide_health_last_ok = time.monotonic()
        self.dashboard_worldwide_view.setUrl(QUrl("https://meshcom.oevsv.at/#"))

    def _reload_classic_worldwide(self):
        if QWebEngineView is None or not hasattr(self, "worldwide_view"):
            return
        if not isinstance(self.worldwide_view, QWebEngineView):
            return
        self._worldwide_reload_pending = False
        self._worldwide_health_last_ok = time.monotonic()
        self.worldwide_view.setUrl(QUrl("https://meshcom.oevsv.at/#"))

    def _worldwide_watchdog_tick(self):
        """Ping the visible Worldwide page and reload only after a real hang."""
        if QWebEngineView is None or self._worldwide_reload_pending:
            return

        view = None
        if hasattr(self, "dashboard_worldwide_view") and isinstance(self.dashboard_worldwide_view, QWebEngineView):
            view = self.dashboard_worldwide_view
        elif hasattr(self, "worldwide_view") and isinstance(self.worldwide_view, QWebEngineView):
            view = self.worldwide_view
        if view is None:
            return

        now = time.monotonic()
        # If the previous JavaScript health check never returned, the renderer
        # is most likely stuck even if Qt has not emitted renderProcessTerminated.
        if self._worldwide_health_pending:
            if now - self._worldwide_health_last_ok >= 20:
                self._worldwide_reload_pending = True
                if view is self.dashboard_worldwide_view:
                    self._reload_dashboard_worldwide()
                else:
                    self._reload_classic_worldwide()
            return

        self._worldwide_health_pending = True

        def _health_result(result):
            self._worldwide_health_pending = False
            self._worldwide_health_last_ok = time.monotonic()

        try:
            view.page().runJavaScript(
                "document.readyState + '|' + (document.documentElement ? document.documentElement.innerHTML.length : 0)",
                _health_result,
            )
        except Exception:
            self._worldwide_health_pending = False

    def _sync_dashboard_tables(self):
        if not hasattr(self, "dashboard_monitor_table"):
            return
        src = self.monitor_table
        dst = self.dashboard_monitor_table
        # Der Dashboard-Monitor muss den kompletten Live-Strom übernehmen.
        # Die frühere Begrenzung auf 8 Zeilen führte dazu, dass ab dem ersten
        # sichtbaren Scrollbereich zwar weiter aufgezeichnet wurde, aber neue
        # Einträge im Dashboard nicht mehr sichtbar wurden.
        rows = src.rowCount()
        dst.setRowCount(rows)
        for r in range(rows):
            vals = [src.item(r, c).text() if src.item(r, c) else "" for c in (0,1,2,3,4,5,6)]
            for c, v in enumerate(vals):
                dst.setItem(r, c, QTableWidgetItem(v))
            # The classic monitor naturally gives the information enough
            # vertical space to wrap long packets.  Keep that behavior in
            # the dashboard instead of cutting the text off in one line.
            dst.setRowHeight(r, 38)
        # Bei aktivem Autoscroll immer den neuesten Monitor-Eintrag zeigen.
        # QTableWidget kann scrollToBottom() innerhalb eines laufenden
        # Layout-/Resize-Zyklus zu früh ausführen. Deshalb nach dem Layout
        # nochmals explizit auf das Ende der vertikalen Scrollbar setzen.
        if getattr(self, "monitor_autoscroll", True) and rows:
            def _dashboard_monitor_to_bottom():
                if not self.dashboard_monitor_table.rowCount():
                    return
                last_item = self.dashboard_monitor_table.item(self.dashboard_monitor_table.rowCount() - 1, 0)
                if last_item is not None:
                    self.dashboard_monitor_table.scrollToItem(
                        last_item, QAbstractItemView.ScrollHint.PositionAtBottom
                    )
                bar = self.dashboard_monitor_table.verticalScrollBar()
                bar.setValue(bar.maximum())

            self.dashboard_monitor_table.scrollToBottom()
            QTimer.singleShot(0, _dashboard_monitor_to_bottom)
        src = self.mh_table
        dst = self.dashboard_mh_table
        rows = min(src.rowCount(), MainWindow.MH_MAX_STATIONS)
        dst.setRowCount(rows)
        for r in range(rows):
            vals = [src.item(r, c).text() if src.item(r, c) else "" for c in (0,1,2,3)]
            for c, v in enumerate(vals):
                dst.setItem(r, c, QTableWidgetItem(v))
        if hasattr(self, "statistics_summary"):
            # Dashboard-Statistik bewusst untereinander statt in einer langen
            # Zeile darstellen. Der vorhandene Statistikbereich bleibt dabei
            # exakt gleich groß.
            message_count = len(self.message_cache)
            node_count = len(self.mh_stations)
            position_count = len(self.station_positions)
            telemetry_count = getattr(self, "telemetry_count", 0)
            monitor_count = len(self.monitor_rows)
            private_count = 0
            room_counts = {}
            for block in self.message_cache.values():
                participants = self._private_participants(block)
                if participants:
                    private_count += 1
                    continue
                # Dieselbe Raumzuordnung wie in der klassischen Statistik:
                # Ziel aus dem MeshCom-Header verwenden, sonst "Alle".
                room = self._room_from_block(block)
                room_key = room if room else "Alle"
                room_counts[room_key] = room_counts.get(room_key, 0) + 1
            lines = [
                f"{ui_text('Nachrichten:')} <b>{message_count}</b>",
                f"{ui_text('Nodes:')} <b>{node_count}</b>",
                f"{ui_text('Positionen:')} <b>{position_count}</b>",
                f"{ui_text('Telemetrie:')} <b>{telemetry_count}</b>",
                f"{ui_text('Privatnachrichten:')} <b>{private_count}</b>",
                f"{ui_text('Monitor-Einträge:')} <b>{monitor_count}</b>",
                f"<b>{ui_text('Nachrichten nach Raum:')}</b>",
            ]
            if room_counts:
                lines.extend(
                    f"{ui_text('Raum')} {room}: <b>{count}</b>"
                    for room, count in sorted(room_counts.items(), key=lambda x: (x[0] != "Alle", int(x[0]) if x[0] != "Alle" else -1))
                )
            else:
                lines.append(ui_text("noch keine Daten"))
            self.dashboard_statistics_label.setText("<br>".join(lines))

    def _worldwide_load_finished(self, ok):
        self._worldwide_health_pending = False
        if not ok or QWebEngineView is None:
            return
        self._worldwide_health_last_ok = time.monotonic()
        # Die eingebettete ÖVSV-Seite übernimmt ihre eigene Aktualisierung.
        # Es gibt keinen zusätzlichen 15-Sekunden-Refresh durch den Guru.
        self.worldwide_view.page().runJavaScript(
            """(function(){
                const els = Array.from(document.querySelectorAll('a,button,[role=button],input'));
                const el = els.find(e => ((e.innerText || e.textContent || e.value || e.title || '') + '').trim().toUpperCase() === 'ACTIVITY');
                if (el) { el.click(); return true; }
                const loose = els.find(e => ((e.innerText || e.textContent || e.value || e.title || '') + '').trim().toUpperCase().includes('ACTIVITY'));
                if (loose) { loose.click(); return true; }
                return false;
            })();"""
        )

    def _update_message_counter(self, text):
        """Update the visible character counter for the 149-character limit."""
        self.message_counter.setText(f"{len(text)}/149")
        if len(text) >= 149:
            self.message_counter.setToolTip("Maximale Länge erreicht: 149 Zeichen")
        else:
            self.message_counter.setToolTip(f"Noch {149 - len(text)} Zeichen frei")

    def _update_dashboard_message_counter(self, text):
        """Update the Dashboard character counter for the 149-character limit."""
        count = len(str(text or ""))
        self.dashboard_message_counter.setText(f"{count}/149")
        if count >= 149:
            self.dashboard_message_counter.setToolTip(
                ui_text("Maximale Länge erreicht: 149 Zeichen")
            )
        else:
            self.dashboard_message_counter.setToolTip(
                ui_text(f"Noch {149 - count} Zeichen frei")
            )

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
        # Das Dashboard und der normale Chat besitzen getrennte Eingabefelder.
        # Beide müssen synchron gesetzt werden, damit Schnelltexte unabhängig
        # davon funktionieren, auf welchem Chat-Tab sie geöffnet wurden.
        self.message_input.setText(text)
        if hasattr(self.message_input, "clearUndo"):
            self.message_input.clearUndo()
        if hasattr(self, "dashboard_message_input"):
            self.dashboard_message_input.setText(text)
            if hasattr(self.dashboard_message_input, "clearUndo"):
                self.dashboard_message_input.clearUndo()
        self.message_input.setFocus()
        self.message_input.setCursorPosition(len(text))
        if hasattr(self, "dashboard_message_input"):
            self.dashboard_message_input.setCursorPosition(len(text))
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

        # Fokus vor dem Öffnen des Popup-Fensters merken. Das Popup selbst
        # erhält anschließend den Fokus, darf aber das Einfügeziel nicht ändern.
        if hasattr(self, "dashboard_message_input") and self.dashboard_message_input.hasFocus():
            self._emoji_target = self.dashboard_message_input
        else:
            self._emoji_target = self.message_input

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

        # Das Fenster erscheint direkt über dem Smiley-Symbol, das gedrückt wurde.
        # Im Dashboard muss deshalb der Dashboard-Smiley verwendet werden;
        # im klassischen Chat der klassische Smiley.
        anchor_button = (
            self.dashboard_emoji_button
            if self._emoji_target is getattr(self, "dashboard_message_input", None)
            else self.emoji_button
        )
        pos = anchor_button.mapToGlobal(anchor_button.rect().topLeft())
        x = max(0, pos.x() - picker.width() + anchor_button.width())
        y = max(0, pos.y() - picker.height() - 6)
        picker.move(x, y)
        picker.show()

    def _insert_emoji(self, emoji):
        """Insert an emoji at the current cursor position."""
        # Das Popup übernimmt den Fokus. Deshalb darf hier nicht erneut über
        # hasFocus() entschieden werden: sonst wird nach dem Öffnen des
        # Pickers fälschlich das alte klassische Nachrichtenfeld verwendet.
        target = self._emoji_target
        if target is None:
            target = self.dashboard_message_input if (
                hasattr(self, "dashboard_message_input") and self.dashboard_message_input.hasFocus()
            ) else self.message_input
        current = target.text()
        if len(current) + len(emoji) > 149:
            self.status.setText(ui_text("Emoji passt nicht mehr in die 149 Zeichen"))
            return
        target.insert(emoji)
        if hasattr(target, "clearUndo"):
            target.clearUndo()
        # Beide Felder bleiben synchron, ohne alten Inhalt zurückzuholen.
        other = self.message_input if target is self.dashboard_message_input else getattr(self, "dashboard_message_input", None)
        if other is not None:
            other.setText(target.text())
            if hasattr(other, "clearUndo"):
                other.clearUndo()
            other.setCursorPosition(target.cursorPosition())
        if self._emoji_picker is not None and self._emoji_picker.isVisible():
            self._emoji_picker.close()
        target.setFocus()
        self._emoji_target = None

    def _clear_emoji_picker(self):
        self._emoji_picker = None
        self._emoji_target = None

    def _load_filter_fields(self, settings):
        for i, field in enumerate(self.filter_inputs, 1):
            field.setText(settings.get(f"filter_room{i}", ""))
        self._ensure_room_tabs()
        # The dashboard is built before the persistent filter fields are loaded.
        # Rebuild its room-chat list afterwards so all five saved rooms are
        # immediately available there as clickable chats.
        if hasattr(self, "dashboard_sidebar"):
            self._dashboard_rebuild_room_buttons(self.dashboard_sidebar.layout())
            self._dashboard_rebuild_private_buttons(self.dashboard_sidebar.layout())

    def _set_connection_status(self, online):
        """Update connection status and preserve online time across auto-reconnects."""
        online = bool(online)
        now = datetime.now()

        if online and not self.connection_online:
            # Neuer Online-Abschnitt: bereits gesammelte Zeit bleibt erhalten.
            self.connection_since = now
        elif not online and self.connection_online:
            # Nur den gerade laufenden Abschnitt einmal aufsummieren.
            if self.connection_since is not None:
                self.connection_elapsed += max(
                    0, int((now - self.connection_since).total_seconds())
                )
            self.connection_since = None

        self.connection_online = online
        self._update_connection_label(now)
        if hasattr(self, "dashboard_connect_button"):
            self.dashboard_connect_button.setEnabled(not online)
        if hasattr(self, "dashboard_disconnect_button"):
            self.dashboard_disconnect_button.setEnabled(online)

    def _reset_connection_duration(self):
        """Reset online duration after an explicit manual disconnect."""
        self.connection_elapsed = 0
        self.connection_since = None

    def _update_connection_label(self, now=None):
        if not hasattr(self, "connection_label"):
            return
        now = now or datetime.now()
        if self.connection_online and self.connection_since is not None:
            current_elapsed = max(
                0, int((now - self.connection_since).total_seconds())
            )
            elapsed = self.connection_elapsed + current_elapsed
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.connection_label.setText(f"🟢 {ui_text('ONLINE  |  seit')} {duration}")
            self.connection_label.setStyleSheet("font-size: 12pt; font-weight: 700; color: #20e060;")
            if hasattr(self, "dashboard_status_label"):
                self.dashboard_status_label.setText(f"🟢 {ui_text('ONLINE  |  seit')} {duration}")
                self.dashboard_status_label.setStyleSheet("font-size: 11pt; font-weight: 700; color: #20e060;")
        else:
            self.connection_label.setText("🔴 " + ui_text("OFFLINE  |  keine Verbindung"))
            self.connection_label.setStyleSheet("font-size: 12pt; font-weight: 700; color: #ff3b30;")
            if hasattr(self, "dashboard_status_label"):
                self.dashboard_status_label.setText("🔴 " + ui_text("OFFLINE  |  keine Verbindung"))
                self.dashboard_status_label.setStyleSheet("font-size: 11pt; font-weight: 700; color: #ff3b30;")

    def _update_clock(self):
        now = datetime.now()
        self.datetime_label.setText(now.strftime("%d.%m.%Y  |  %H:%M:%S"))
        self.datetime_label.setStyleSheet("font-size: 12pt; font-weight: 700;")
        if hasattr(self, "dashboard_clock_label"):
            self.dashboard_clock_label.setText(self.datetime_label.text())
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
        dialog.setWindowTitle(ui_text("Chat-Farben"))
        dialog.resize(520, 430)
        layout = QVBoxLayout(dialog)

        info = QLabel(ui_text("Gemeinsame Farben für alle Räume und Chat-Ansichten:"))
        layout.addWidget(info)

        preview = QTextBrowser(dialog)
        preview.setReadOnly(True)
        preview.setMinimumHeight(120)
        preview.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(preview)

        bg_row = QHBoxLayout()
        bg_label = QLabel(ui_text("Chat-Hintergrund:"))
        bg_preview = QLabel()
        bg_preview.setFixedSize(70, 30)
        bg_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bg_button = QPushButton(ui_text("🎨 Farbe auswählen …"))
        bg_row.addWidget(bg_label)
        bg_row.addWidget(bg_preview)
        bg_row.addWidget(bg_button, 1)
        layout.addLayout(bg_row)

        text_row = QHBoxLayout()
        text_label = QLabel(ui_text("Schriftfarbe für „Alle“:"))
        text_preview = QLabel()
        text_preview.setFixedSize(70, 30)
        text_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_button = QPushButton(ui_text("✏️ Farbe auswählen …"))
        text_row.addWidget(text_label)
        text_row.addWidget(text_preview)
        text_row.addWidget(text_button, 1)
        layout.addLayout(text_row)

        link_row = QHBoxLayout()
        link_label = QLabel(ui_text("Anklickbare Rufzeichen / Internetlinks:"))
        link_preview = QLabel()
        link_preview.setFixedSize(70, 30)
        link_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        link_button = QPushButton(ui_text("🔗 Farbe auswählen …"))
        link_row.addWidget(link_label)
        link_row.addWidget(link_preview)
        link_row.addWidget(link_button, 1)
        layout.addLayout(link_row)

        reset = QPushButton(ui_text("🔄 Standard wiederherstellen"))
        layout.addWidget(reset)

        def refresh():
            bg = self.chat_background
            fg = self.chat_text_color
            link = self.chat_link_color
            bg_preview.setText(bg)
            bg_preview.setStyleSheet(f"background:{bg}; color:{'#ffffff' if QColor(bg).lightness() < 160 else '#000000'}; border:1px solid #777; border-radius:5px;")
            text_preview.setText(fg)
            text_preview.setStyleSheet(f"background:{bg}; color:{fg}; border:1px solid #777; border-radius:5px;")
            link_preview.setText(link)
            link_preview.setStyleSheet(f"background:{bg}; color:{link}; border:1px solid #777; border-radius:5px;")
            self._update_chat_color_preview(preview, bg, fg)

        def pick_bg():
            color = QColorDialog.getColor(QColor(self.chat_background), dialog, ui_text("Chat-Hintergrundfarbe"))
            if color.isValid():
                self._set_chat_colors_live(background=color.name(QColor.NameFormat.HexRgb))
                refresh()

        def pick_text():
            color = QColorDialog.getColor(QColor(self.chat_text_color), dialog, ui_text("Chat-Schriftfarbe"))
            if color.isValid():
                self._set_chat_colors_live(text=color.name(QColor.NameFormat.HexRgb))
                refresh()

        def pick_link():
            color = QColorDialog.getColor(QColor(self.chat_link_color), dialog, ui_text("Farbe für Rufzeichen und Internetlinks"))
            if color.isValid():
                self._set_chat_colors_live(link=color.name(QColor.NameFormat.HexRgb))
                refresh()

        def do_reset():
            self._set_chat_colors_live(background="#000000", text="#ffffff", link="#062f6f")
            refresh()

        bg_button.clicked.connect(pick_bg)
        text_button.clicked.connect(pick_text)
        link_button.clicked.connect(pick_link)
        reset.clicked.connect(do_reset)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        refresh()
        self._apply_language_ui()
        dialog.exec()

    def _set_chat_colors_live(self, background=None, text=None, link=None):
        if background is not None:
            self.chat_background = self._normalize_chat_color(background)
        if text is not None:
            self.chat_text_color = self._normalize_chat_color(text)
        if link is not None:
            self.chat_link_color = self._normalize_chat_color(link)
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
                view.set_chat_colors(self.chat_background, self.chat_text_color, self.chat_link_color)
            except Exception:
                pass
        self.status.setText(
            f"Chat-Farben geändert: Hintergrund {self.chat_background}, Schrift {self.chat_text_color}, Links {self.chat_link_color} – {len(views)} Ansichten"
        )

    # ---------- Settings ----------
    def _write_settings(self):
        config = configparser.ConfigParser()
        if SETTINGS_FILE.exists():
            config.read(SETTINGS_FILE, encoding="utf-8")
        if "MeshCom" not in config:
            config["MeshCom"] = {}
        section = config["MeshCom"]

        # Dashboard und klassische Ansicht benutzen dieselben Einstellungen.
        # Die Dashboard-Felder sind eigene QLineEdit-Widgets. Sie dürfen aber
        # NUR dann zurück in die zentralen Felder synchronisiert werden, wenn
        # das Dashboard tatsächlich aktiv ist. In der klassischen Ansicht
        # sind diese Widgets unsichtbar und können noch alte Werte enthalten.
        # Das führte dazu, dass "Einstellungen speichern" in der klassischen
        # Ansicht die gerade eingegebenen Werte wieder überschrieben hat.
        if getattr(self, "layout_mode", "classic") == "dashboard":
            if hasattr(self, "dashboard_hotspot_input"):
                dashboard_ip = self.dashboard_hotspot_input.text().strip().rstrip("/")
                if dashboard_ip:
                    self.ip_input.setText(dashboard_ip)
            if hasattr(self, "dashboard_room_input"):
                self.target_input.setText(self.dashboard_room_input.text().strip())
            if hasattr(self, "dashboard_callsign_input"):
                self.own_callsign_input.setText(self.dashboard_callsign_input.text().strip())
            if hasattr(self, "dashboard_lat_input"):
                self.own_lat_input.setText(self.dashboard_lat_input.text().strip())
            if hasattr(self, "dashboard_lon_input"):
                self.own_lon_input.setText(self.dashboard_lon_input.text().strip())

        section["ip"] = self.ip_input.text().strip().rstrip("/")
        section["target"] = self.target_input.text().strip()
        section["filter_enabled"] = "1" if self.filter_enabled.isChecked() else "0"
        section["theme"] = self.current_theme
        section["layout_mode"] = getattr(self, "layout_mode", "classic")
        section["chat_background"] = self.chat_background
        section["chat_text_color"] = self.chat_text_color
        section["chat_link_color"] = self.chat_link_color
        section["language"] = self.language if getattr(self, "language", "de") in ("de", "en", "it", "nl", "fr") else "de"
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
        section["own_callsign"] = self._normalize_callsign(self.own_callsign_input.text())
        self.own_callsign_input.setText(section["own_callsign"])
        if hasattr(self, "dashboard_callsign_input"):
            self.dashboard_callsign_input.setText(section["own_callsign"])
        section["own_lat"] = self.own_lat_input.text().strip()
        section["own_lon"] = self.own_lon_input.text().strip()
        for i, field in enumerate(self.filter_inputs, 1):
            section[f"filter_room{i}"] = field.text().strip()
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            config.write(f)

    def open_language_dialog(self):
        """Show the available UI languages."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("language_title"))
        layout = QVBoxLayout(dialog)
        label = QLabel(tr("language"))
        combo = QComboBox()
        combo.addItem(tr("german"), "de")
        combo.addItem(tr("english"), "en")
        combo.addItem(tr("italian"), "it")
        combo.addItem(tr("dutch"), "nl")
        combo.addItem(tr("french"), "fr")
        current = getattr(self, "language", "de")
        combo.setCurrentIndex({"de": 0, "en": 1, "it": 2, "nl": 3, "fr": 4}.get(current, 0))
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
        # Qt provides standard translations for common dialogs/widgets.
        if language == "en":
            return
        try:
            path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
            if self._qt_translator.load(f"qtbase_{language}", path):
                app.installTranslator(self._qt_translator)
                self._qt_translator_loaded = True
        except Exception:
            pass

    def _set_ui_language(self, language):
        """Save and immediately apply the selected UI language."""
        language = language if language in ("de", "en", "it", "nl", "fr") else "de"
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

        # Tab labels: use the stable internal tab key instead of the visible
        # label. This is important for multilingual room tabs because a
        # translated label (e.g. "Stanza 10" or "Salon 10") must not be
        # mistaken for the German source text on the next language change.
        if hasattr(self, "tabs"):
            for i in range(self.tabs.count()):
                widget = self.tabs.widget(i)
                key = getattr(widget, "_mesh_key", None)
                if key and key[0] == "all":
                    self.tabs.setTabText(i, tr("Alle"))
                elif key and key[0] == "room":
                    self.tabs.setTabText(i, self._room_tab_title(key[1]))
                else:
                    title = self.tabs.tabText(i)
                    if title == "Karte" or title == "Map":
                        self.tabs.setTabText(i, tr("Karte"))
                    elif title in {"📡 Monitor", "📡 Moniteur", "📡 Monitor"}:
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

        # Wetteranzeige immer aus den unveränderten Rohwerten neu aufbauen.
        # Wichtig: Niemals den bereits übersetzten Anzeigetext erneut durch
        # ui_text() schicken. Sonst können bei einem Sprachwechsel aus
        # "Temperatur"/"Temperatuur"/"Temperature" Buchstaben angehängt werden.
        self._update_weather_display()

        # Table headers
        if hasattr(self, "monitor_table"):
            self.monitor_table.setHorizontalHeaderLabels([ui_text(x) for x in ["Zeit", "Typ", "Von", "Nach", "RSSI", "SNR", "Information"]])
        if hasattr(self, "mh_table"):
            self.mh_table.setHorizontalHeaderLabels([ui_text(x) for x in ["Rufzeichen", "Entfernung", "RSSI", "SNR", "Batterie", "Zuletzt gehört"]])
        if hasattr(self, "dashboard_monitor_table"):
            self.dashboard_monitor_table.setHorizontalHeaderLabels([
                ui_text("Zeit"), ui_text("Typ"), ui_text("Rufzeichen"), ui_text("Ziel"),
                "RSSI", "SNR", ui_text("Information")
            ])
        if hasattr(self, "dashboard_monitor_filter_combo") and self.dashboard_monitor_filter_combo.count() > 0:
            self.dashboard_monitor_filter_combo.setItemText(0, tr("Alle"))
        if hasattr(self, "dashboard_mh_table"):
            self.dashboard_mh_table.setHorizontalHeaderLabels([
                ui_text("Rufzeichen"), ui_text("Entfernung"), "RSSI", "SNR"
            ])

    def save_all_settings(self):
        # Nur im Dashboard werden die sichtbaren Dashboard-Felder als
        # Eingabequelle verwendet. In der klassischen Ansicht sind diese
        # Felder nur Spiegelwerte und dürfen die klassischen Eingaben nicht
        # mit alten, unsichtbaren Werten überschreiben.
        if getattr(self, "layout_mode", "classic") == "dashboard":
            if hasattr(self, "dashboard_hotspot_input"):
                dashboard_ip = self.dashboard_hotspot_input.text().strip().rstrip("/")
                if dashboard_ip:
                    self.ip_input.setText(dashboard_ip)
            if hasattr(self, "dashboard_room_input"):
                self.target_input.setText(self.dashboard_room_input.text().strip())
            if hasattr(self, "dashboard_callsign_input"):
                self.own_callsign_input.setText(self.dashboard_callsign_input.text().strip())
            if hasattr(self, "dashboard_lat_input"):
                self.own_lat_input.setText(self.dashboard_lat_input.text().strip())
            if hasattr(self, "dashboard_lon_input"):
                self.own_lon_input.setText(self.dashboard_lon_input.text().strip())

        ip = self.ip_input.text().strip().rstrip("/")
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
        self.own_callsign_input.setText(self.own_callsign)
        self.own_lat, self.own_lon = lat, lon
        self._write_settings()

        # Einstellungen speichern darf die bestehende Verbindung NICHT
        # trennen. Die bisherige Version erzeugte hier ein neues MeshCom-
        # Objekt und setzte den Verbindungsstatus auf OFFLINE. Das löste
        # anschließend unnötig den Auto-Reconnect aus.
        #
        # Wenn eine neue Hotspot-IP eingetragen wurde, wird nur die Adresse
        # des bereits vorhandenen Clients aktualisiert. Die nächste Anfrage
        # verwendet damit die neue Adresse, ohne beim Speichern bewusst zu
        # disconnecten.
        if ip:
            if hasattr(self, "mesh") and self.mesh is not None:
                self.mesh.ip = ip
            else:
                self.mesh = MeshCom(ip)
        self._ensure_room_tabs()
        self._update_map()
        if ip:
            self.status.setText(ui_text("Einstellungen gespeichert"))
        else:
            self.status.setText(ui_text("Einstellungen gespeichert – Hotspot-IP fehlt noch"))

    def save_filter_settings(self):
        self._write_settings()
        self._ensure_room_tabs()
        self.update_messages()
        if hasattr(self, "dashboard_sidebar"):
            self._dashboard_rebuild_room_buttons(self.dashboard_sidebar.layout())
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

    def _update_weather_display(self):
        """Render the weather line from raw values for the current language.

        The raw values in self.weather_data are language-independent. Rebuilding
        the complete line on every language change prevents translations from
        being applied repeatedly to an already translated string.
        """
        data = getattr(self, "weather_data", None) or {}
        if not data or not all(data.get(k) not in (None, "") for k in ("temperature", "humidity", "qfe", "qnh")):
            return
        weather_text = (
            f"{tr('Temperatur:')} {data.get('temperature', '–')} | "
            f"{tr('Luftfeuchte:')} {data.get('humidity', '–')} | "
            f"{tr('QFE:')} {data.get('qfe', '–')} | "
            f"{tr('QNH:')} {data.get('qnh', '–')}"
        )
        if hasattr(self, "weather_values_label"):
            self.weather_values_label.setText(weather_text)
        if hasattr(self, "dashboard_weather_values"):
            self.dashboard_weather_values.setText(weather_text)

    def _apply_weather_result(self, data):
        self._weather_fetch_in_progress = False
        self.weather_refresh_button.setEnabled(True)
        if data.get("error"):
            self.weather_values_label.setText(ui_text("Keine Wetterwerte in der WX-Information gefunden"))
            self.weather_status_label.setText(str(data["error"]))
            return
        self.weather_data = data
        self._update_weather_display()
        if hasattr(self, "dashboard_weather_city") and self.dashboard_weather_city.text().strip() != self.weather_city_input.text().strip():
            self.dashboard_weather_city.setText(self.weather_city_input.text().strip())
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
        try:
            from i18n import get_language
            lang = get_language()
        except Exception:
            lang = "de"
        titles = {
            "de": "MeshCom-Guru – Anleitung",
            "en": "MeshCom-Guru – User guide",
            "it": "MeshCom-Guru – Guida utente",
            "nl": "MeshCom-Guru – Gebruikershandleiding",
            "fr": "MeshCom-Guru – Guide utilisateur",
        }
        dialog.setWindowTitle(titles.get(lang, titles["de"]))
        dialog.resize(860, 720)
        layout = QVBoxLayout(dialog)
        view = QTextBrowser(dialog)
        view.setOpenExternalLinks(True)

        guides = {
            "de": f"""
            <h2>MeshCom-Guru v{VERSION}</h2><h3>Kurzanleitung</h3>
            <h3>🎛 Darstellung: Klassisch oder Dashboard</h3>
            <p>Unter <b>Einstellungen → Darstellung</b> kann zwischen <b>Klassisch</b> und dem neuen <b>Dashboard</b> gewechselt werden. Beide Ansichten verwenden dieselben MeshCom-Daten und Funktionen. Die Auswahl wird gespeichert und beim nächsten Start wieder verwendet.</p>
            <p>Das Dashboard bündelt Verbindung, Räume, Chat, Karte, Weltweit, Monitor, MH und Statistik in einer Ansicht. Die klassische Oberfläche bleibt vollständig verfügbar.</p>
            <h3>💬 Raum-Chats und 👤 Private Chats</h3>
            <p>Die bis zu <b>fünf gespeicherten Räume</b> werden im Dashboard links direkt als anklickbare <b>Raum-Chats</b> angezeigt. Ein Klick auf einen Raum öffnet ausschließlich diesen Raum. <b>Alle</b> ist eine eigene Ansicht und kann jederzeit wieder angeklickt werden.</p>
            <p><b>Private Chats</b> stehen getrennt darunter. Ein Klick auf einen privaten Chat öffnet die private Unterhaltung und wechselt nicht ungewollt zurück zu „Alle“. Neue private Nachrichten werden in der privaten Unterhaltung und im Bereich „Alle“ berücksichtigt.</p>
            <p><b>Rufzeichen anklicken:</b> Ein anklickbares Rufzeichen öffnet ein kleines Menü mit <b>Privater Chat</b> und <b>QRZ.com</b>. Für QRZ.com wird automatisch nur das reine Rufzeichen verwendet, also z. B. <code>DO1ABC-12</code> → <code>DO1ABC</code>.</p>
            <h3>Verbindung und Einstellungen</h3>
            <p><b>Hotspot-IP:</b> IP-Adresse des MeshCom-WebService eintragen.</p>
            <p><b>Eigene Station / GPS:</b> Eigenes Rufzeichen sowie optional Breitengrad und Längengrad eintragen.</p>
            <p><b>Einstellungen speichern:</b> Speichert persönliche Einstellungen unter <code>~/.MeshCom/settings.ini</code>.</p>
            <h3>Verbinden und Trennen / Auto-Reconnect</h3>
            <p>Mit <b>Verbinden</b> wird die Verbindung zum MeshCom-WebService hergestellt. Nach einer manuellen Verbindung ist die automatische Wiederverbindung aktiv.</p>
            <p>Wenn die Verbindung durch einen vorübergehenden Netzwerk-, Hotspot- oder WebService-Fehler verloren geht, versucht MeshCom-Guru automatisch erneut zu verbinden. Mit <b>Trennen</b> wird die automatische Wiederverbindung bewusst abgeschaltet.</p>
            <h3>Nachrichten senden</h3>
            <p>Im Dashboard genügt <b>Enter</b> zum Senden. Ein zusätzlicher Senden-Button wird dort nicht benötigt und schafft mehr Platz für das Nachrichtenfeld.</p>
            <p>Nachrichten sind auf <b>149 Zeichen</b> begrenzt. Der Live-Zähler zeigt die aktuelle Länge.</p>
            <h3>📡 Monitor, 📋 Stations / MH und 📊 Statistik</h3>
            <p>Der <b>Monitor</b> zeigt MeshCom-UDP-Pakete auf <b>Port 1799</b> mit Typ, Rufzeichen, Ziel, RSSI, SNR und Information. Die Informationsspalte bleibt lesbar und kann bei Bedarf gescrollt werden.</p>
            <p><b>Stations / MH</b> zeigt zuletzt gehörte Stationen mit Rufzeichen, Entfernung, RSSI und SNR. Die Spalten sind so angeordnet, dass keine unnötige horizontale Scrollleiste benötigt wird.</p>
            <p><b>Statistik</b> zeigt die laufenden Sitzungszähler für Nachrichten, Nodes, Positionen, Telemetrie, private Nachrichten, Monitor-Einträge und Nachrichten nach Raum.</p>
            <h3>🗺 Karte und 🌐 Weltweit</h3>
            <p>Die OSM-/Leaflet-Karte zeigt Positionsdaten und Stationen. Der Tab <b>🌐 Weltweit</b> bzw. die Weltweit-Ansicht im Dashboard öffnet die öffentliche MeshCom-Aktivitätsseite des ÖVSV. Beim Laden wird automatisch <b>ACTIVITY</b> ausgewählt. Die eingebettete Webseite übernimmt ihre eigene Aktualisierung; MeshCom-Guru verwendet keinen zusätzlichen 15-Sekunden-Refresh.</p>
            <h3>🌤 Wetterdaten</h3>
            <p>Die WX-Anzeige zeigt Temperatur, Luftfeuchte, QFE und QNH, sofern der WebService diese Werte liefert. Wetter kann aktualisiert und an das aktuell ausgewählte Ziel gesendet werden.</p>
            <h3>⚡ Schnelltexte und 😊 Emojis</h3>
            <p>Schnelltexte können eingefügt, bearbeitet, ergänzt und gelöscht werden. Das Einfügen sendet nicht automatisch. Der Emoji-Picker fügt das ausgewählte Emoji an der Cursorposition ein.</p>
            <h3>🎨 Chat-Farben und 🔊 Sound</h3>
            <p>Unter <b>Einstellungen → Chat-Farben …</b> können Hintergrund, Schriftfarbe für „Alle“ sowie die Farbe anklickbarer Rufzeichen und Internetlinks eingestellt werden. Sound, Lautstärke und Hell-/Dunkel-Theme können ebenfalls konfiguriert werden.</p>
            <h3>Node Info</h3><p><b>Node Info aufrufen</b> öffnet die Informationen des verbundenen MeshCom-WebService.</p>
            <h3>Sprache</h3><p>Die Benutzeroberfläche unterstützt <b>Deutsch, English, Italiano, Nederlands und Français</b>. Die Auswahl wird gespeichert. Auch die integrierte Anleitung folgt der gewählten Sprache.</p>
<h3>💾 Datensicherung und ♻️ Wiederherstellung</h3><p>Über <b>Datei → Datensicherung erstellen …</b> können die persönlichen MeshCom-Guru-Daten aus <code>~/.MeshCom</code> als ZIP-Datei gesichert werden. Mit <b>Datei → Datensicherung wiederherstellen …</b> kann eine zuvor erstellte Sicherung zurückgespielt werden. Nicht im Backup enthaltene Dateien werden nicht gelöscht.</p><p>Nach einer Wiederherstellung werden die Daten auch in der laufenden Anwendung übernommen. Beim anschließenden Neustart bleibt der restaurierte Backup-Stand erhalten.</p>
<h3>🔄 Nach Updates suchen</h3><p>Über <b>Hilfe → Nach Update suchen …</b> kann die installierte Version mit der aktuellen GitHub-Release verglichen werden. Bei einer neueren Version wird ein Hinweis mit Link zur GitHub-Release angezeigt. MeshCom-Guru lädt Updates nicht automatisch herunter und installiert sie nicht automatisch.</p>
                        <h3>Installation</h3><p><b>Linux ZIP:</b> Den Ordner <code>MeshCom</code> entpacken und <code>./run_linux.sh</code> starten. <b>Windows:</b> <code>run_windows.bat</code> starten. <b>Debian:</b> Installation nach <code>/usr/share/MeshCom</code>; persönliche Einstellungen bleiben unter <code>~/.MeshCom/settings.ini</code>.</p>
            """,
            "en": f"""
            <h2>MeshCom-Guru v{VERSION}</h2><h3>Quick guide</h3>
            <h3>🎛 Display: Classic or Dashboard</h3><p>Under <b>Settings → Display</b>, choose between <b>Classic</b> and the new <b>Dashboard</b>. Both views use the same MeshCom data and functions. The selection is saved and restored at the next start.</p><p>The Dashboard combines connection, rooms, chat, map, worldwide activity, monitor, MH and statistics in one view. The classic interface remains fully available.</p>
            <h3>💬 Room Chats and 👤 Private Chats</h3><p>The up to <b>five saved rooms</b> appear on the left as directly clickable <b>Room Chats</b>. Clicking a room opens that room only. <b>All</b> is a separate view and can always be selected again.</p><p><b>Private Chats</b> are listed separately below. Clicking a private chat opens that conversation and does not jump back to “All”. New private messages are reflected in the private conversation and in “All”.</p><p><b>Clicking a callsign:</b> A clickable callsign opens a small menu with <b>Private Chat</b> and <b>QRZ.com</b>. For QRZ.com, only the base callsign is used automatically, for example <code>DO1ABC-12</code> → <code>DO1ABC</code>.</p>
            <h3>Connection and settings</h3><p><b>Hotspot IP:</b> Enter the MeshCom WebService IP address.</p><p><b>Own station / GPS:</b> Enter your callsign and optionally latitude and longitude.</p><p><b>Save settings:</b> Personal settings are stored in <code>~/.MeshCom/settings.ini</code>.</p>
            <h3>Connect / Disconnect / Auto-Reconnect</h3><p>Use <b>Connect</b> to connect to the MeshCom WebService. After a manual connection, automatic reconnection is armed. If a temporary network, hotspot or WebService error occurs, MeshCom-Guru tries to reconnect automatically. <b>Disconnect</b> deliberately disables automatic reconnection.</p>
            <h3>Sending messages</h3><p>In the Dashboard, simply press <b>Enter</b> to send. No separate Send button is needed, leaving more room for the message field.</p><p>Messages are limited to <b>149 characters</b> and the live counter shows the current length.</p>
            <h3>📡 Monitor, 📋 Stations / MH and 📊 Statistics</h3><p><b>Monitor</b> shows MeshCom UDP packets on <b>port 1799</b> with type, callsign, target, RSSI, SNR and information. The information column remains readable and can be scrolled when necessary.</p><p><b>Stations / MH</b> shows recently heard stations with callsign, distance, RSSI and SNR without an unnecessary horizontal scrollbar.</p><p><b>Statistics</b> shows live session counters for messages, nodes, positions, private messages, monitor entries and messages by room.</p>
            <h3>🗺 Map and 🌐 Worldwide</h3><p>The OSM/Leaflet map displays positions and stations. The <b>Worldwide</b> view opens the public MeshCom activity page of ÖVSV and automatically selects <b>ACTIVITY</b>. The embedded website handles its own updates; MeshCom-Guru does not add a 15-second refresh.</p>
            <h3>🌤 Weather</h3><p>WX can display temperature, humidity, QFE and QNH when supplied by the WebService. Weather can be refreshed and sent to the currently selected target.</p>
            <h3>⚡ Quick texts and 😊 Emojis</h3><p>Quick texts can be inserted, edited, added and deleted. Inserting a quick text does not send it automatically. The emoji picker inserts the selected emoji at the cursor position.</p>
            <h3>🎨 Chat colors and 🔊 Sound</h3><p>Under <b>Settings → Chat colors …</b> you can configure the background, the text color for “All”, and the color of clickable callsigns and Internet links. Sound, volume and light/dark theme are also configurable.</p>
            <h3>Node Info</h3><p><b>Open Node Info</b> displays information from the connected MeshCom WebService.</p>
            <h3>Language</h3><p>The interface supports <b>Deutsch, English, Italiano, Nederlands and Français</b>. The choice is saved, and the built-in guide follows the selected language.</p>
<h3>💾 Backup and ♻️ Restore</h3><p>Use <b>File → Create backup …</b> to save the personal MeshCom-Guru data from <code>~/.MeshCom</code> as a ZIP file. Use <b>File → Restore backup …</b> to restore a previously created backup. Files that are not included in the backup are not deleted.</p><p>After a restore, the restored data is also applied to the running application. During the following restart, the restored backup state is preserved.</p>
<h3>🔄 Check for updates</h3><p>Use <b>Help → Check for updates …</b> to compare the installed version with the current GitHub release. If a newer version is available, MeshCom-Guru shows a notice with a link to the GitHub release. MeshCom-Guru does not download or install updates automatically.</p>
                        <h3>Installation</h3><p><b>Linux ZIP:</b> Extract <code>MeshCom</code> and run <code>./run_linux.sh</code>. <b>Windows:</b> run <code>run_windows.bat</code>. <b>Debian:</b> installation in <code>/usr/share/MeshCom</code>; personal settings remain in <code>~/.MeshCom/settings.ini</code>.</p>
            """,
            "it": f"""
            <h2>MeshCom-Guru v{VERSION}</h2><h3>Guida rapida</h3>
            <h3>🎛 Visualizzazione: Classica o Dashboard</h3><p>In <b>Impostazioni → Visualizzazione</b> è possibile scegliere tra <b>Classica</b> e la nuova <b>Dashboard</b>. Entrambe usano gli stessi dati e le stesse funzioni MeshCom. La scelta viene salvata.</p><p>La Dashboard riunisce connessione, stanze, chat, mappa, attività mondiale, monitor, MH e statistiche in un'unica vista.</p>
            <h3>💬 Chat delle stanze e 👤 Chat privati</h3><p>Le <b>cinque stanze salvate</b> vengono mostrate a sinistra come <b>chat delle stanze</b> selezionabili. Facendo clic su una stanza si apre solo quella stanza. <b>Tutti</b> è una vista separata e può essere selezionata in qualsiasi momento.</p><p>I <b>chat privati</b> sono elencati separatamente. Facendo clic su un chat privato si apre la conversazione privata senza tornare a “Tutti”.</p><p><b>Facendo clic su un nominativo:</b> un nominativo cliccabile apre un piccolo menu con <b>Chat privato</b> e <b>QRZ.com</b>. Per QRZ.com viene utilizzato automaticamente solo il nominativo base, ad esempio <code>DO1ABC-12</code> → <code>DO1ABC</code>.</p>
            <h3>Connessione e impostazioni</h3><p><b>IP hotspot:</b> inserire l'indirizzo IP del WebService MeshCom. <b>Stazione/GPS:</b> inserire il proprio nominativo e, se necessario, latitudine e longitudine. Le impostazioni personali sono salvate in <code>~/.MeshCom/settings.ini</code>.</p>
            <h3>Connetti / Disconnetti / Riconnessione automatica</h3><p><b>Connetti</b> stabilisce la connessione. Dopo una connessione manuale la riconnessione automatica è attiva. <b>Disconnetti</b> la disattiva intenzionalmente.</p>
            <h3>Invio dei messaggi</h3><p>Nella Dashboard basta premere <b>Invio</b> per spedire il messaggio. Non serve un pulsante Invia separato. Il limite è di <b>149 caratteri</b>.</p>
            <h3>📡 Monitor, 📋 Stations / MH e 📊 Statistiche</h3><p>Il <b>Monitor</b> mostra i pacchetti UDP MeshCom sulla <b>porta 1799</b> con tipo, nominativo, destinazione, RSSI, SNR e informazioni. La colonna informazioni può essere fatta scorrere.</p><p><b>Stations / MH</b> mostra le stazioni ascoltate recentemente con nominativo, distanza, RSSI e SNR senza una barra orizzontale inutile. Le <b>Statistiche</b> mostrano i contatori della sessione.</p>
            <h3>🗺 Mappa e 🌐 Mondiale</h3><p>La mappa OSM/Leaflet mostra posizioni e stazioni. La vista <b>Mondiale</b> apre l'attività pubblica MeshCom e seleziona automaticamente <b>ACTIVITY</b>. Il sito integrato gestisce i propri aggiornamenti; non viene aggiunto un refresh di 15 secondi.</p>
            <h3>🌤 Meteo, ⚡ Testi rapidi e 😊 Emoji</h3><p>La WX mostra temperatura, umidità, QFE e QNH quando disponibili. I testi rapidi possono essere inseriti e modificati senza invio automatico. Il selettore emoji inserisce l'emoji nella posizione del cursore.</p>
            <h3>🎨 Colori chat e 🔊 Suono</h3><p>I colori della chat, dei nominativi/link cliccabili, il suono, il volume e il tema chiaro/scuro possono essere configurati nelle impostazioni.</p>
            <h3>Node Info</h3><p><b>Info nodo</b> mostra le informazioni del WebService MeshCom collegato.</p>
            <h3>Lingua</h3><p>L'interfaccia supporta <b>Deutsch, English, Italiano, Nederlands e Français</b>. Anche questa guida segue la lingua selezionata.</p>
            <h3>💾 Backup e ♻️ Ripristino</h3><p>Con <b>File → Crea backup …</b> puoi salvare i dati personali di MeshCom-Guru da <code>~/.MeshCom</code> in un file ZIP. Con <b>File → Ripristina backup …</b> puoi ripristinare un backup creato in precedenza. I file non inclusi nel backup non vengono eliminati.</p><p>Dopo il ripristino, i dati vengono applicati anche all'applicazione in esecuzione. Al riavvio successivo il contenuto ripristinato viene mantenuto.</p>
            <h3>🔄 Controlla aggiornamenti</h3><p>Con <b>Aiuto → Cerca aggiornamenti …</b> puoi confrontare la versione installata con la release GitHub corrente. Se è disponibile una versione più recente, MeshCom-Guru mostra un avviso con il link alla release GitHub. Gli aggiornamenti non vengono scaricati o installati automaticamente.</p>
            <h3>Installazione</h3><p><b>Linux:</b> estrarre <code>MeshCom</code> e avviare <code>./run_linux.sh</code>. <b>Windows:</b> avviare <code>run_windows.bat</code>. <b>Debian:</b> installazione in <code>/usr/share/MeshCom</code>.</p>
            """,
            "nl": f"""
            <h2>MeshCom-Guru v{VERSION}</h2><h3>Korte handleiding</h3>
            <h3>🎛 Weergave: Klassiek of Dashboard</h3><p>Onder <b>Instellingen → Weergave</b> kun je kiezen tussen <b>Klassiek</b> en het nieuwe <b>Dashboard</b>. Beide weergaven gebruiken dezelfde MeshCom-gegevens en functies. De keuze wordt opgeslagen.</p><p>Het Dashboard combineert verbinding, ruimtes, chat, kaart, wereldwijde activiteit, monitor, MH en statistieken.</p>
            <h3>💬 Ruimtechats en 👤 Privéchats</h3><p>De <b>vijf opgeslagen ruimtes</b> staan links als direct aanklikbare <b>ruimtechats</b>. Klik op een ruimte om alleen die ruimte te openen. <b>Alle</b> is een aparte weergave en kan altijd opnieuw worden gekozen.</p><p><b>Privéchats</b> staan apart. Een klik opent de privéconversatie en springt niet terug naar “Alle”.</p><p><b>Op een roepnaam klikken:</b> een aanklikbare roepnaam opent een klein menu met <b>Privéchat</b> en <b>QRZ.com</b>. Voor QRZ.com wordt automatisch alleen de basisroepnaam gebruikt, bijvoorbeeld <code>DO1ABC-12</code> → <code>DO1ABC</code>.</p>
            <h3>Verbinding en instellingen</h3><p><b>Hotspot-IP:</b> voer het IP-adres van de MeshCom-WebService in. <b>Eigen station/GPS:</b> voer je roepnaam en eventueel breedte- en lengtegraad in. Persoonlijke instellingen worden opgeslagen in <code>~/.MeshCom/settings.ini</code>.</p>
            <h3>Verbinden / Verbinding verbreken / Automatische herverbinding</h3><p>Met <b>Verbinden</b> maak je verbinding met de MeshCom-WebService. Na een handmatige verbinding is automatische herverbinding actief. <b>Verbinding verbreken</b> schakelt dit bewust uit.</p>
            <h3>Berichten verzenden</h3><p>In het Dashboard druk je gewoon op <b>Enter</b> om te verzenden. Een aparte knop Verzenden is niet nodig. Berichten zijn beperkt tot <b>149 tekens</b>.</p>
            <h3>📡 Monitor, 📋 Stations / MH en 📊 Statistieken</h3><p>De <b>Monitor</b> toont MeshCom-UDP-pakketten op <b>poort 1799</b> met type, roepnaam, doel, RSSI, SNR en informatie. De informatiekolom kan worden gescrold.</p><p><b>Stations / MH</b> toont recent gehoorde stations met roepnaam, afstand, RSSI en SNR zonder onnodige horizontale scrollbar. <b>Statistieken</b> tonen de actuele sessietellers.</p>
            <h3>🗺 Kaart en 🌐 Wereldwijd</h3><p>De OSM/Leaflet-kaart toont posities en stations. <b>Wereldwijd</b> opent de openbare MeshCom Activity-pagina en selecteert automatisch <b>ACTIVITY</b>. De website beheert zijn eigen updates; MeshCom-Guru voegt geen refresh van 15 seconden toe.</p>
            <h3>🌤 Weer, ⚡ Snelteksten en 😊 Emoji's</h3><p>WX toont temperatuur, luchtvochtigheid, QFE en QNH indien beschikbaar. Snelteksten worden ingevoegd zonder automatisch verzenden. De emoji-kiezer plaatst de emoji op de cursorpositie.</p>
            <h3>🎨 Chatkleuren en 🔊 Geluid</h3><p>Chatkleuren, kleuren voor klikbare roepnamen/links, geluid, volume en licht/donker-thema zijn instelbaar.</p>
            <h3>Node-info</h3><p><b>Node-info</b> toont de informatie van de verbonden MeshCom-WebService.</p>
            <h3>Taal</h3><p>De interface ondersteunt <b>Deutsch, English, Italiano, Nederlands en Français</b>. De ingebouwde handleiding volgt de gekozen taal.</p>
            <h3>💾 Back-up en ♻️ Herstellen</h3><p>Gebruik <b>Bestand → Back-up maken …</b> om de persoonlijke MeshCom-Guru-gegevens uit <code>~/.MeshCom</code> als ZIP-bestand op te slaan. Met <b>Bestand → Back-up herstellen …</b> kun je een eerder gemaakte back-up terugzetten. Bestanden die niet in de back-up staan worden niet verwijderd.</p><p>Na herstel worden de teruggezette gegevens ook in de actieve toepassing overgenomen. Bij de daaropvolgende herstart blijft de herstelde back-up behouden.</p>
            <h3>🔄 Naar updates zoeken</h3><p>Via <b>Help → Naar updates zoeken …</b> kun je de geïnstalleerde versie vergelijken met de huidige GitHub-release. Als een nieuwere versie beschikbaar is, toont MeshCom-Guru een melding met een link naar de GitHub-release. Updates worden niet automatisch gedownload of geïnstalleerd.</p>
            <h3>Installatie</h3><p><b>Linux:</b> pak <code>MeshCom</code> uit en start <code>./run_linux.sh</code>. <b>Windows:</b> start <code>run_windows.bat</code>. <b>Debian:</b> installatie in <code>/usr/share/MeshCom</code>.</p>
            """,
            "fr": f"""
            <h2>MeshCom-Guru v{VERSION}</h2><h3>Guide rapide</h3>
            <h3>🎛 Affichage : Classique ou Tableau de bord</h3><p>Dans <b>Paramètres → Affichage</b>, choisissez entre <b>Classique</b> et le nouveau <b>Tableau de bord</b>. Les deux vues utilisent les mêmes données et fonctions MeshCom. Le choix est enregistré.</p><p>Le Tableau de bord réunit connexion, salons, chat, carte, activité mondiale, moniteur, MH et statistiques dans une seule vue.</p>
            <h3>💬 Chats de salons et 👤 Chats privés</h3><p>Les <b>cinq salons enregistrés</b> sont affichés à gauche comme <b>chats de salons</b> cliquables. Un clic ouvre uniquement ce salon. <b>Tous</b> est une vue séparée et peut être sélectionnée à tout moment.</p><p>Les <b>chats privés</b> sont affichés séparément. Un clic ouvre la conversation privée sans revenir à « Tous ».</p><p><b>Cliquer sur un indicatif :</b> un indicatif cliquable ouvre un petit menu avec <b>Chat privé</b> et <b>QRZ.com</b>. Pour QRZ.com, seul l'indicatif de base est utilisé automatiquement, par exemple <code>DO1ABC-12</code> → <code>DO1ABC</code>.</p>
            <h3>Connexion et paramètres</h3><p><b>IP du hotspot :</b> saisir l'adresse IP du WebService MeshCom. <b>Station/GPS :</b> saisir votre indicatif et, si nécessaire, latitude et longitude. Les paramètres personnels sont enregistrés dans <code>~/.MeshCom/settings.ini</code>.</p>
            <h3>Connecter / Déconnecter / Reconnexion automatique</h3><p><b>Connecter</b> établit la connexion au WebService MeshCom. Après une connexion manuelle, la reconnexion automatique est activée. <b>Déconnecter</b> la désactive volontairement.</p>
            <h3>Envoi des messages</h3><p>Dans le Tableau de bord, appuyez simplement sur <b>Entrée</b> pour envoyer. Aucun bouton Envoyer séparé n'est nécessaire. Les messages sont limités à <b>149 caractères</b>.</p>
            <h3>📡 Moniteur, 📋 Stations / MH et 📊 Statistiques</h3><p>Le <b>Moniteur</b> affiche les paquets UDP MeshCom sur le <b>port 1799</b> avec type, indicatif, destination, RSSI, SNR et informations. La colonne d'informations peut être parcourue.</p><p><b>Stations / MH</b> affiche les stations entendues récemment avec indicatif, distance, RSSI et SNR sans barre de défilement horizontale inutile. Les <b>Statistiques</b> affichent les compteurs de session.</p>
            <h3>🗺 Carte et 🌐 Monde entier</h3><p>La carte OSM/Leaflet affiche les positions et stations. <b>Monde entier</b> ouvre la page publique d'activité MeshCom et sélectionne automatiquement <b>ACTIVITY</b>. Le site intégré gère ses propres mises à jour ; MeshCom-Guru n'ajoute pas de rafraîchissement de 15 secondes.</p>
            <h3>🌤 Météo, ⚡ Textes rapides et 😊 Emojis</h3><p>WX affiche la température, l'humidité, QFE et QNH lorsqu'ils sont disponibles. Les textes rapides sont insérés sans envoi automatique. Le sélecteur d'emoji insère l'emoji à la position du curseur.</p>
            <h3>🎨 Couleurs du chat et 🔊 Son</h3><p>Les couleurs du chat, des indicatifs/liens cliquables, le son, le volume et le thème clair/sombre sont configurables dans les paramètres.</p>
            <h3>Infos du nœud</h3><p><b>Infos du nœud</b> affiche les informations du WebService MeshCom connecté.</p>
            <h3>Langue</h3><p>L'interface prend en charge <b>Deutsch, English, Italiano, Nederlands et Français</b>. Le guide intégré suit également la langue sélectionnée.</p>
<h3>💾 Sauvegarde et ♻️ restauration</h3><p>Utilisez <b>Fichier → Créer une sauvegarde …</b> pour enregistrer les données personnelles de MeshCom-Guru depuis <code>~/.MeshCom</code> dans un fichier ZIP. Avec <b>Fichier → Restaurer une sauvegarde …</b>, vous pouvez restaurer une sauvegarde précédente. Les fichiers qui ne figurent pas dans la sauvegarde ne sont pas supprimés.</p><p>Après la restauration, les données restaurées sont également appliquées à l'application en cours d'exécution. Lors du redémarrage suivant, l'état restauré est conservé.</p>
<h3>🔄 Rechercher les mises à jour</h3><p>Avec <b>Aide → Rechercher les mises à jour …</b>, vous pouvez comparer la version installée avec la release GitHub actuelle. Si une version plus récente est disponible, MeshCom-Guru affiche un message avec un lien vers la release GitHub. Les mises à jour ne sont ni téléchargées ni installées automatiquement.</p>
                        <h3>Installation</h3><p><b>Linux :</b> extraire <code>MeshCom</code> et lancer <code>./run_linux.sh</code>. <b>Windows :</b> lancer <code>run_windows.bat</code>. <b>Debian :</b> installation dans <code>/usr/share/MeshCom</code>.</p>
            """,
        }
        view.setHtml(guides.get(lang, guides["de"]))
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

    def _room_tab_title(self, room):
        """Return the translated display title for a MeshCom room tab."""
        return f"{ui_text('Raum')} {room}"

    def _ensure_room_tabs(self):
        self._ensure_tab(("all", "all"), tr("Alle"))
        rooms = self._rooms()
        for room in rooms:
            self._ensure_tab(("room", room), self._room_tab_title(room))

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
        view.set_chat_colors(self.chat_background, self.chat_text_color, self.chat_link_color)
        view._mesh_key = key
        # Keep a direct registry of every chat view.  This is intentionally
        # independent of the current tab index, so every room is updated
        # immediately when the common background color changes.
        if view not in self._all_chat_views:
            self._all_chat_views.append(view)
        view.callsignActionClicked.connect(self._handle_callsign_action)
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

        # Dashboard: die sichtbaren Raum-/Privat-/Alle-Schaltflächen müssen
        # exakt dieselbe Ungelesen-Logik wie die klassische Tab-Leiste benutzen.
        # Entscheidend ist dabei die aktuell im Dashboard angezeigte Auswahl,
        # nicht der (unsichtbare) aktuelle Index der klassischen Tab-Leiste.
        if hasattr(self, "dashboard_sidebar"):
            self._dashboard_update_chat_button(key)

        dashboard_current = getattr(self, "dashboard_current_key", None)
        classic_current = self.tabs.currentIndex() == idx
        if not was_unread and dashboard_current != key and not classic_current:
            self._play_notification_sound()

    def _set_tab_normal(self, key):
        if key not in self.tab_keys:
            return
        idx = self.tab_keys[key]
        self.tabs.tabBar().setTabTextColor(idx, Qt.GlobalColor.black if self.current_theme == "light" else Qt.GlobalColor.white)
        if hasattr(self, "dashboard_sidebar"):
            self._dashboard_update_chat_button(key)

    def _handle_callsign_action(self, callsign, action):
        callsign = self._normalize_callsign(callsign)
        if not callsign:
            return
        if action == "private":
            self.open_private_chat(callsign)
            return
        if action == "mention":
            text = f"@{callsign} "
            # Nur das aktuell sichtbare Eingabefeld ändern. Dadurch werden
            # keine unnötigen TextChanged-Signale im anderen Layout ausgelöst.
            if getattr(self, "layout_mode", "classic") == "dashboard" and hasattr(self, "dashboard_message_input"):
                target = self.dashboard_message_input
            else:
                target = self.message_input
            target.setText(text)
            target.setFocus()
            target.setCursorPosition(len(text))
            self.status.setText(ui_text(f"Erwähnung vorbereitet: @{callsign}"))
            return
        if action == "qrz":
            qrz_callsign = callsign.split("-", 1)[0]
            QDesktopServices.openUrl(QUrl(f"https://www.qrz.com/db/{qrz_callsign}"))

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
        if hasattr(self, "dashboard_sidebar"):
            self._dashboard_rebuild_private_buttons(self.dashboard_sidebar.layout())
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
        timestamp = cls._timestamp_from_block(block) or ""
        if match:
            # MsgIds are not globally unique for the lifetime of the program.
            # They can wrap/repeat after enough traffic. Using only MSGID as
            # the cache key can therefore hide a later message in the chat
            # although it is still visible in Monitor.
            msgid = match.group(1).upper()
            without_msgid = re.sub(r"\bMSGID\s*[:=\s]*[0-9A-F]+", "", plain, flags=re.IGNORECASE)
            without_msgid = re.sub(r"\s+", " ", without_msgid).strip().casefold()
            return ("msgid", msgid, timestamp, without_msgid)
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
            r"[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?"
            r"(?=\s|$)",
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

    def _bubble_link_activated(self, url):
        """Handle links clicked inside room/private message bubbles.

        Rufzeichen in Bubble-Chats use the same non-modal context menu as the
        normal QTextBrowser chats.  In particular, do NOT open a modal QMenu
        here: on the Raspberry Pi that can block the Qt/GTK event loop.
        """
        value = str(url or "").strip()
        if value.startswith("meshcom://call/"):
            callsign = re.sub(
                r"[^A-Za-z0-9-]",
                "",
                value.rsplit("/", 1)[-1],
            ).upper()
            if not callsign:
                return

            menu = QMenu(self)
            private_action = menu.addAction(ui_text("Privat Chat"))
            mention_action = menu.addAction(f"@{callsign}")
            menu.addSeparator()
            qrz_action = menu.addAction("QRZ.com")

            private_action.triggered.connect(
                lambda _checked=False, c=callsign: self._handle_callsign_action(c, "private")
            )
            mention_action.triggered.connect(
                lambda _checked=False, c=callsign: self._handle_callsign_action(c, "mention")
            )
            qrz_action.triggered.connect(
                lambda _checked=False, c=callsign: self._handle_callsign_action(c, "qrz")
            )

            # Nicht-modal: der normale Event-Loop bleibt aktiv.
            self._callsign_menu = menu
            menu.aboutToHide.connect(lambda: setattr(self, "_callsign_menu", None))
            menu.popup(QCursor.pos())
            return

        if value.startswith(("http://", "https://")):
            QDesktopServices.openUrl(QUrl(value))

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
            if self._room_from_block(b) in rooms
            or self._is_all_target(b)
            or self._private_participants(b) is not None
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
        # Die Karten sind im Dashboard und in der klassischen Ansicht getrennt.
        # Deshalb darf ein fehlendes klassisches map_view niemals verhindern,
        # dass das Dashboard seine Marker bekommt.
        self._map_pending_stations = list(stations or [])

        classic_available = (
            QWebEngineView is not None
            and isinstance(getattr(self, "map_view", None), QWebEngineView)
        )
        if classic_available and self._map_ready:
            import json
            station_json = json.dumps(self._map_pending_stations, ensure_ascii=False)
            self.map_view.page().runJavaScript(
                f"if (typeof window.updateStations === 'function') window.updateStations({station_json});"
            )

        if hasattr(self, "dashboard_map_view"):
            self._push_dashboard_map_stations(self._map_pending_stations)

    def _update_map(self):
        # Classic and Dashboard use separate WebEngine map views.  In Dashboard
        # mode the classic map view may not exist, so do not abort just because
        # map_view is absent; the dashboard map must receive the same station
        # data as the classic map.
        classic_map_available = (
            QWebEngineView is not None
            and isinstance(getattr(self, "map_view", None), QWebEngineView)
        )
        dashboard_map_available = (
            QWebEngineView is not None
            and isinstance(getattr(self, "dashboard_map_view", None), QWebEngineView)
        )
        if not classic_map_available and not dashboard_map_available:
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
    def connect_mesh(self, automatic=False):
        """Connect to the WebService; after a user connection, auto-reconnect is armed.

        The connection handler is shared by both layouts.  Rebuilding the
        Dashboard/classic widgets must never leave the classic Connect button
        in a stale disabled state.
        """
        # A manual click explicitly enables automatic recovery.  Automatic
        # retries do not change this flag, so a transient network/node failure
        # cannot permanently disable the connection.
        if not automatic:
            self.auto_reconnect_enabled = True

        ip = self.ip_input.text().strip().rstrip("/")
        if not ip:
            self.auto_reconnect_enabled = False
            self.status.setText(ui_text("Fehler: Keine Hotspot-IP eingetragen"))
            return

        if self.reconnect_in_progress:
            return

        self.reconnect_in_progress = True
        try:
            self.mesh = MeshCom(ip)
            if automatic:
                self.status.setText(ui_text("Verbindung verloren – verbinde erneut …"))
            else:
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
            self._set_connection_status(False)
            # IMPORTANT: Do not clear auto_reconnect_enabled here.  A failed
            # request is a lost connection, not a user-requested disconnect.
            if self.auto_reconnect_enabled:
                self.connect_button.setEnabled(False)
                self.disconnect_button.setEnabled(True)
                self.status.setText(ui_text(f"Verbindung verloren – neuer Versuch: {exc}"))
            else:
                self.connect_button.setEnabled(True)
                self.disconnect_button.setEnabled(False)
                self.status.setText(ui_text(f"Verbindung fehlgeschlagen: {exc}"))
        finally:
            self.reconnect_in_progress = False

    def disconnect_mesh(self):
        """Manually disconnect and permanently cancel automatic reconnect."""
        self.auto_reconnect_enabled = False
        self.connected = False
        self.reconnect_in_progress = False
        self._set_connection_status(False)
        # Bewusstes manuelles Trennen beendet die aktuelle Session.
        # Beim nächsten manuellen Verbinden startet die Onlinezeit wieder bei 00:00:00.
        self._reset_connection_duration()
        self._update_connection_label()
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.status.setText(ui_text("Vom MeshCom-WebService getrennt"))
        self._dashboard_sync_header()

    # ---------- Refresh ----------
    def update_messages(self):
        if not self.connected:
            # The normal 5-second refresh timer also acts as the reconnect
            # timer.  Once the user has connected, a lost WebService
            # connection is recovered automatically.  Manual "Trennen" clears
            # auto_reconnect_enabled, so it never reconnects by itself.
            if self.auto_reconnect_enabled and not self.reconnect_in_progress:
                self.connect_mesh(automatic=True)
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
                idx = self._ensure_tab(key, self._room_tab_title(room))
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

            if hasattr(self, "dashboard_sidebar"):
                self._dashboard_rebuild_private_buttons(self.dashboard_sidebar.layout())

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

            # Zusätzlich bekannte UDP-Positionsdaten werden nur bei
            # deaktiviertem Raumfilter als Nachrichtenblock in „Alle“ angezeigt.
            # Die Positionsdaten selbst bleiben unabhängig davon in
            # station_positions für die Karte erhalten. Dadurch verschwinden
            # beim aktiven Raumfilter die Koordinaten aus dem Chat, während die
            # Kartenmarker weiterhin sichtbar bleiben.
            seen_all = {self._message_identity(b) for b in all_blocks if self._message_identity(b)}
            if not self.filter_enabled.isChecked():
                for block in self.udp_position_blocks:
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
                block_timestamp = self._timestamp_from_block(block) or ""

                # In „Alle“ dürfen zwei echte Nachrichten desselben
                # Rufzeichens mit exakt demselben Text NICHT als Duplikat
                # verworfen werden, wenn sie zu unterschiedlichen Zeiten
                # gesendet wurden.
                #
                # Gleichzeitig können dieselbe Nachricht und ihre leicht
                # unterschiedlich gerenderte WebService-Variante weiterhin
                # zusammengeführt werden: gleicher Absender + gleicher Text
                # + gleicher Zeitstempel.
                if callsign and text_key:
                    duplicate = False
                    for old_callsign, old_text, old_timestamp in seen_all_pairs:
                        if old_text != text_key:
                            continue
                        if block_timestamp and old_timestamp and block_timestamp != old_timestamp:
                            continue
                        a = re.sub(r"[^A-Z0-9-]", "", callsign.upper())
                        b = re.sub(r"[^A-Z0-9-]", "", old_callsign.upper())
                        if a and b and (a in b or b in a):
                            duplicate = True
                            break
                    if duplicate:
                        continue
                    seen_all_pairs.add((callsign.upper(), text_key, block_timestamp))
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

            # Kartenmarker sind unabhängig vom Raumfilter. Die bereits
            # gespeicherten station_positions werden nach jeder Chat-/Filter-
            # Aktualisierung erneut an Classic und Dashboard gepusht.
            self._update_map()

            if self.filter_enabled.isChecked():
                rooms = self._rooms()
                self.status.setText(ui_text("Nachrichten aktualisiert – Filter: " + (", ".join(rooms) if rooms else "keine Räume")))
            else:
                self.status.setText(ui_text("Nachrichten aktualisiert – alle Räume"))
        except Exception as exc:
            self.connected = False
            self._set_connection_status(False)
            # Do not interpret a temporary HTTP/network error as a manual
            # disconnect.  The next 5-second timer tick will reconnect.
            if self.auto_reconnect_enabled:
                self.connect_button.setEnabled(False)
                self.disconnect_button.setEnabled(True)
                self.status.setText(ui_text(f"Verbindung verloren – verbinde erneut … ({exc})"))
            else:
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
            # Dashboard exakt wie die klassische Ansicht behandeln:
            # Die Bubble-Widgets werden nur neu aufgebaut, wenn sich der
            # sichtbare Inhalt tatsächlich geändert hat. Ein regelmäßiger
            # Refresh mit identischen Nachrichten darf die Blasen und damit
            # auch die Scrollposition nicht neu erzeugen.
            if (old_digest != digest and
                    getattr(self, "dashboard_current_key", None) == key and
                    hasattr(self, "dashboard_chat_view")):
                self.dashboard_chat_view.set_bubbles(getattr(view, "_bubble_items", unique))
                if hasattr(self, "dashboard_chat_title"):
                    self.dashboard_chat_title.setText(
                        f"💬 Raum #{key[1]}" if key[0] == "room" else f"👤 Privat – {key[1]}"
                    )
        else:
            rendered = self._render_blocks(blocks)
            digest = hashlib.sha1(rendered.encode("utf-8", errors="ignore")).hexdigest()
            changed = self.tab_hashes.get(key) not in ("", digest) and self.tab_hashes.get(key) != digest
            self.tab_hashes[key] = digest
            if key[0] == "all":
                view.set_all_html(rendered)
                # Dashboard shows the exact same rendered Alle chat.  This
                # deliberately reuses the established renderer instead of
                # creating a second, simplified message parser.
                # Nur wenn im Dashboard tatsächlich „Alle“ ausgewählt ist,
                # darf der regelmäßige Nachrichten-Refresh dessen Inhalt setzen.
                # Bei Raum/Privat darf ein Hintergrund-Refresh den aktuell
                # ausgewählten Chat nicht wieder auf „Alle“ zurücksetzen.
                if (hasattr(self, "dashboard_chat_view") and
                        getattr(self, "dashboard_current_key", ("all", "all")) == ("all", "all")):

                    self.dashboard_chat_view.set_all_html(rendered)
            else:
                view.setHtml(rendered)
        # ChatView keeps the current scroll position during refreshes and only
        # follows the newest message when the user was already at the bottom.
        # Die klassische Ansicht färbt einen Tab bei geändertem Inhalt rot,
        # wenn er nicht aktiv ist. Im Dashboard gilt dasselbe Prinzip für die
        # sichtbare Auswahl. Dadurch färben sich Raum-Tabs und „Alle“ auch dann
        # korrekt, wenn der klassische Tab im Hintergrund auf „Alle“ steht.
        dashboard_current = getattr(self, "dashboard_current_key", None)
        dashboard_inactive = dashboard_current is not None and dashboard_current != key
        classic_inactive = self.tabs.currentIndex() != index
        if changed and (classic_inactive or dashboard_inactive):
            self._set_tab_unread(key)
        if hasattr(self, "dashboard_sidebar"):
            self._dashboard_update_chat_button(key)

    def _export_current_chat(self):
        """Experimental export of the currently selected chat tab.

        The export reads the same session cache that feeds the chat tabs. It
        does not change message handling or the existing bubble renderer.
        """
        index = self.tabs.currentIndex()
        key = self._key_for_index(index)
        if key is None:
            self.status.setText(ui_text("Kein Chat zum Exportieren ausgewählt"))
            return

        cached_blocks = list(self.message_cache.values())
        if key[0] == "room":
            blocks = self._room_blocks(cached_blocks, key[1])
            title = self._room_tab_title(key[1])
        elif key[0] == "private":
            blocks = self._private_blocks(cached_blocks, key[1])
            title = f"Privatchat {key[1]}"
        else:
            blocks = self._filter_blocks(cached_blocks)
            title = "Alle Nachrichten"

        blocks = sorted(blocks, key=lambda b: self._timestamp_from_block(b) or "99:99:99")
        if not blocks:
            self.status.setText(ui_text("Keine Nachrichten zum Exportieren"))
            return

        default_name = "meshcom_chat_export.html"
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            ui_text("Chat exportieren"),
            default_name,
            "HTML-Datei (*.html);;Textdatei (*.txt);;CSV-Datei (*.csv)"
        )
        if not path:
            return

        try:
            suffix = Path(path).suffix.lower()
            records = []
            for block in blocks:
                plain = self._normalized_plain(block)
                if not plain:
                    continue
                time_text = self._timestamp_from_block(block) or ""
                participants = self._private_participants(block)
                sender = participants[0] if participants else ""
                target = participants[1] if participants else ""
                if not sender:
                    hm = re.search(
                        r"(?P<left>[A-Z]{1,3}[0-9][A-Z0-9]{0,3}(?:-[0-9]{1,2})?)\s*>\s*(?P<right>[A-Z0-9*\-]{1,20})",
                        plain, re.IGNORECASE)
                    if hm:
                        sender = self._normalize_callsign(hm.group("left")) or hm.group("left")
                        target = hm.group("right")
                nm = re.search(r"(?:💬\s*)?Nachricht\s*:\s*(.*)$", plain, re.IGNORECASE)
                body = nm.group(1).strip() if nm else plain
                body = re.sub(r"^(?:20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}[ T]+)?[01]\d:[0-5]\d(?::[0-5]\d)?\s*", "", body).strip()
                records.append({"time": time_text, "sender": sender or "-", "target": target or "-", "body": body})

            if suffix == ".txt":
                lines = [f"MeshCom-Guru Chat-Export", f"{title}", "", *[
                    f"{r['time']}  {r['sender']}  -> {r['target']}  {r['body']}" for r in records
                ]]
                Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
            elif suffix == ".csv":
                import csv
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    writer = csv.writer(fh, delimiter=";")
                    writer.writerow(["Datum/Zeit", "Rufzeichen", "Ziel", "Nachricht"])
                    for r in records:
                        writer.writerow([r["time"], r["sender"], r["target"], r["body"]])
            else:
                rows = []
                for r in records:
                    body_html = self._make_clickable(self._chat_escape(r["body"]))
                    rows.append(
                        "<article class='message'>"
                        f"<div class='meta'>{self._chat_escape(r['time'])} &nbsp; <b>{self._chat_escape(r['sender'])}</b> &nbsp;→&nbsp; {self._chat_escape(r['target'])}</div>"
                        f"<div class='body'>{body_html}</div>"
                        "</article>"
                    )
                document = (
                    "<!doctype html><html><head><meta charset='utf-8'>"
                    f"<title>{self._chat_escape(title)}</title>"
                    "<style>body{font-family:sans-serif;background:#101722;color:#e6edf3;margin:24px}"
                    ".message{max-width:900px;margin:0 auto 12px;padding:12px 16px;border-radius:12px;background:#1b2635}"
                    ".meta{font-size:13px;color:#aeb9c7;margin-bottom:7px}.body{font-size:15px;white-space:pre-wrap}"
                    f"a{{color:{self.chat_link_color};}}</style></head><body>"
                    f"<h2>{self._chat_escape(title)}</h2>{''.join(rows)}</body></html>"
                )
                Path(path).write_text(document, encoding="utf-8")

            self.status.setText(ui_text(f"Chat exportiert: {path}"))
        except Exception as exc:
            self.status.setText(ui_text(f"Export fehlgeschlagen: {exc}"))

    # ---------- Send ----------
    def _monitor_add_local_message(self, text, target):
        """Store every successful local send in the monitor immediately.

        This is deliberately independent of the UDP echo: the monitor must
        show that the WebService accepted the send even when the packet does
        not later return over UDP/MH. A paused monitor still stores the row;
        it becomes visible as soon as the monitor is resumed.
        """
        if not hasattr(self, "monitor_rows"):
            self.monitor_rows = []
        clean_text = str(text or "").strip()
        clean_target = str(target or "-").strip() or "-"
        self.monitor_rows.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": "MSG",
            "src": str(self.own_callsign or "-").strip() or "-",
            "dst": clean_target,
            "rssi": "-",
            "snr": "-",
            "detail": clean_text,
            "_local_send": True,
            "_text": clean_text,
            "_source": "local_send",
        })
        self.monitor_rows = self.monitor_rows[-1000:]
        # Do not let the paused state prevent the send from being recorded.
        if not getattr(self, "monitor_paused", False):
            self._render_monitor()

    def send(self):
        if not self.connected:
            self.status.setText(ui_text("Bitte zuerst mit dem MeshCom-WebService verbinden"))
            return
        text = self.message_input.text().strip()

        # In der klassischen Ansicht ist der aktuell sichtbare Tab die
        # maßgebliche Zielauswahl. Nach einem Dashboard -> Klassisch Wechsel
        # kann target_input noch einen alten Wert enthalten (z. B. einen
        # Filterraum). Deshalb beim Senden immer den tatsächlich ausgewählten
        # Chat-Tab verwenden.
        target = self.target_input.text().strip()
        if getattr(self, "layout_mode", "classic") == "classic":
            try:
                current_index = self.tabs.currentIndex()
                current_key = self._key_for_index(current_index)
                if current_key and current_key[0] in {"room", "private"}:
                    target = str(current_key[1]).strip()
                    self.target_input.setText(target)
            except Exception:
                pass

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
            # Auch den Undo-/Redo-Verlauf löschen, damit keine zuvor verwendeten
            # Emojis oder Schnelltexte durch Eingabe-/IME-Wiederherstellung
            # erneut auftauchen können.
            if hasattr(self.message_input, "clearUndo"):
                self.message_input.clearUndo()
            if hasattr(self, "dashboard_message_input"):
                self.dashboard_message_input.clear()
                if hasattr(self.dashboard_message_input, "clearUndo"):
                    self.dashboard_message_input.clearUndo()

            # Bei leerem Ziel bleibt der Tab „Alle“ aktiv.
            # Wichtig: Kein künstlicher Privat-Tab für ein leeres Ziel
            # und kein sofortiger Refresh, der das aktuelle Chatfenster
            # mit einer leeren Serverantwort überschreiben könnte.
            if target:
                if target.isdigit():
                    key = ("room", target)
                    idx = self._ensure_tab(key, self._room_tab_title(target))
                else:
                    key = ("private", target.upper())
                    # Wurde dieser Privat-Tab vorher bewusst geschlossen und
                    # wird jetzt wieder an dasselbe Ziel gesendet, soll der
                    # Tab sofort wieder erscheinen. Der alte Schließ-Marker
                    # darf den erneuten Versand nicht blockieren.
                    self.closed_private.pop(target.upper(), None)
                    idx = self._ensure_tab(key, target.upper())
                    if hasattr(self, "dashboard_sidebar"):
                        self._dashboard_rebuild_private_buttons(self.dashboard_sidebar.layout())
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
            if not getattr(self, "_skip_settings_write_on_close", False):
                self._write_settings()
        finally:
            event.accept()

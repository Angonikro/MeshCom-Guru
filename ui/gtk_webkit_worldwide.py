"""Embedded ÖVSV Worldwide page using WebKitGTK instead of QtWebEngine.

The GTK/WebKit window is embedded into the Qt application through its native
X11 window handle. This keeps the real HTML/JavaScript page in MeshCom-Guru
while avoiding a Chromium renderer for the Worldwide view.
"""

import os
import sys

# Allow PyGObject installed by Debian to be used from a normal Python venv.
for _p in ("/usr/lib/python3/dist-packages", "/usr/lib/aarch64-linux-gnu/python3/dist-packages", "/usr/lib/x86_64-linux-gnu/python3/dist-packages"):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.append(_p)

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QWindow, QDesktopServices
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


try:
    import gi
    gi.require_version("Gtk", "3.0")
    try:
        gi.require_version("WebKit2", "4.1")
    except ValueError:
        gi.require_version("WebKit2", "4.0")
    gi.require_version("GdkX11", "3.0")
    from gi.repository import Gtk, WebKit2, GdkX11, Gio
    GTK_WEBKIT_AVAILABLE = True
except Exception:
    Gtk = WebKit2 = GdkX11 = Gio = None
    GTK_WEBKIT_AVAILABLE = False


class GtkWebKitWorldwide(QWidget):
    """Real ÖVSV HTML page embedded in the Qt UI using WebKitGTK."""

    URL = "https://meshcom.oevsv.at/#"

    def __init__(self, url=None, parent=None):
        super().__init__(parent)
        self.setObjectName("GtkWebKitWorldwide")
        self._gtk_window = None
        self._webview = None
        self._foreign_window = None
        self._container = None
        self._gtk_ready = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if not GTK_WEBKIT_AVAILABLE:
            label = QLabel(
                "Weltweit benötigt WebKitGTK.\n\n"
                "Bitte ./install_webkitgtk.sh ausführen und MeshCom-Guru neu starten."
            )
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            return

        try:
            # Gtk can coexist with Qt on X11 as long as its event queue is
            # iterated from the Qt event loop. Do not start a second main loop.
            try:
                Gtk.init_check([])
            except Exception:
                pass

            self._gtk_window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
            self._gtk_window.set_decorated(False)
            self._gtk_window.set_resizable(True)
            self._gtk_window.set_default_size(800, 500)

            self._webview = WebKit2.WebView()
            self._webview.set_hexpand(True)
            self._webview.set_vexpand(True)
            self._webview.connect("load-changed", self._on_load_changed)
            # External Internet links from the embedded ÖVSV page must open
            # in the normal system browser instead of navigating the embedded
            # WebKit view away from the Worldwide page.
            self._webview.connect("decide-policy", self._on_decide_policy)
            self._gtk_window.add(self._webview)
            self._gtk_window.show_all()

            # Realize the GTK window before asking GDK/X11 for its native XID.
            for _ in range(20):
                while Gtk.events_pending():
                    Gtk.main_iteration_do(False)
                if self._gtk_window.get_window() is not None:
                    break

            gdk_window = self._gtk_window.get_window()
            if gdk_window is None:
                raise RuntimeError("WebKitGTK-Fenster konnte nicht realisiert werden")

            xid = GdkX11.X11Window.get_xid(gdk_window)
            self._foreign_window = QWindow.fromWinId(int(xid))
            self._foreign_window.setFlags(Qt.WindowType.FramelessWindowHint)
            self._container = QWidget.createWindowContainer(self._foreign_window, self)
            self._container.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self._container.setMinimumSize(1, 1)
            layout.addWidget(self._container, 1)
            self._gtk_ready = True

            # The X11 foreign-window container can otherwise receive its first
            # real geometry only after the user moves the splitter.  Apply the
            # current size immediately and once again after the Qt layout pass.
            self._sync_foreign_geometry()
            QTimer.singleShot(0, self._sync_foreign_geometry)
            QTimer.singleShot(150, self._sync_foreign_geometry)
            QTimer.singleShot(500, self._sync_foreign_geometry)
            QTimer.singleShot(1000, self._sync_foreign_geometry)

            # Keep GTK's event queue moving without starting gtk_main().
            self._gtk_timer = QTimer(self)
            self._gtk_timer.timeout.connect(self._iterate_gtk)
            self._gtk_timer.start(10)

            self._webview.load_uri(url or self.URL)
        except Exception as exc:
            self._gtk_ready = False
            fallback = QLabel(f"Weltweit konnte mit WebKitGTK nicht gestartet werden:\n{exc}")
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(fallback)

    def _sync_foreign_geometry(self):
        if not self._gtk_ready or self._container is None:
            return
        try:
            size = self._container.size()
            if size.width() > 0 and size.height() > 0:
                if self._foreign_window is not None:
                    self._foreign_window.resize(size.width(), size.height())
                if self._gtk_window is not None:
                    self._gtk_window.resize(size.width(), size.height())
        except Exception:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self._sync_foreign_geometry)

    def _iterate_gtk(self):
        if not GTK_WEBKIT_AVAILABLE:
            return
        try:
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
        except Exception:
            pass


    def _on_decide_policy(self, webview, decision, decision_type):
        """Open user-clicked external HTTP(S) links in the system browser."""
        try:
            if decision_type not in (
                WebKit2.PolicyDecisionType.NAVIGATION_ACTION,
                WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION,
            ):
                return False

            navigation_action = decision.get_navigation_action()
            if navigation_action is None:
                return False

            # Only intercept an actual user click/gesture. Internal redirects
            # and the page's own navigation are left inside WebKit.
            if hasattr(navigation_action, "is_user_gesture") and not navigation_action.is_user_gesture():
                return False

            request = navigation_action.get_request()
            uri = request.get_uri() if request is not None else ""
            if not uri:
                return False

            lower_uri = uri.lower()
            if not lower_uri.startswith(("http://", "https://")):
                return False

            # Links belonging to the embedded ÖVSV page stay embedded.
            try:
                from urllib.parse import urlparse
                host = (urlparse(uri).hostname or "").lower()
                if host in ("meshcom.oevsv.at", "www.meshcom.oevsv.at"):
                    return False
            except Exception:
                pass

            # Prevent the embedded page from following the external URL and
            # hand it to the user's configured desktop browser instead.
            decision.ignore()
            try:
                QDesktopServices.openUrl(QUrl(uri))
            except Exception:
                if Gio is not None:
                    try:
                        Gio.AppInfo.launch_default_for_uri(uri, None)
                    except Exception:
                        pass
            return True
        except Exception:
            return False

    def _on_load_changed(self, webview, load_event):
        if not GTK_WEBKIT_AVAILABLE or WebKit2 is None:
            return
        try:
            if load_event == WebKit2.LoadEvent.FINISHED:
                # The ÖVSV site keeps the top-level hash while loading
                # activity.html dynamically. Click ACTIVITY just like a user.
                script = """
                (function(){
                    const els = Array.from(document.querySelectorAll('a,button,[role=button],input'));
                    const el = els.find(e => ((e.innerText||e.textContent||e.value||e.title||'')+'').trim().toUpperCase() === 'ACTIVITY');
                    if (el) { el.click(); return true; }
                    const loose = els.find(e => ((e.innerText||e.textContent||e.value||e.title||'')+'').trim().toUpperCase().includes('ACTIVITY'));
                    if (loose) { loose.click(); return true; }
                    return false;
                })();
                """
                self._webview.run_javascript(script, None, None, None)
        except Exception:
            pass

    def closeEvent(self, event):
        try:
            if hasattr(self, "_gtk_timer"):
                self._gtk_timer.stop()
            if self._gtk_window is not None:
                self._gtk_window.hide()
                self._gtk_window.destroy()
        except Exception:
            pass
        super().closeEvent(event)

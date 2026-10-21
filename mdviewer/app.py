"""MD Viewer TY — Windows için okuma odaklı Markdown görüntüleyici."""
from __future__ import annotations

import ctypes
import json
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.parse import unquote

import webview

from mdviewer import APP_ID, APP_NAME, __version__, updater
from mdviewer.renderer import render
from mdviewer.storage import Store

if getattr(sys, "frozen", False):
    UI_DIR = Path(sys._MEIPASS) / "mdviewer" / "ui"
else:
    UI_DIR = Path(__file__).parent / "ui"

MD_EXTENSIONS = (".md", ".markdown", ".mdown", ".mkd", ".mdx", ".txt")
THEME_BACKGROUNDS = {"paper": "#FBF8F2", "sepia": "#F3EAD7", "night": "#17181C", "ink": "#000000"}


class Api:
    """JavaScript tarafına `window.pywebview.api` olarak açılan köprü."""

    def __init__(self, store: Store, initial: str | None) -> None:
        self._store = store
        self._window: webview.Window | None = None
        self._initial = initial
        self._current: str | None = None
        self._mtime: float = 0
        self._update: dict | None = None

    # --- belge yükleme -------------------------------------------------
    def _document(self, path: str) -> dict:
        path = os.path.abspath(path)
        p = Path(path)
        try:
            raw = p.read_bytes()
        except OSError as exc:
            return {"error": f"Dosya açılamadı: {exc.strerror or exc}"}
        text = raw.decode("utf-8-sig", errors="replace")

        doc = render(text, p.parent)
        self._current = path
        self._mtime = p.stat().st_mtime
        doc.update({
            "path": path,
            "name": p.name,
            "folder": str(p.parent),
            "title": doc["title"] or p.stem,
            "mtime": self._mtime,
            "position": self._store.position(path),
        })
        return doc

    def load(self, path: str) -> dict:
        doc = self._document(path)
        if "error" not in doc:
            self._store.touch_recent(doc["path"], doc["title"], doc["minutes"])
        return doc

    def open_dialog(self) -> dict | None:
        dialog = getattr(getattr(webview, "FileDialog", None), "OPEN", None) or webview.OPEN_DIALOG
        start = os.path.dirname(self._current) if self._current else ""
        result = self._window.create_file_dialog(
            dialog,
            directory=start,
            file_types=("Markdown (*.md;*.markdown;*.mdown;*.mkd;*.mdx;*.txt)", "Tüm dosyalar (*.*)"),
        )
        if not result:
            return None
        return self.load(result[0])

    def check_changed(self) -> dict | None:
        if not self._current:
            return None
        try:
            mtime = os.stat(self._current).st_mtime
        except OSError:
            return None
        if mtime == self._mtime:
            return None
        return self._document(self._current)

    def follow_link(self, href: str) -> dict | None:
        """Belgedeki bağlantıyı açar: yerel .md ise içeride, değilse tarayıcıda."""
        if href.startswith(("http://", "https://", "mailto:")):
            webbrowser.open(href)
            return None
        target = unquote(href.split("#")[0])
        if self._current and not os.path.isabs(target):
            target = os.path.join(os.path.dirname(self._current), target)
        if os.path.isfile(target):
            if target.lower().endswith(MD_EXTENSIONS):
                return self.load(target)
            os.startfile(target)
        return None

    # --- durum ---------------------------------------------------------
    def get_state(self) -> dict:
        initial = None
        if self._initial:
            initial = self.load(self._initial)
            self._initial = None
        return {"settings": self._store.settings, "recent": self._store.recent(), "initial": initial}

    def get_recent(self) -> list[dict]:
        return self._store.recent()

    def remove_recent(self, path: str) -> list[dict]:
        self._store.remove_recent(path)
        return self._store.recent()

    def save_settings(self, settings: dict) -> None:
        self._store.set_settings(settings)

    def save_position(self, path: str, ratio: float) -> None:
        self._store.set_position(path, max(0.0, min(1.0, float(ratio))))

    def close_document(self) -> None:
        self._current = None

    def reveal(self) -> None:
        if self._current:
            os.system(f'explorer /select,"{self._current}"')

    def toggle_fullscreen(self) -> None:
        self._window.toggle_fullscreen()

    def open_url(self, url: str) -> None:
        if url.startswith("https://"):
            webbrowser.open(url)

    # --- güncelleme ----------------------------------------------------
    def get_info(self) -> dict:
        return {"name": APP_NAME, "version": __version__, "canSelfUpdate": updater.can_self_update(),
                "releases": updater.RELEASES_PAGE}

    def check_update(self) -> dict:
        try:
            info = updater.check()
        except updater.UpdateError as exc:
            return {"error": str(exc)}
        if info.get("available"):
            self._update = info
        return info

    def install_update(self) -> None:
        """İndirmeyi arka planda başlatır; ilerleme JS'ye `MDV.updateProgress` ile iletilir."""
        info = self._update
        if not info:
            return
        if not updater.can_self_update():
            webbrowser.open(info["page"])
            return

        def push(fn: str, payload) -> None:
            self._window.evaluate_js(f"MDV.{fn}({json.dumps(payload, ensure_ascii=False)})")

        def worker() -> None:
            last = [0.0]

            def progress(p: float) -> None:
                if p - last[0] >= 0.02 or p >= 1:
                    last[0] = p
                    push("updateProgress", p)

            try:
                setup = updater.download(info, progress)
                push("updateProgress", 1)
                updater.launch_installer(setup)
            except updater.UpdateError as exc:
                push("updateFailed", str(exc))
                return
            except Exception as exc:  # beklenmeyen ağ/disk hatası
                push("updateFailed", f"Güncelleme indirilemedi: {exc}")
                return
            time.sleep(0.6)
            self._window.destroy()

        threading.Thread(target=worker, daemon=True).start()


def _bind_drop(window: webview.Window, api: Api) -> None:
    from webview.dom import DOMEventHandler

    def on_drop(event: dict) -> None:
        files = event.get("dataTransfer", {}).get("files", [])
        paths = [f.get("pywebviewFullPath") for f in files if f.get("pywebviewFullPath")]
        if not paths:
            return
        doc = api.load(paths[0])
        window.evaluate_js(f"MDV.show({json.dumps(doc, ensure_ascii=False)})")

    window.dom.document.events.drop += DOMEventHandler(on_drop, True, True)


def _set_app_user_model_id() -> None:
    # Görev çubuğunda python.exe yerine uygulamanın kendi kimliği ve ikonu görünsün.
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except (AttributeError, OSError):
        pass


def main() -> None:
    _set_app_user_model_id()
    initial = next((a for a in sys.argv[1:] if os.path.isfile(a)), None)
    store = Store()
    api = Api(store, initial)
    theme = store.settings.get("theme", "paper")

    window = webview.create_window(
        APP_NAME,
        str(UI_DIR / "index.html"),
        js_api=api,
        width=1240,
        height=860,
        min_size=(560, 480),
        background_color=THEME_BACKGROUNDS.get(theme, "#FBF8F2"),
        text_select=True,
    )
    api._window = window
    window.events.loaded += lambda: _bind_drop(window, api)
    webview.start(private_mode=True, debug="--debug" in sys.argv)


if __name__ == "__main__":
    main()

"""GitHub Releases üzerinden güncelleme denetimi ve kurulumu.

Her sürümde iki dosya yayımlanır:
  MDViewerTY-Setup-<sürüm>.exe  — kurulum dosyası
  SHA256SUMS.txt                — tüm dosyaların SHA-256 özetleri
İndirilen kurulum dosyası, özet dosyasıyla doğrulanmadan çalıştırılmaz.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Callable

from mdviewer import APP_NAME, GITHUB_REPO, __version__

API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{GITHUB_REPO}/releases"
USER_AGENT = f"MDViewerTY/{__version__} (+https://github.com/{GITHUB_REPO})"
SETUP_PATTERN = re.compile(r"^MDViewerTY-Setup-.*\.exe$", re.I)


class UpdateError(Exception):
    pass


def parse_version(text: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", text.split("-")[0])
    return tuple(int(n) for n in nums[:3]) + (0,) * (3 - len(nums[:3]))


def is_newer(latest: str, current: str = __version__) -> bool:
    return parse_version(latest) > parse_version(current)


def _get(url: str, timeout: float = 10) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def check() -> dict:
    """En son sürümü sorgular. Yeni sürüm yoksa {"available": False} döner."""
    try:
        data = json.loads(_get(API_LATEST))
    except Exception as exc:  # ağ yok, oran sınırı vb.
        raise UpdateError(f"Güncelleme sunucusuna ulaşılamadı ({exc.__class__.__name__}).") from exc

    latest = data.get("tag_name", "").lstrip("vV")
    if not latest or not is_newer(latest):
        return {"available": False, "current": __version__, "latest": latest or __version__}

    assets = {a["name"]: a for a in data.get("assets", [])}
    setup = next((a for name, a in assets.items() if SETUP_PATTERN.match(name)), None)
    sums = assets.get("SHA256SUMS.txt")
    notes = (data.get("body") or "").strip()
    return {
        "available": True,
        "current": __version__,
        "latest": latest,
        "notes": notes[:1500],
        "page": data.get("html_url") or RELEASES_PAGE,
        "setup_url": setup["browser_download_url"] if setup else None,
        "setup_name": setup["name"] if setup else None,
        "setup_size": setup["size"] if setup else 0,
        "sums_url": sums["browser_download_url"] if sums else None,
    }


def _expected_hash(sums_url: str, name: str) -> str:
    text = _get(sums_url).decode("utf-8", errors="replace")
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) == 2 and parts[1].lstrip("*") == name:
            return parts[0].lower()
    raise UpdateError("Kurulum dosyasının doğrulama özeti bulunamadı.")


def download(info: dict, progress: Callable[[float], None]) -> Path:
    if not info.get("setup_url") or not info.get("sums_url"):
        raise UpdateError("Bu sürümde otomatik kurulum dosyası yok; sürüm sayfasından indirebilirsin.")

    expected = _expected_hash(info["sums_url"], info["setup_name"])
    target_dir = Path(tempfile.gettempdir()) / "MDViewerTY-update"
    target_dir.mkdir(exist_ok=True)
    target = target_dir / info["setup_name"]

    req = urllib.request.Request(info["setup_url"], headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    with urllib.request.urlopen(req, timeout=30) as resp, open(target, "wb") as fh:
        total = int(resp.headers.get("Content-Length") or info.get("setup_size") or 0)
        done = 0
        while chunk := resp.read(256 * 1024):
            fh.write(chunk)
            digest.update(chunk)
            done += len(chunk)
            if total:
                progress(min(done / total, 1.0))

    if digest.hexdigest().lower() != expected:
        target.unlink(missing_ok=True)
        raise UpdateError("İndirilen dosya doğrulanamadı (SHA-256 uyuşmuyor). Güncelleme iptal edildi.")
    return target


def install_mode_flag() -> str:
    """Mevcut kurulum tüm kullanıcılar içinse güncelleme de öyle kurulmalı."""
    exe = os.path.normcase(sys.executable)
    program_files = [os.environ.get(k, "") for k in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432")]
    if any(pf and exe.startswith(os.path.normcase(pf)) for pf in program_files):
        return "/ALLUSERS"
    return "/CURRENTUSER"


def launch_installer(setup: Path) -> None:
    """Kurulumu sessiz başlatır; kurulum bitince uygulama yeniden açılır (/UPDATE=1)."""
    args = [str(setup), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS",
            install_mode_flag(), "/UPDATE=1"]
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen(args, close_fds=True, creationflags=flags)


def can_self_update() -> bool:
    return bool(getattr(sys, "frozen", False))


__all__ = ["APP_NAME", "RELEASES_PAGE", "UpdateError", "check", "download", "launch_installer", "can_self_update", "is_newer"]

"""MD Viewer TY yayın derlemesi.

Adımlar: sürüm bilgisi -> PyInstaller -> taşınabilir zip -> Inno Setup kurulumu -> SHA256SUMS.txt
Kullanım: python tools/build.py [--skip-installer]
Çıktılar dist/ altında toplanır.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"
EXE_NAME = "MDViewerTY"


def version() -> str:
    text = (ROOT / "mdviewer" / "__init__.py").read_text(encoding="utf-8")
    return re.search(r'__version__\s*=\s*"([^"]+)"', text).group(1)


def write_version_file(ver: str) -> Path:
    nums = (list(map(int, re.findall(r"\d+", ver))) + [0, 0, 0, 0])[:4]
    tup = tuple(nums)
    BUILD.mkdir(exist_ok=True)
    path = BUILD / "version_info.txt"
    path.write_text(f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(filevers={tup}, prodvers={tup}, mask=0x3f, flags=0x0, OS=0x40004,
                    fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('041F04B0', [
      StringStruct('CompanyName', 'Talha Yaşar'),
      StringStruct('FileDescription', 'MD Viewer TY'),
      StringStruct('FileVersion', '{ver}'),
      StringStruct('InternalName', '{EXE_NAME}'),
      StringStruct('LegalCopyright', '© Talha Yaşar. MIT Lisansı.'),
      StringStruct('OriginalFilename', '{EXE_NAME}.exe'),
      StringStruct('ProductName', 'MD Viewer TY'),
      StringStruct('ProductVersion', '{ver}')])]),
    VarFileInfo([VarStruct('Translation', [0x041F, 1200])])
  ]
)
""", encoding="utf-8")
    return path


def run(cmd: list[str]) -> None:
    print("»", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def pyinstaller(ver: str) -> Path:
    vfile = write_version_file(ver)
    sep = os.pathsep
    run([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
        "--name", EXE_NAME,
        "--icon", str(ROOT / "assets" / "icon.ico"),
        "--version-file", str(vfile),
        "--add-data", f"{ROOT / 'mdviewer' / 'ui'}{sep}mdviewer/ui",
        "--collect-submodules", "pygments",
        "--collect-submodules", "mdit_py_plugins",
        "--distpath", str(DIST), "--workpath", str(BUILD / "pyinstaller"), "--specpath", str(BUILD),
        str(ROOT / "MDViewerTY.pyw"),
    ])
    return DIST / EXE_NAME


def portable_zip(app_dir: Path, ver: str) -> Path:
    out = DIST / f"{EXE_NAME}-{ver}-portable.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in app_dir.rglob("*"):
            z.write(f, Path(EXE_NAME) / f.relative_to(app_dir))
    return out


def find_iscc() -> str:
    candidates = [
        shutil.which("iscc"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    for c in candidates:
        if c and Path(c).is_file():
            return c
    sys.exit("Inno Setup 6 (ISCC.exe) bulunamadı. https://jrsoftware.org/isdl.php adresinden kurabilirsin.")


def installer(ver: str) -> Path:
    run([find_iscc(), f"/DAppVersion={ver}", str(ROOT / "installer" / "MDViewerTY.iss")])
    return DIST / f"{EXE_NAME}-Setup-{ver}.exe"


def checksums(files: list[Path]) -> Path:
    out = DIST / "SHA256SUMS.txt"
    lines = [f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}" for f in files]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ver = version()
    print(f"MD Viewer TY {ver} derleniyor", flush=True)
    if DIST.exists():
        shutil.rmtree(DIST)
    app_dir = pyinstaller(ver)
    artifacts = [portable_zip(app_dir, ver)]
    if "--skip-installer" not in sys.argv:
        artifacts.insert(0, installer(ver))
    sums = checksums(artifacts)
    print("\nHazır:")
    for f in [*artifacts, sums]:
        print(f"  {f.relative_to(ROOT)}  ({f.stat().st_size / 1_048_576:.1f} MB)")


if __name__ == "__main__":
    main()

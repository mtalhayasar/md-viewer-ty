"""CHANGELOG.md içinden verilen sürümün bölümünü yazdırır ya da dosyaya yazar.

Kullanım: python tools/release_notes.py 1.0.0 [çıktı.md]
"""
import re
import sys
from pathlib import Path

version = sys.argv[1].lstrip("vV")
text = (Path(__file__).resolve().parent.parent / "CHANGELOG.md").read_text(encoding="utf-8")
match = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)", text, flags=re.M | re.S)
if not match:
    sys.exit(f"CHANGELOG.md içinde {version} bölümü yok.")
notes = match.group(1).strip() + "\n"
if len(sys.argv) > 2:
    Path(sys.argv[2]).write_text(notes, encoding="utf-8")
else:
    sys.stdout.reconfigure(encoding="utf-8")
    print(notes, end="")

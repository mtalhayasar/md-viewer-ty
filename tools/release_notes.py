"""CHANGELOG.md içinden verilen sürümün bölümünü yazdırır: python tools/release_notes.py 1.0.0"""
import re
import sys
from pathlib import Path

version = sys.argv[1].lstrip("vV")
text = (Path(__file__).resolve().parent.parent / "CHANGELOG.md").read_text(encoding="utf-8")
match = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)", text, flags=re.M | re.S)
if not match:
    sys.exit(f"CHANGELOG.md içinde {version} bölümü yok.")
sys.stdout.reconfigure(encoding="utf-8")
print(match.group(1).strip())

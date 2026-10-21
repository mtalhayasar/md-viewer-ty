"""Markdown -> HTML dönüşümü, içindekiler ve okuma istatistikleri."""
from __future__ import annotations

import base64
import html
import mimetypes
import re
from pathlib import Path
from urllib.parse import unquote

from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from pygments import highlight as pyg_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

WORDS_PER_MINUTE = 200
MAX_INLINE_IMAGE = 15 * 1024 * 1024

_TR = str.maketrans("çğıöşüÇĞİÖŞÜâîûÂÎÛ", "cgiosuCGIOSUaiuAIU")
_FORMATTER = HtmlFormatter(nowrap=True)

CALLOUTS = {
    "NOTE": "Not",
    "TIP": "İpucu",
    "IMPORTANT": "Önemli",
    "WARNING": "Uyarı",
    "CAUTION": "Dikkat",
}


def slugify(text: str) -> str:
    text = text.translate(_TR).lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_]+", "-", text).strip("-") or "bolum"


def _highlight(code: str, lang: str, _attrs: str) -> str:
    lang = (lang or "").strip().lower()
    lexer = None
    if lang:
        try:
            lexer = get_lexer_by_name(lang)
        except ClassNotFound:
            lexer = None
    body = pyg_highlight(code, lexer, _FORMATTER) if lexer else html.escape(code)
    return f'<pre class="code" data-lang="{html.escape(lang)}"><code>{body}</code></pre>'


def _build_parser() -> MarkdownIt:
    md = MarkdownIt(
        "gfm-like",
        {"html": True, "linkify": True, "typographer": True, "highlight": _highlight},
    )
    md.use(front_matter_plugin)
    md.use(footnote_plugin)
    md.use(deflist_plugin)
    md.use(tasklists_plugin)
    md.use(anchors_plugin, min_level=1, max_level=4, slug_func=slugify)
    return md


_MD = _build_parser()


def _sanitize(out: str) -> str:
    # Belge içine gömülü betiklerin uygulama köprüsüne erişmesini engelle.
    out = re.sub(r"<script\b[\s\S]*?</script\s*>", "", out, flags=re.I)
    out = re.sub(r"<(iframe|object|embed)\b[\s\S]*?(</\1\s*>|/?>)", "", out, flags=re.I)
    out = re.sub(r"\son\w+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", "", out, flags=re.I)
    return re.sub(r"(href|src)\s*=\s*([\"'])\s*javascript:[^\"']*\2", r'\1="#"', out, flags=re.I)


def _callouts(out: str) -> str:
    def repl(m: re.Match) -> str:
        kind = m.group(1).upper()
        label = CALLOUTS[kind]
        return (
            f'<blockquote class="callout callout-{kind.lower()}">'
            f'<p class="callout-title">{label}</p><p>'
        )

    pattern = r"<blockquote>\s*<p>\[!(" + "|".join(CALLOUTS) + r")\]\s*"
    out = re.sub(pattern, repl, out, flags=re.I)
    # Başlık satırından sonra boş kalan paragrafı temizle.
    return out.replace('</p><p></p>', '</p>')


def _inline_images(out: str, base_dir: Path) -> str:
    def repl(m: re.Match) -> str:
        src = m.group(2)
        if re.match(r"^(https?:|data:|file:)", src, flags=re.I):
            return m.group(0)
        path = (base_dir / unquote(src.split("?")[0].split("#")[0])).resolve()
        try:
            if not path.is_file() or path.stat().st_size > MAX_INLINE_IMAGE:
                return m.group(0)
            mime = mimetypes.guess_type(path.name)[0] or "image/png"
            data = base64.b64encode(path.read_bytes()).decode("ascii")
        except OSError:
            return m.group(0)
        return f"{m.group(1)}data:{mime};base64,{data}{m.group(3)}"

    return re.sub(r'(<img\b[^>]*?\bsrc=")([^"]+)(")', repl, out, flags=re.I)


def count_words(rendered: str) -> int:
    text = re.sub(r"<pre[\s\S]*?</pre>", " ", rendered)
    text = re.sub(r"<[^>]+>", " ", text)
    return len(re.findall(r"\w+", html.unescape(text)))


def _front_matter_title(tokens) -> str | None:
    for tok in tokens:
        if tok.type == "front_matter":
            m = re.search(r"^title:\s*[\"']?(.+?)[\"']?\s*$", tok.content, flags=re.M)
            return m.group(1) if m else None
    return None


def render(text: str, base_dir: Path) -> dict:
    env: dict = {}
    tokens = _MD.parse(text, env)

    toc = []
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open" and tok.attrGet("id"):
            inline = tokens[i + 1]
            label = "".join(
                c.content for c in (inline.children or []) if c.type in ("text", "code_inline")
            ) or inline.content
            toc.append({"level": int(tok.tag[1]), "id": tok.attrGet("id"), "text": label})

    out = _MD.renderer.render(tokens, _MD.options, env)
    out = _sanitize(out)
    out = _callouts(out)
    out = _inline_images(out, base_dir)

    words = count_words(out)
    title = _front_matter_title(tokens)
    if not title:
        h1 = next((t for t in toc if t["level"] == 1), None)
        title = h1["text"] if h1 else None

    return {
        "html": out,
        "toc": toc,
        "title": title,
        "words": words,
        "minutes": max(1, round(words / WORDS_PER_MINUTE)),
    }

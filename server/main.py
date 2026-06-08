"""M2AI — Methodology-to-AI Research Portal (MVP).

Лёгкая версия: лендинг, статьи (HTML-визуализации + markdown), браузер файлов.
Полный REST + MCP по PROJECT-SPEC.md достраивается поверх позже (KAN-258).
"""
import os
import html
from pathlib import Path
from urllib.parse import quote

import markdown as md
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent.parent
CONTENT = Path(os.environ.get("CONTENT_DIR", BASE / "content"))

app = FastAPI(title="M2AI — Methodology-to-AI Research Portal", docs_url="/api-docs")

# Сырой контент: визуализации (html), книги (скачивание), json
if CONTENT.exists():
    app.mount("/content", StaticFiles(directory=str(CONTENT), html=False), name="content")

CSS = """
:root{--bg:#0f1117;--card:#171a23;--fg:#e6e8ee;--mut:#9aa3b2;--acc:#7aa2ff;--bd:#252a36}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:960px;margin:0 auto;padding:32px 20px 64px}
header.top{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;margin-bottom:8px}
header.top h1{font-size:24px;margin:0}
nav a{margin-right:18px;color:var(--mut)}nav a:hover{color:var(--fg)}
.lead{color:var(--mut);margin:8px 0 28px;max-width:680px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;margin:24px 0}
.stat{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:16px}
.stat b{display:block;font-size:26px}.stat span{color:var(--mut);font-size:13px}
.list{list-style:none;padding:0;margin:0}
.list li{background:var(--card);border:1px solid var(--bd);border-radius:10px;
padding:12px 16px;margin-bottom:10px;display:flex;justify-content:space-between;gap:12px;align-items:center}
.list li .meta{color:var(--mut);font-size:13px;white-space:nowrap}
h2{margin-top:36px;border-bottom:1px solid var(--bd);padding-bottom:8px}
.crumbs{color:var(--mut);font-size:14px;margin-bottom:16px}
.md{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:24px 28px}
.md pre{background:#0b0d12;padding:12px;border-radius:8px;overflow:auto}
.md code{background:#0b0d12;padding:1px 5px;border-radius:4px}
.md table{border-collapse:collapse}.md td,.md th{border:1px solid var(--bd);padding:6px 10px}
footer{color:var(--mut);font-size:13px;margin-top:48px;border-top:1px solid var(--bd);padding-top:16px}
"""

NAV = (
    '<nav><a href="/">Главная</a><a href="/articles">Статьи</a>'
    '<a href="/files">Файлы</a><a href="/api-docs">API</a></nav>'
)


def page(title: str, body: str) -> str:
    return (
        f"<!doctype html><html lang=ru><head><meta charset=utf-8>"
        f'<meta name=viewport content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head>"
        f'<body><div class="wrap"><header class="top"><h1>M2AI</h1>{NAV}</header>'
        f"{body}"
        f'<footer>M2AI — Methodology-to-AI Research Portal · наследие Г.П. Щедровицкого, '
        f"формальный алфавит операций мышления</footer></div></body></html>"
    )


def fsize(p: Path) -> str:
    n = p.stat().st_size
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if n < 1024 or unit == "ГБ":
            return f"{n:.0f} {unit}" if unit == "Б" else f"{n:.1f} {unit}"
        n /= 1024


# ---- статьи: визуализации + ключевые markdown ----
VIZ_TITLES = {
    "GP_DECOMPOSITION_RESULTS.html": "GP-разложение: результаты (7-табовый дашборд)",
    "NAVIGATOR_ENTITIES.html": "Навигатор сущностей",
    "NAVIGATOR_MERGED_ALL.html": "Объединённый навигатор",
    "GP_RESEARCH_PROGRAM_v1.html": "Исследовательская программа GP",
}
MD_ARTICLES = {
    "entities/_MASTER_INDEX.md": "Мастер-индекс сущностей",
    "skills/gp-decomposition-SKILL.md": "Методология GP-разложения (алгоритм)",
}


@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"


@app.get("/", response_class=HTMLResponse)
def landing():
    # счётчики
    ent = len(list((CONTENT / "entities").rglob("entity.md"))) if (CONTENT / "entities").exists() else 0
    decomp = len(list((CONTENT / "decompositions").glob("*.json"))) if (CONTENT / "decompositions").exists() else 0
    books = 0
    bdir = CONTENT / "books"
    if bdir.exists():
        books = sum(1 for p in bdir.rglob("*") if p.is_file() and p.suffix.lower() in (".pdf", ".docx"))
    cards = (
        '<div class="cards">'
        f'<div class="stat"><b>{ent}</b><span>сущностей</span></div>'
        f'<div class="stat"><b>18</b><span>типов операций (A01–A18)</span></div>'
        f'<div class="stat"><b>34</b><span>операции разложено</span></div>'
        f'<div class="stat"><b>{books}</b><span>книг (PDF/DOCX)</span></div>'
        "</div>"
    )
    body = (
        '<p class="lead">Исследовательский портал проекта «Методология»: систематическая '
        "обработка наследия Г.П. Щедровицкого и построение формального алфавита операций "
        "мышления. Здесь — статьи и интерактивные визуализации, а также библиотека исходных файлов.</p>"
        + cards
        + '<h2>Разделы</h2><ul class="list">'
        '<li><a href="/articles">Статьи и визуализации</a><span class="meta">дашборды + методология</span></li>'
        '<li><a href="/files">Библиотека файлов</a><span class="meta">книги, разложения, данные</span></li>'
        '<li><a href="/api-docs">API (Swagger)</a><span class="meta">для интеграций</span></li>'
        "</ul>"
    )
    return page("M2AI — Research Portal", body)


@app.get("/articles", response_class=HTMLResponse)
def articles():
    viz_dir = CONTENT / "visualizations"
    items = []
    for fname, title in VIZ_TITLES.items():
        p = viz_dir / fname
        if p.exists():
            items.append(f'<li><a href="/content/visualizations/{quote(fname)}">{html.escape(title)}</a>'
                         f'<span class="meta">интерактив</span></li>')
    md_items = []
    for rel, title in MD_ARTICLES.items():
        if (CONTENT / rel).exists():
            md_items.append(f'<li><a href="/md/{quote(rel)}">{html.escape(title)}</a>'
                            f'<span class="meta">текст</span></li>')
    body = '<h2>Визуализации</h2><ul class="list">' + ("".join(items) or "<li>—</li>") + "</ul>"
    body += '<h2>Документы</h2><ul class="list">' + ("".join(md_items) or "<li>—</li>") + "</ul>"
    return page("Статьи — M2AI", body)


@app.get("/md/{relpath:path}", response_class=HTMLResponse)
def render_md(relpath: str):
    target = (CONTENT / relpath).resolve()
    if not str(target).startswith(str(CONTENT.resolve())) or target.suffix.lower() != ".md" or not target.exists():
        raise HTTPException(404, "Документ не найден")
    htmlc = md.markdown(target.read_text(encoding="utf-8", errors="replace"),
                        extensions=["tables", "fenced_code", "toc"])
    body = '<div class="crumbs"><a href="/articles">← Статьи</a></div>' \
           f'<div class="md">{htmlc}</div>'
    return page(target.stem, body)


@app.get("/files", response_class=HTMLResponse)
@app.get("/files/{relpath:path}", response_class=HTMLResponse)
def files(relpath: str = ""):
    root = CONTENT
    target = (root / relpath).resolve()
    if not str(target).startswith(str(root.resolve())) or not target.exists():
        raise HTTPException(404, "Путь не найден")
    if target.is_file():
        return FileResponse(str(target), filename=target.name)
    # директория → листинг
    entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    rows = []
    if relpath:
        parent = "/".join(relpath.rstrip("/").split("/")[:-1])
        rows.append(f'<li><a href="/files/{quote(parent)}">../</a><span class="meta">наверх</span></li>')
    for p in entries:
        rel = f"{relpath}/{p.name}" if relpath else p.name
        if p.is_dir():
            cnt = sum(1 for _ in p.iterdir())
            rows.append(f'<li><a href="/files/{quote(rel)}">{html.escape(p.name)}/</a>'
                        f'<span class="meta">{cnt} элем.</span></li>')
        else:
            rows.append(f'<li><a href="/content/{quote(rel)}">{html.escape(p.name)}</a>'
                        f'<span class="meta">{fsize(p)}</span></li>')
    crumb = "content/" + relpath
    body = f'<div class="crumbs">{html.escape(crumb)}</div><ul class="list">' + "".join(rows) + "</ul>"
    return page("Файлы — M2AI", body)

"""M2AI — Methodology-to-AI Research Portal (MVP).

Стиль: «карандаш и мел» — светлый чертёжный. Лендинг, статьи, файлы,
дорожная карта, лента изменений (news.json). Полный REST+MCP — позже (KAN-258).
"""
import os
import html
import json
from pathlib import Path
from urllib.parse import quote

import markdown as md
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent.parent
CONTENT = Path(os.environ.get("CONTENT_DIR", BASE / "content"))
ROADMAP_FILE = BASE / "roadmap" / "roadmap.json"
NEWS_FILE = BASE / "roadmap" / "news.json"
GRAPH_NODES_FILE = BASE / "graph" / "nodes.json"
GRAPH_EDGES_FILE = BASE / "graph" / "edges.json"
BACKBONE_FILE = BASE / "graph" / "backbone.json"

def _load_graph():
    try:
        nodes = json.loads(GRAPH_NODES_FILE.read_text(encoding="utf-8"))
        edges = json.loads(GRAPH_EDGES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return [], {}, []
    return nodes, {n["id"]: n for n in nodes}, edges

GRAPH_NODES, GRAPH_BY_ID, GRAPH_EDGES = _load_graph()

WIKI_CSS = """
.widx{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:8px 18px}
.widx a{display:block;padding:6px 0;font-size:14px;border-bottom:1px dotted var(--line)}
.widx a small{color:var(--ink2);font-family:'IBM Plex Mono',monospace;font-size:10px;margin-right:6px}
.wsearch{width:100%;padding:9px 12px;border:1.5px solid var(--ink);font-family:Inter,sans-serif;font-size:14px;margin:6px 0 18px;background:var(--paper)}
.versions{list-style:none;padding:0;margin:0}
.versions li{padding:9px 0 9px 16px;border-left:2px solid var(--line2);margin-left:6px;font-size:14px}
.versions li .h{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--red)}
.dl{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:9px;border:1px solid var(--line2);padding:1px 5px;margin-left:6px;text-transform:uppercase;color:var(--ink2)}
.dl.new{color:#1c7a4d;border-color:#bfe3cf}.dl.deepened{color:#9a6b12;border-color:#ecd9a8}
.dl.confirmed{color:#27557f;border-color:#cadcef}.dl.revised{color:#a32d2d;border-color:#f0c1c1}
.bbflow{display:flex;flex-direction:column;gap:0}
.bbc{border:1px solid var(--line2);margin-bottom:0;border-bottom:none}
.bbc:last-child{border-bottom:1px solid var(--line2)}
.bbc .hd{background:var(--wash);padding:8px 12px;font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink2);display:flex;justify-content:space-between;align-items:center}
.bbc .arrow{text-align:center;color:var(--ink2);font-family:'IBM Plex Mono',monospace;font-size:12px;padding:2px}
.chips{display:flex;flex-wrap:wrap;gap:8px;padding:12px}
.bnode{font-size:12px;padding:5px 10px;border:1px solid var(--line2);background:var(--paper);display:inline-flex;align-items:center;gap:6px}
.bnode.hit{border-color:#1c7a4d}.bnode.hit::before{content:'✓';color:#1c7a4d;font-family:'IBM Plex Mono',monospace}
.bnode.gap{border-style:dashed;color:var(--ink2)}.bnode.gap::before{content:'○';color:var(--red)}
.bnode a{text-decoration:none;color:var(--ink)}
.cover{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--ink2)}
.def{font-size:16px;color:#2a2d34;border-left:3px solid var(--ink);padding-left:14px;margin:14px 0}
.idline{display:flex;gap:10px;flex-wrap:wrap;align-items:center;font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--ink2);margin-top:6px}
.badge{border:1px solid var(--line2);padding:2px 8px;text-transform:uppercase;letter-spacing:.05em}
.badge.cat{border-color:#1d7a5e;color:#1d7a5e}
.srcs{list-style:none;padding:0;margin:0}
.srcs li{padding:7px 0;border-top:1px dashed var(--line2);font-size:14px}
.srcs li:first-child{border:none}
.rel{list-style:none;padding:0;margin:0}
.rel li{display:flex;align-items:baseline;gap:10px;padding:7px 0;border-top:1px solid var(--line);font-size:14px}
.rel li:first-child{border:none}
.rel .edge{font-family:'IBM Plex Mono',monospace;font-size:10px;color:var(--red);width:110px;flex:0 0 110px;text-transform:uppercase}
.rel a{color:var(--ink);text-decoration:none}.rel a:hover{text-decoration:underline;text-decoration-color:var(--red);text-underline-offset:3px}
"""


app = FastAPI(title="M2AI — Methodology-to-AI Research Portal", docs_url="/api-docs")

if CONTENT.exists():
    app.mount("/content", StaticFiles(directory=str(CONTENT), html=False), name="content")

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600'
         '&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">')

CSS = """
:root{--ink:#16181d;--ink2:#5b606b;--line:#dcdee3;--line2:#bcbfc7;--paper:#ffffff;
--red:#c0392b;--wash:#f7f8fa;--grid:#eef1f5}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,system-ui,sans-serif;
-webkit-font-smoothing:antialiased;line-height:1.6;
background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px);
background-size:28px 28px}
.mono{font-family:"IBM Plex Mono",ui-monospace,monospace}
a{color:var(--ink);text-decoration:none}
.wrap{max-width:1180px;margin:0 auto;padding:0 28px}
header.top{display:flex;justify-content:space-between;align-items:center;padding:18px 0;border-bottom:2px solid var(--ink)}
.brand{font-weight:600;font-size:19px;letter-spacing:-.01em}
.brand i{color:var(--red);font-style:normal;margin:0 2px}
.brand small{display:block;font-family:"IBM Plex Mono",monospace;font-weight:400;font-size:10px;
letter-spacing:.2em;text-transform:uppercase;color:var(--ink2);margin-top:3px}
nav a{color:var(--ink2);font-size:13px;margin-left:20px}
nav a:hover{color:var(--ink);text-decoration:underline;text-decoration-color:var(--red);text-underline-offset:4px}
.metastrip{display:flex;gap:24px;flex-wrap:wrap;padding:8px 0;border-bottom:1px solid var(--line);
font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink2)}
.layout{display:grid;grid-template-columns:1fr 308px;gap:0}
.layout.full{grid-template-columns:1fr}
.main{padding:32px 38px 40px 0;border-right:1px solid var(--line)}
.layout.full .main{border-right:none;padding-right:0}
.idx{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink2)}
h1{font-size:46px;line-height:1.04;letter-spacing:-.025em;font-weight:600;margin:12px 0 16px}
h1 .u{text-decoration:underline;text-decoration-color:var(--red);text-underline-offset:6px}
h2{font-size:22px;font-weight:600;margin:34px 0 14px;letter-spacing:-.01em}
h3{font-size:16px;font-weight:600;margin:24px 0 10px}
.lead{font-size:17px;line-height:1.55;color:#2a2d34;max-width:600px}
.diagram{display:flex;align-items:center;margin:30px 0;font-family:"IBM Plex Mono",monospace;font-size:11px;flex-wrap:wrap;gap:8px 0}
.node{border:1.5px solid var(--ink);padding:9px 13px;text-align:center;min-width:90px;line-height:1.2;background:var(--paper)}
.node small{display:block;color:var(--ink2);font-size:10px;margin-top:3px}
.arr{flex:0 0 34px;height:1.5px;background:var(--ink);position:relative}
.arr::after{content:"";position:absolute;right:0;top:-4px;border-left:7px solid var(--ink);border-top:4px solid transparent;border-bottom:4px solid transparent}
.stats{display:flex;flex-wrap:wrap;border:1px solid var(--ink);margin:26px 0;background:var(--paper)}
.stats div{flex:1;min-width:90px;padding:15px 14px;border-right:1px solid var(--line)}
.stats div:last-child{border-right:none}
.stats b{display:block;font-size:28px;font-weight:600;letter-spacing:-.02em}
.stats span{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--ink2);letter-spacing:.05em;text-transform:uppercase}
.list{list-style:none;padding:0;margin:0}
.list li{display:flex;align-items:baseline;gap:16px;padding:15px 0;border-top:1px solid var(--line)}
.list li .k{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--red);width:34px;flex:0 0 34px}
.list li a{font-size:19px;font-weight:500}
.list li a:hover{text-decoration:underline;text-decoration-color:var(--red);text-underline-offset:4px}
.list li .d{margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--ink2)}
.crumbs{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--ink2);margin:6px 0 14px}
.md{max-width:720px}.md pre{background:var(--wash);padding:12px 14px;border:1px solid var(--line);overflow:auto}
.md code{background:var(--wash);padding:1px 5px;border:1px solid var(--line)}
.md table{border-collapse:collapse}.md td,.md th{border:1px solid var(--line);padding:6px 10px}
.md h1{font-size:30px;margin-top:8px}.md h2{font-size:20px}.md h3{font-size:16px}
aside.news{padding:32px 0 40px 28px}
aside.news h4{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink2);margin:0 0 4px}
aside.news .rule{height:2px;background:var(--ink);margin-bottom:14px}
.it{padding:13px 0;border-bottom:1px solid var(--line)}
.it .dt{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--ink2)}
.it .dt b{color:var(--red);font-weight:500}
.it .tg{font-family:"IBM Plex Mono",monospace;font-size:9px;letter-spacing:.1em;text-transform:uppercase;border:1px solid var(--line2);color:var(--ink2);padding:1px 6px;margin-left:6px}
.it p{margin:6px 0 0;font-size:13px;line-height:1.45}
.it p b{font-weight:600}
footer{border-top:2px solid var(--ink);margin-top:0;padding:14px 0 30px;font-family:"IBM Plex Mono",monospace;
font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink2);display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
.proj{border:1px solid var(--line2);padding:16px 18px;margin-bottom:14px;background:var(--paper)}
.proj h3{margin:0 0 4px;font-size:18px}
.proj .code{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink2)}
.proj p.sum{color:#2a2d34;margin:8px 0 12px;font-size:14px}
.bar{height:7px;background:var(--wash);border:1px solid var(--line);overflow:hidden;margin:10px 0}
.bar>i{display:block;height:100%;background:var(--ink)}
.chip{display:inline-block;font-family:"IBM Plex Mono",monospace;font-size:10px;padding:2px 8px;border:1px solid var(--line2);margin-right:6px;text-transform:uppercase;letter-spacing:.04em}
.s-live{background:#e7f6ee;color:#1c7a4d;border-color:#bfe3cf}
.s-done{background:#e9f1fb;color:#27557f;border-color:#cadcef}
.s-in_progress{background:#fbf3e0;color:#9a6b12;border-color:#ecd9a8}
.s-next{background:#f1ebfb;color:#6a3fa3;border-color:#ddccef}
.s-backlog{background:#f0f1f3;color:#5b606b;border-color:#dcdee3}
.s-idea{background:#f6f6f7;color:#75797f;border-color:#e3e4e7}
.meta-row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--ink2)}
.epic{border:1px solid var(--line);padding:12px 14px;margin:10px 0;background:var(--wash)}
.epic h4{margin:0 0 8px;font-size:15px}
.tasks{list-style:none;padding:0;margin:0}
.tasks li{display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-top:1px dashed var(--line2);font-size:14px}
.tasks li:first-child{border-top:none}
.tl{list-style:none;padding:0;margin:0}
.tl li{padding:8px 0 8px 16px;border-left:2px solid var(--line2);margin-left:6px;font-size:14px}
.tl li b{font-family:"IBM Plex Mono",monospace;color:var(--red);font-weight:500;font-size:12px}
.grp h2{margin-top:28px}
"""


def _load_json(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def news_rail():
    data = _load_json(NEWS_FILE) or {"items": []}
    items = data.get("items", [])[:6]
    rows = ""
    for it in items:
        d = html.escape(it.get("date", ""))
        tg = it.get("tag", "")
        tg_html = f'<span class="tg">{html.escape(tg)}</span>' if tg else ""
        rows += (f'<div class="it"><div class="dt"><b>{d}</b>{tg_html}</div>'
                 f'<p>{html.escape(it.get("text",""))}</p></div>')
    return (f'<aside class="news"><h4>{html.escape(data.get("title","Лента изменений"))}</h4>'
            f'<div class="rule"></div>{rows}'
            f'<div class="it" style="border:none"><a class="mono" style="font-size:11px;color:var(--red)" href="/news">все записи →</a></div></aside>')


NAV = ('<nav><a href="/">Главная</a><a href="/articles">Статьи</a>'
       '<a href="/files">Файлы</a><a href="/wiki">Вики</a><a href="/roadmap">Дорожная карта</a>'
       '<a href="/news">Лента</a><a href="/api-docs">API</a></nav>')

META = ('<div class="metastrip mono"><span>M2AI · Research Portal</span>'
        '<span>Г.П. Щедровицкий</span><span>1956 — 1987</span>'
        '<span>www.m-2ai.com</span></div>')


def page(title: str, body: str, rail: bool = False) -> str:
    inner = (f'<div class="layout"><div class="main">{body}</div>{news_rail()}</div>'
             if rail else f'<div class="layout full"><div class="main">{body}</div></div>')
    return (
        f'<!doctype html><html lang=ru><head><meta charset=utf-8>'
        f'<meta name=viewport content="width=device-width,initial-scale=1">'
        f'<title>{html.escape(title)}</title>{FONTS}<style>{CSS}{WIKI_CSS}</style></head><body>'
        f'<div class="wrap"><header class="top"><div class="brand">М2<i>/</i>Методология'
        f'<small>M2AI — Methodology to AI</small></div>{NAV}</header>{META}'
        f'{inner}'
        f'<footer><span>M2AI — Methodology to AI</span>'
        f'<span>Наследие Г.П. Щедровицкого · алфавит операций мышления</span></footer></div></body></html>'
    )


def fsize(p: Path) -> str:
    n = p.stat().st_size
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if n < 1024 or unit == "ГБ":
            return f"{n:.0f} {unit}" if unit == "Б" else f"{n:.1f} {unit}"
        n /= 1024


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
    ent = len(list((CONTENT / "entities").rglob("entity.md"))) if (CONTENT / "entities").exists() else 0
    bdir = CONTENT / "books"
    books = sum(1 for p in bdir.rglob("*") if p.is_file() and p.suffix.lower() in (".pdf", ".docx")) if bdir.exists() else 0
    decomp = len(list((CONTENT / "decompositions").glob("*.json"))) if (CONTENT / "decompositions").exists() else 0
    body = (
        '<div class="idx mono">00 — Общий вид</div>'
        '<h1>Операции <span class="u">мышления</span>,<br>разложенные.</h1>'
        '<p class="lead">Наследие Г.П. Щедровицкого как формальная система: тексты разложены '
        'на элементарные операции «сопоставление + отнесение», типы сведены в алфавит, '
        'сущности связаны в граф, результаты — в навигаторы и интерактивные отчёты.</p>'
        '<div class="diagram">'
        '<div class="node">ТЕКСТ<small>источник</small></div><div class="arr"></div>'
        '<div class="node">ОПЕРАЦИЯ<small>S1–S6</small></div><div class="arr"></div>'
        '<div class="node">ТИП<small>A01–A18</small></div><div class="arr"></div>'
        '<div class="node">ГРАФ<small>связи</small></div></div>'
        '<div class="stats">'
        f'<div><b>{ent}</b><span>сущности</span></div>'
        '<div><b>18</b><span>типов · A01–A18</span></div>'
        f'<div><b>{decomp}</b><span>разложений</span></div>'
        f'<div><b>{books}</b><span>книг</span></div></div>'
        '<h2>Разделы</h2><ul class="list">'
        '<li><span class="k mono">§01</span><a href="/articles">Статьи и визуализации</a><span class="d">дашборды · методология</span></li>'
        '<li><span class="k mono">§02</span><a href="/files">Библиотека файлов</a><span class="d">книги · разложения · данные</span></li>'
        '<li><span class="k mono">§03</span><a href="/roadmap">Дорожная карта</a><span class="d">8 проектов · логи</span></li>'
        '<li><span class="k mono">§04</span><a href="/api-docs">API / MCP</a><span class="d">интеграции · агенты</span></li>'
        '</ul>'
    )
    return page("M2AI — Research Portal", body, rail=True)


@app.get("/news", response_class=HTMLResponse)
def news_page():
    data = _load_json(NEWS_FILE) or {"items": []}
    rows = ""
    for it in data.get("items", []):
        tg = it.get("tag", "")
        tg_html = f'<span class="tg">{html.escape(tg)}</span>' if tg else ""
        rows += (f'<div class="it"><div class="dt"><b>{html.escape(it.get("date",""))}</b>{tg_html}</div>'
                 f'<p>{html.escape(it.get("text",""))}</p></div>')
    body = '<div class="idx mono">Журнал</div><h2 style="margin-top:8px">Лента изменений</h2>' + rows
    return page("Лента изменений — M2AI", body)


@app.get("/articles", response_class=HTMLResponse)
def articles():
    viz_dir = CONTENT / "visualizations"
    items = "".join(
        f'<li><span class="k mono">{i+1:02d}</span><a href="/content/visualizations/{quote(f)}">{html.escape(t)}</a><span class="d">интерактив</span></li>'
        for i, (f, t) in enumerate(VIZ_TITLES.items()) if (viz_dir / f).exists()
    )
    md_items = "".join(
        f'<li><span class="k mono">{i+1:02d}</span><a href="/md/{quote(rel)}">{html.escape(t)}</a><span class="d">текст</span></li>'
        for i, (rel, t) in enumerate(MD_ARTICLES.items()) if (CONTENT / rel).exists()
    )
    body = ('<div class="idx mono">§01 — Статьи</div><h2 style="margin-top:8px">Визуализации</h2>'
            f'<ul class="list">{items or "<li>—</li>"}</ul>'
            f'<h2>Документы</h2><ul class="list">{md_items or "<li>—</li>"}</ul>')
    return page("Статьи — M2AI", body, rail=True)


@app.get("/md/{relpath:path}", response_class=HTMLResponse)
def render_md(relpath: str):
    target = (CONTENT / relpath).resolve()
    if not str(target).startswith(str(CONTENT.resolve())) or target.suffix.lower() != ".md" or not target.exists():
        raise HTTPException(404, "Документ не найден")
    htmlc = md.markdown(target.read_text(encoding="utf-8", errors="replace"),
                        extensions=["tables", "fenced_code", "toc"])
    body = f'<div class="crumbs"><a href="/articles">← Статьи</a></div><div class="md">{htmlc}</div>'
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
    entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    rows = ""
    if relpath:
        parent = "/".join(relpath.rstrip("/").split("/")[:-1])
        rows += f'<li><span class="k mono">··</span><a href="/files/{quote(parent)}">наверх</a></li>'
    for p in entries:
        rel = f"{relpath}/{p.name}" if relpath else p.name
        if p.is_dir():
            cnt = sum(1 for _ in p.iterdir())
            rows += f'<li><span class="k mono">DIR</span><a href="/files/{quote(rel)}">{html.escape(p.name)}/</a><span class="d">{cnt} элем.</span></li>'
        else:
            rows += f'<li><span class="k mono">·</span><a href="/content/{quote(rel)}">{html.escape(p.name)}</a><span class="d">{fsize(p)}</span></li>'
    body = (f'<div class="idx mono">§02 — Файлы</div><div class="crumbs">content/{html.escape(relpath)}</div>'
            f'<ul class="list">{rows}</ul>')
    return page("Файлы — M2AI", body)


HORIZON_ORDER = [("now", "Сейчас"), ("next", "Следующее"), ("later", "Дальше"), ("done", "Завершено")]


def _chip(status):
    return f'<span class="chip s-{html.escape(status)}">{html.escape(status)}</span>'


@app.get("/roadmap", response_class=HTMLResponse)
def roadmap():
    rm = _load_json(ROADMAP_FILE) or {"projects": []}
    projs = rm.get("projects", [])
    by_h = {}
    for p in projs:
        by_h.setdefault(p.get("horizon", "later"), []).append(p)
    total = len(projs)
    avg = round(sum(p.get("progress", 0) for p in projs) / total) if total else 0
    body = ('<div class="idx mono">§03 — Дорожная карта</div>'
            '<p class="lead" style="margin-top:10px">Портфель проектов «Методологии»: статусы, эпики, '
            'зависимости и лог движения. Данные — связанный граф объектов (roadmap.json).</p>'
            '<div class="stats">'
            f'<div><b>{total}</b><span>проектов</span></div>'
            f'<div><b>{sum(1 for p in projs if p.get("status") in ("live","done"))}</b><span>готово / в проде</span></div>'
            f'<div><b>{avg}%</b><span>средний прогресс</span></div></div>')
    for hkey, htitle in HORIZON_ORDER:
        items = by_h.get(hkey, [])
        if not items:
            continue
        body += f'<div class="grp"><h2>{html.escape(htitle)}</h2>'
        for p in items:
            deps = p.get("depends_on") or []
            depstr = (" · зависит: " + ", ".join(deps)) if deps else ""
            body += (
                f'<div class="proj"><div class="code">{html.escape(p.get("code",""))}{depstr}</div>'
                f'<h3><a href="/roadmap/{html.escape(p.get("id",""))}">{html.escape(p.get("title",""))}</a></h3>'
                f'<div class="meta-row">{_chip(p.get("status","backlog"))}'
                f'<span>приоритет: {html.escape(p.get("priority","-"))}</span><span>{p.get("progress",0)}%</span></div>'
                f'<div class="bar"><i style="width:{p.get("progress",0)}%"></i></div>'
                f'<p class="sum">{html.escape(p.get("summary",""))}</p></div>'
            )
        body += '</div>'
    return page("Дорожная карта — M2AI", body, rail=True)


@app.get("/roadmap/{pid}", response_class=HTMLResponse)
def roadmap_project(pid: str):
    rm = _load_json(ROADMAP_FILE) or {"projects": []}
    p = next((x for x in rm.get("projects", []) if x.get("id") == pid), None)
    if not p:
        raise HTTPException(404, "Проект не найден")
    deps = ", ".join(p.get("depends_on") or []) or "—"
    body = ('<div class="crumbs"><a href="/roadmap">← Дорожная карта</a></div>'
            f'<div class="idx mono">{html.escape(p.get("code",""))}</div>'
            f'<h2 style="margin-top:6px">{html.escape(p.get("title",""))}</h2>'
            f'<div class="meta-row">{_chip(p.get("status","backlog"))}'
            f'<span>приоритет: {html.escape(p.get("priority","-"))}</span>'
            f'<span>горизонт: {html.escape(p.get("horizon","-"))}</span>'
            f'<span>зависит: {html.escape(deps)}</span></div>'
            f'<div class="bar"><i style="width:{p.get("progress",0)}%"></i></div>'
            f'<p class="lead" style="font-size:15px">{html.escape(p.get("summary",""))}</p>'
            '<h3>Эпики и задачи</h3>')
    for e in p.get("epics", []):
        body += f'<div class="epic"><h4>{_chip(e.get("status","backlog"))} {html.escape(e.get("title",""))}</h4><ul class="tasks">'
        for t in e.get("tasks", []):
            body += f'<li><span>{html.escape(t.get("title",""))}</span>{_chip(t.get("status","backlog"))}</li>'
        body += '</ul></div>'
    log = p.get("log", [])
    body += '<h3>Лог движения</h3>'
    body += ('<ul class="tl">' + "".join(
        f'<li><b>{html.escape(l.get("date",""))}</b><br>{html.escape(l.get("entry",""))}</li>' for l in log
    ) + '</ul>') if log else '<p class="sum">записей пока нет</p>'
    return page(p.get("title", "Проект") + " — M2AI", body)


# ---- Вики (граф связанных объектов) ----
def _mini_graph_svg(nid):
    neigh = []
    for e in GRAPH_EDGES:
        if e["from"] == nid and e["to"] != nid:
            neigh.append((e["to"], e.get("rel"), "out"))
        elif e["to"] == nid and e["from"] != nid:
            neigh.append((e["from"], e.get("rel"), "in"))
    seen, uniq = set(), []
    for t, rel, d in neigh:
        if t in seen:
            continue
        seen.add(t); uniq.append((t, rel, d))
    uniq = uniq[:8]
    import math
    cx, cy = 150, 125
    svg = ['<svg viewBox="0 0 300 250" width="100%" height="230" role="img" aria-label="мини-граф">',
           '<defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6" fill="#bcbfc7"/></marker></defs>']
    n = max(len(uniq), 1)
    pts = []
    for i, (t, rel, d) in enumerate(uniq):
        ang = 2 * math.pi * i / n - math.pi / 2
        x, y = cx + 95 * math.cos(ang), cy + 92 * math.sin(ang)
        pts.append((x, y, t, rel))
    for x, y, t, rel in pts:
        col = "#c0392b" if rel == "transforms" else "#bcbfc7"
        dash = '' if rel == "relates_to" else ' stroke-dasharray="3 3"'
        svg.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.0f}" y2="{y:.0f}" stroke="{col}" stroke-width="1.1"{dash} marker-end="url(#a)"/>')
    for x, y, t, rel in pts:
        nd = GRAPH_BY_ID.get(t)
        lbl = (nd["title"] if nd else t)[:14]
        svg.append(f'<rect x="{x-32:.0f}" y="{y-11:.0f}" width="64" height="22" fill="#fff" stroke="#bcbfc7"/>'
                   f'<text x="{x:.0f}" y="{y+3:.0f}" text-anchor="middle" font-size="8" font-family="IBM Plex Mono,monospace" fill="#16181d">{html.escape(lbl)}</text>')
    ctitle = (GRAPH_BY_ID.get(nid, {}).get("title", nid))[:16]
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="28" fill="#fff" stroke="#16181d" stroke-width="1.8"/>'
               f'<text x="{cx}" y="{cy+3}" text-anchor="middle" font-size="9" font-family="IBM Plex Mono,monospace" fill="#16181d">{html.escape(ctitle)}</text></svg>')
    return "".join(svg)


@app.get("/wiki", response_class=HTMLResponse)
def wiki_index(q: str = ""):
    ql = q.strip().lower()
    ents = [n for n in GRAPH_NODES if n["type"] == "entity"]
    if ql:
        ents = [n for n in ents if ql in n["title"].lower() or ql in (n.get("definition") or "").lower()]
    by_cat = {}
    for n in ents:
        by_cat.setdefault(n.get("category_label", "—"), []).append(n)
    total = len([n for n in GRAPH_NODES if n["type"] == "entity"])
    body = ('<div class="idx mono">Вики · граф связанных объектов</div>'
            '<h2 style="margin-top:8px">База знаний ГП</h2>'
            f'<p class="lead" style="font-size:15px">{total} сущностей · 18 типов операций · '
            '<a href="/wiki/backbone" style="color:var(--red)">каркас-эталон ↗</a></p>'
            f'<form method="get"><input class="wsearch" name="q" placeholder="поиск по сущностям…" value="{html.escape(q)}"></form>')
    for cat in sorted(by_cat, key=lambda c: -len(by_cat[c])):
        items = sorted(by_cat[cat], key=lambda n: n["title"].lower())
        body += f'<h3>{html.escape(cat)} · {len(items)}</h3><div class="widx">'
        for n in items:
            body += f'<a href="/wiki/{html.escape(n["id"])}"><small>{html.escape(n["id"])}</small>{html.escape(n["title"])}</a>'
        body += '</div>'
    return page("Вики — M2AI", body, rail=True)


@app.get("/wiki/backbone", response_class=HTMLResponse)
def wiki_backbone():
    bb = _load_json(BACKBONE_FILE) or {"clusters": [], "flow": []}
    ents = [n for n in GRAPH_NODES if n["type"] == "entity"]

    def match(label):
        ll = label.lower()
        for n in ents:
            t = n["title"].lower()
            if ll == t or ll in t or t in ll:
                return n
        return None

    clusters = {c["id"]: c for c in bb.get("clusters", [])}
    hit = tot = 0
    rows = ""
    flow = bb.get("flow") or list(clusters)
    for ci, cid in enumerate(flow):
        c = clusters.get(cid)
        if not c:
            continue
        chips = ""
        for nd in c["nodes"]:
            tot += 1
            m = match(nd.get("match", nd["label"]))
            if m:
                hit += 1
                chips += f'<span class="bnode hit"><a href="/wiki/{html.escape(m["id"])}">{html.escape(nd["label"])}</a></span>'
            else:
                chips += f'<span class="bnode gap">{html.escape(nd["label"])}</span>'
        src = f'<span>← {html.escape(c["source"])}</span>' if c.get("source") else '<span></span>'
        rows += (f'<div class="bbc"><div class="hd"><span>{html.escape(c["label"])}</span>{src}</div>'
                 f'<div class="chips">{chips}</div></div>')
        if ci < len(flow) - 1:
            rows += '<div class="arrow">↓</div>'
    body = ('<div class="crumbs"><a href="/wiki">← Вики</a></div>'
            f'<div class="idx mono">Каркас-эталон · A4.5 сверка</div>'
            f'<h2 style="margin-top:6px">{html.escape(bb.get("title","Каркас"))}</h2>'
            f'<p class="lead" style="font-size:14px">{html.escape(bb.get("note",""))} '
            f'<span class="cover">· покрытие {hit}/{tot} ({round(hit*100/tot) if tot else 0}%) · '
            '✓ есть в графе · ○ пробел</span></p>'
            f'<div class="bbflow">{rows}</div>')
    return page("Каркас-эталон — M2AI", body)


@app.get("/wiki/{nid}", response_class=HTMLResponse)
def wiki_node(nid: str):
    n = GRAPH_BY_ID.get(nid)
    if not n:
        raise HTTPException(404, "Узел не найден")
    layer = ""
    crumbs = '<div class="crumbs"><a href="/wiki">← Вики</a></div>'
    idline = (f'<div class="idline"><span class="badge mono">{html.escape(n["id"])}</span>'
              f'<span class="badge cat mono">{html.escape(n.get("category_label",""))}</span>'
              + (f'<span class="mono">первое появление: {html.escape(n["first_appearance"])}</span>' if n.get("first_appearance") else "") + '</div>')
    body = crumbs + idline + f'<h1 style="font-size:32px">{html.escape(n["title"])}</h1>'
    if n.get("definition"):
        body += f'<p class="def">{html.escape(n["definition"])}</p>'

    if n["type"] == "operation_type":
        body += ('<h2>Параметры типа</h2><div class="meta-row">'
                 f'<span>S-паттерн: {html.escape(str(n.get("s_pattern")))}</span>'
                 f'<span>знак: {html.escape(str(n.get("sign")))}</span>'
                 f'<span>частота: {html.escape(str(n.get("frequency")))}</span>'
                 f'<span>ген.сложность: {html.escape(str(n.get("genetic_complexity")))}</span></div>')

    # versions (revises timeline)
    vers = n.get("versions") or []
    if len(vers) > 0:
        body += '<h2>Версии инстанса (revises)</h2><ul class="versions">'
        for v in vers:
            body += (f'<li><span class="h mono">{html.escape(v.get("source",""))}</span>'
                     f'<span class="dl {v.get("delta","new")}">{v.get("delta","new")}</span>'
                     f'<br>{html.escape((v.get("text") or "")[:400])}</li>')
        body += '</ul>'
    # sources
    if n.get("sources"):
        body += '<h2>Источники (cites)</h2><ul class="srcs">' + "".join(
            f'<li><span>{html.escape(s)}</span></li>' for s in n["sources"]) + '</ul>'
    # relations out
    outs = [e for e in GRAPH_EDGES if e["from"] == nid]
    if outs:
        body += '<h2>Связи</h2><ul class="rel">'
        for e in outs[:40]:
            tgt = GRAPH_BY_ID.get(e["to"])
            nm = e.get("to_name") or (tgt["title"] if tgt else e["to"])
            link = f'/wiki/{e["to"]}' if tgt else None
            label = f'{html.escape(e["to"])} · {html.escape(nm)}'
            cell = f'<a href="{link}">{label}</a>' if link else f'<span>{label}</span>'
            rel = e.get("rel_type") or e.get("rel")
            body += f'<li><span class="edge">{html.escape(rel)}→</span>{cell}</li>'
        body += '</ul>'
    # backlinks
    ins = [e for e in GRAPH_EDGES if e["to"] == nid]
    if ins:
        body += '<h2>Обратные ссылки</h2><ul class="rel">'
        for e in ins[:30]:
            src = GRAPH_BY_ID.get(e["from"])
            nm = src["title"] if src else e["from"]
            cell = f'<a href="/wiki/{e["from"]}">{html.escape(e["from"])} · {html.escape(nm)}</a>' if src else f'<span>{html.escape(e["from"])}</span>'
            body += f'<li><span class="edge">←{html.escape(e.get("rel",""))}</span>{cell}</li>'
        body += '</ul>'
    # mini-graph
    body += '<h2>Мини-граф окружения</h2>' + _mini_graph_svg(nid)
    return page(n["title"] + " — Вики", body)

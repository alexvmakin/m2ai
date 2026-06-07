# M2AI — Methodology-to-AI Research Portal

> **Проект:** M2AI (Methodology to AI)
> **Домен:** `life.avmakin.com/m2ai`
> **Репозиторий:** `alexvmakin/m2ai` (GitHub, private)
> **Хостинг:** Railway (в рамках существующего проекта MGSS / makin-life)
> **Статус:** NEW — готов к разработке
> **Дата:** 2026-05-24
> **Приоритет:** высокий

---

## 1. Суть проекта

Исследовательский портал для публикации результатов проекта "Методология" — систематической обработки наследия Г.П. Щедровицкого и построения формального алфавита операций мышления.

**Два типа клиентов:**
1. **Люди (партнёры по проекту)** — браузер, навигация, чтение, скачивание
2. **AI-агенты** — MCP-подключение, программный доступ к структурированным данным

---

## 2. Что публикуем (контент)

### 2.1. Исходные книги (PDF)
Источник: `05_PROJECTS/METHODOLOGY/0/`, `05_PROJECTS/METHODOLOGY/1/`

| Папка | Содержание | Файлы |
|-------|-----------|-------|
| `0/` | Хрестоматии Зинченко: путеводители, ОРУ, рефлексия, СМД | 6 PDF + 2 DOCX |
| `1/` | Оригинальные тексты ГП: диссертация, логика науки, на перекрёстке мысли | 4 PDF + 2 DOCX |

### 2.2. Проработка #1 — Извлечение сущностей
Источник: `05_PROJECTS/METHODOLOGY/ENTITIES/`

- **202 сущности** в 6 категориях: concepts (133), methodologies, methods, schemas, theories, theses
- Каждая сущность: `entity.md` (определение, источники, цитаты), `LOG.md`, `CONNECTIONS.md`
- Мастер-индекс: `_MASTER_INDEX.md`
- HTML-навигаторы: `NAVIGATOR_ENTITIES.html`, `NAVIGATOR_MERGED_*.html`

### 2.3. Проработка #2 — GP-разложение (операции мышления)
Источник: `05_PROJECTS/METHODOLOGY/1/DECOMPOSITIONS/`

- 3 JSON-разложения: `01_DISSERTATION_INTRO.json`, `02_EUCLID_ANALYSIS.json`, `03_THINKING_ACTIVITY.json`
- Сводный мета-алфавит: `04_MERGED_ALPHABET.json` (18 типов, 34 операции)
- Валидация: `05_VALIDATION.json` (10 операций, PASSED)
- HTML-визуализация: `GP_DECOMPOSITION_RESULTS.html` (интерактивный 7-табовый дашборд)
- Алгоритм: `SKILLS/gp-decomposition/SKILL.md`

### 2.4. Вспомогательные материалы
- Онтологические карты: `ONTOLOGICAL_MAP_FOLDER_0.md`, `ONTOLOGICAL_MAP_FOLDER_1.md`
- Исследовательская программа: `PROGRAM/GP_RESEARCH_PROGRAM_v1.html`
- Дельты и анализы книг: `BOOK_*_DELTA.md`, `BOOK_*_ENTITIES.md`

---

## 3. Архитектура

### 3.1. Общая схема

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Repo: m2ai                         │
│  /content/books/     — PDF/DOCX файлы                       │
│  /content/entities/  — entity.md файлы (202 сущности)       │
│  /content/decompositions/ — JSON разложения + алфавит       │
│  /content/visualizations/ — HTML визуализации               │
│  /server/            — FastAPI app                          │
│  /mcp_server/        — MCP Server (SSE transport)           │
│  /frontend/          — статический HTML (landing + навигация)│
└─────────────┬───────────────────────────────────────────────┘
              │ git push → auto-deploy
              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Railway Service                           │
│                                                              │
│  FastAPI (uvicorn)                                           │
│  ├── /api/v1/        — REST API (JSON)                      │
│  ├── /mcp/           — MCP SSE endpoint                     │
│  ├── /viz/           — HTML визуализации (static)           │
│  └── /               — Landing page + навигация             │
│                                                              │
│  Port: $PORT (Railway назначает)                            │
└─────────────┬───────────────────────────────────────────────┘
              │
     ┌────────┼────────┐
     ▼        ▼        ▼
  Браузер   AI Agent  External
  (люди)    (MCP)     (REST API)
```

### 3.2. Стек

| Компонент | Технология | Почему |
|-----------|-----------|--------|
| Backend | **FastAPI** (Python 3.11+) | Async, автодокументация OpenAPI, знакомый стек (как Hub API) |
| MCP Server | **mcp[sse]** (Python SDK) | Официальный SDK, SSE transport для remote access |
| Frontend | **Static HTML + Tailwind CDN** | Минимум — без SPA, без сборки, просто HTML |
| Файлы | Git LFS для PDF > 50MB | Хранение книг в репо |
| Deploy | **Railway** (Docker) | Существующий проект, автодеплой |

### 3.3. Без базы данных

Все данные — файлы в репо (JSON, MD, PDF). Никакой БД не нужно на этом этапе. Сервер читает файлы из `/content/` при старте и кеширует в памяти.

---

## 4. REST API (для людей и внешних интеграций)

### 4.1. Endpoints

```
GET  /api/v1/books
     → список книг с метаданными (название, автор, год, папка)

GET  /api/v1/books/{book_id}/download
     → скачать PDF/DOCX файл

GET  /api/v1/entities
     → список всех сущностей (id, name, category, short_definition)
     Query params: ?category=concepts&search=рефлексия

GET  /api/v1/entities/{entity_id}
     → полная сущность (definition, sources, quotes, connections)

GET  /api/v1/entities/{entity_id}/connections
     → граф связей сущности

GET  /api/v1/decompositions
     → список разложений (id, title, source, operation_count)

GET  /api/v1/decompositions/{decomposition_id}
     → полное разложение (все операции с сопоставлением/отнесением)

GET  /api/v1/alphabet
     → сводный мета-алфавит (18 типов с определениями, частотами, S-паттернами)

GET  /api/v1/alphabet/{type_id}
     → детальное описание типа операции (определение, экземпляры, генетические связи)

GET  /api/v1/genetic-map
     → граф генетических связей (nodes + edges для визуализации)

GET  /api/v1/validation
     → результаты валидации (контрольный фрагмент)

GET  /api/v1/stats
     → общая статистика: кол-во книг, сущностей, операций, типов

GET  /api/v1/search
     → полнотекстовый поиск по сущностям и операциям
     Query params: ?q=рефлексия&scope=entities,operations
```

### 4.2. Формат ответов

```json
{
  "status": "ok",
  "data": { ... },
  "meta": {
    "total": 202,
    "page": 1,
    "per_page": 50
  }
}
```

---

## 5. MCP Server (для AI-агентов)

### 5.1. Transport

SSE (Server-Sent Events) через endpoint `/mcp/` — стандартный remote MCP transport. Агенты подключаются по URL:

```
https://life.avmakin.com/m2ai/mcp/
```

### 5.2. MCP Tools

```python
@mcp.tool()
async def search_entities(query: str, category: str = None, limit: int = 20) -> list[Entity]:
    """Поиск сущностей по названию или определению.
    Категории: concepts, methodologies, methods, schemas, theories, theses."""

@mcp.tool()
async def get_entity(entity_id: str) -> Entity:
    """Получить полную сущность: определение, источники, цитаты, связи."""

@mcp.tool()
async def get_entity_connections(entity_id: str) -> list[Connection]:
    """Получить граф связей сущности с другими сущностями."""

@mcp.tool()
async def list_decompositions() -> list[DecompositionSummary]:
    """Список всех GP-разложений с метаданными."""

@mcp.tool()
async def get_decomposition(decomposition_id: str) -> Decomposition:
    """Полное GP-разложение: все операции с сопоставлением и отнесением."""

@mcp.tool()
async def get_alphabet() -> Alphabet:
    """Сводный мета-алфавит: 18 типов операций мышления ГП."""

@mcp.tool()
async def get_operation_type(type_id: str) -> OperationType:
    """Детальное описание типа операции: определение, экземпляры, генетика."""

@mcp.tool()
async def get_genetic_map() -> GeneticMap:
    """Генетическая карта: DAG из 18 узлов и 21 ребра."""

@mcp.tool()
async def search_operations(query: str, s_type: str = None) -> list[Operation]:
    """Поиск операций по тексту. Фильтр по S-типу: S1..S6."""

@mcp.tool()
async def get_book_info(book_id: str = None) -> list[BookInfo]:
    """Информация о книгах: название, автор, год, описание."""

@mcp.tool()
async def get_stats() -> Stats:
    """Общая статистика портала: количество книг, сущностей, операций, типов."""
```

### 5.3. MCP Resources (read-only контент)

```python
@mcp.resource("m2ai://books")
async def list_books() -> str:
    """Каталог книг."""

@mcp.resource("m2ai://alphabet")  
async def full_alphabet() -> str:
    """Полный алфавит в текстовом формате."""

@mcp.resource("m2ai://methodology")
async def methodology() -> str:
    """Описание методологии GP-разложения (SKILL.md)."""
```

---

## 6. Frontend (статический)

### 6.1. Страницы

| URL | Назначение |
|-----|-----------|
| `/` | Landing: название проекта, описание, навигация |
| `/viz/decompositions` | GP_DECOMPOSITION_RESULTS.html (7-табовый дашборд) |
| `/viz/entities` | NAVIGATOR_ENTITIES.html (граф сущностей) |
| `/viz/program` | GP_RESEARCH_PROGRAM_v1.html (исследовательская программа) |
| `/viz/maps` | NAVIGATOR_MERGED_ALL.html (объединённый навигатор) |
| `/docs` | Swagger UI (автогенерация FastAPI) |
| `/mcp-docs` | Инструкция подключения MCP для агентов |

### 6.2. Landing page

Минимальный HTML: логотип/название, краткое описание проекта, карточки с числами (202 сущности, 18 типов операций, 34 операции, 10 книг), навигация по разделам, ссылка на API docs и MCP endpoint.

---

## 7. Структура репозитория

```
m2ai/
├── README.md
├── Dockerfile
├── railway.json
├── requirements.txt
├── .gitattributes          ← Git LFS для PDF
├── .github/
│   └── workflows/
│       └── ci.yml          ← lint + type check
│
├── server/
│   ├── __init__.py
│   ├── main.py             ← FastAPI app, роутинг
│   ├── config.py           ← настройки (PORT, CONTENT_DIR)
│   ├── models.py           ← Pydantic-модели (Entity, Operation, Alphabet, ...)
│   ├── data_loader.py      ← загрузка JSON/MD из /content/ при старте
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── books.py        ← /api/v1/books
│   │   ├── entities.py     ← /api/v1/entities
│   │   ├── decompositions.py ← /api/v1/decompositions
│   │   ├── alphabet.py     ← /api/v1/alphabet, /api/v1/genetic-map
│   │   ├── search.py       ← /api/v1/search
│   │   └── stats.py        ← /api/v1/stats
│   └── utils/
│       ├── __init__.py
│       ├── markdown_parser.py  ← парсинг entity.md файлов
│       └── search_engine.py    ← простой полнотекстовый поиск
│
├── mcp_server/
│   ├── __init__.py
│   ├── server.py           ← MCP Server с SSE transport
│   ├── tools.py            ← MCP tools (search_entities, get_alphabet, ...)
│   └── resources.py        ← MCP resources
│
├── frontend/
│   ├── index.html          ← Landing page
│   ├── mcp-docs.html       ← Инструкция MCP подключения
│   └── static/
│       ├── style.css
│       └── logo.svg
│
├── content/                ← ДАННЫЕ (копируются из METHODOLOGY/)
│   ├── books/
│   │   ├── catalog.json    ← метаданные книг
│   │   ├── 0/              ← PDF из папки 0
│   │   └── 1/              ← PDF из папки 1
│   ├── entities/
│   │   ├── _MASTER_INDEX.md
│   │   ├── concepts/       ← entity.md файлы
│   │   ├── methodologies/
│   │   ├── methods/
│   │   ├── schemas/
│   │   ├── theories/
│   │   └── theses/
│   ├── decompositions/
│   │   ├── 01_DISSERTATION_INTRO.json
│   │   ├── 02_EUCLID_ANALYSIS.json
│   │   ├── 03_THINKING_ACTIVITY.json
│   │   ├── 04_MERGED_ALPHABET.json
│   │   └── 05_VALIDATION.json
│   ├── visualizations/
│   │   ├── GP_DECOMPOSITION_RESULTS.html
│   │   ├── NAVIGATOR_ENTITIES.html
│   │   ├── NAVIGATOR_MERGED_ALL.html
│   │   └── GP_RESEARCH_PROGRAM_v1.html
│   └── skills/
│       └── gp-decomposition-SKILL.md
│
└── tests/
    ├── test_data_loader.py
    ├── test_api.py
    └── test_mcp.py
```

---

## 8. Конфигурация Railway

### 8.1. railway.json

```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn server.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/api/v1/stats",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### 8.2. Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE $PORT

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 8.3. requirements.txt

```
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
mcp[sse]>=1.0.0
python-multipart>=0.0.9
pydantic>=2.0.0
aiofiles>=24.0.0
markdown>=3.7
pyyaml>=6.0
```

### 8.4. Переменные окружения (Railway)

```
PORT=8000                          # Railway назначает автоматически
CONTENT_DIR=/app/content           # путь к данным
CORS_ORIGINS=*                     # для MVP, потом ограничить
MCP_ENABLED=true                   # включить MCP server
```

---

## 9. Настройка домена

### 9.1. Railway Custom Domain

В Railway Dashboard → Service → Settings → Networking → Custom Domain:
- Добавить: `life.avmakin.com`

### 9.2. DNS (у регистратора домена)

```
CNAME  life.avmakin.com  →  <railway-provided-domain>.up.railway.app
```

### 9.3. Path routing

Если `life.avmakin.com` уже используется для makin-life Web (Next.js), то M2AI нужно выносить на поддомен:

**Вариант A (рекомендуемый):** Отдельный поддомен
```
m2ai.avmakin.com → M2AI Railway service
```

**Вариант B:** Path-based routing через Railway
```
life.avmakin.com/m2ai/* → M2AI service (Railway path routing)
life.avmakin.com/*      → makin-life Web (Next.js)
```

> **ВАЖНО:** Вариант B требует настройки path-based routing в Railway, что поддерживается через Private Networking или через reverse proxy. Вариант A проще и надёжнее.

---

## 10. Инструкция по запуску

### 10.1. Создание репозитория

```bash
# 1. Создать репо на GitHub
gh repo create alexvmakin/m2ai --private

# 2. Клонировать
git clone git@github.com:alexvmakin/m2ai.git
cd m2ai

# 3. Настроить Git LFS для PDF
git lfs install
echo "*.pdf filter=lfs diff=lfs merge=lfs -text" > .gitattributes
git add .gitattributes
git commit -m "Configure Git LFS for PDFs"
```

### 10.2. Копирование контента

```bash
# Из папки проекта METHODOLOGY скопировать данные:

# Книги
mkdir -p content/books/0 content/books/1
cp 05_PROJECTS/METHODOLOGY/0/*.pdf content/books/0/
cp 05_PROJECTS/METHODOLOGY/1/*.pdf content/books/1/

# Сущности
cp -r 05_PROJECTS/METHODOLOGY/ENTITIES/ content/entities/

# Разложения
mkdir -p content/decompositions
cp 05_PROJECTS/METHODOLOGY/1/DECOMPOSITIONS/*.json content/decompositions/

# Визуализации
mkdir -p content/visualizations
cp 05_PROJECTS/METHODOLOGY/1/DECOMPOSITIONS/GP_DECOMPOSITION_RESULTS.html content/visualizations/
cp 05_PROJECTS/METHODOLOGY/ENTITIES/NAVIGATOR_ENTITIES.html content/visualizations/
cp 05_PROJECTS/METHODOLOGY/NAVIGATORS/NAVIGATOR_MERGED_ALL.html content/visualizations/
cp 05_PROJECTS/METHODOLOGY/PROGRAM/GP_RESEARCH_PROGRAM_v1.html content/visualizations/

# Скилл GP-разложения
mkdir -p content/skills
cp 05_PROJECTS/METHODOLOGY/SKILLS/gp-decomposition/SKILL.md content/skills/gp-decomposition-SKILL.md
```

### 10.3. Railway Deploy

```bash
# 1. В Railway Dashboard → New Service → GitHub Repo → alexvmakin/m2ai
# 2. Railway автоматически обнаружит Dockerfile
# 3. Добавить переменные окружения (см. раздел 8.4)
# 4. Настроить домен (см. раздел 9)
# 5. Deploy → проверить /api/v1/stats
```

### 10.4. Подключение MCP-агента

```json
// В Claude Desktop config (claude_desktop_config.json):
{
  "mcpServers": {
    "m2ai": {
      "transport": "sse",
      "url": "https://m2ai.avmakin.com/mcp/"
    }
  }
}
```

---

## 11. Задачи для фабрики разработки

### Эпик 1: Skeleton (MVP) — 1-2 дня

| # | Задача | Агент | Приоритет |
|---|--------|-------|-----------|
| 1.1 | Создать структуру репо (файлы, папки, Dockerfile, requirements.txt, railway.json) | Devin | P0 |
| 1.2 | Реализовать `data_loader.py` — загрузка JSON/MD из /content/ при старте | Devin | P0 |
| 1.3 | Реализовать Pydantic-модели (`models.py`) | Devin | P0 |
| 1.4 | Реализовать REST API — все endpoints (routers/) | Devin | P0 |
| 1.5 | Реализовать MCP Server с SSE transport и всеми tools | Devin | P0 |
| 1.6 | Landing page (index.html) | Devin | P1 |
| 1.7 | Настроить CI (GitHub Actions: ruff + mypy) | Devin | P1 |

### Эпик 2: Контент — 1 день

| # | Задача | Агент | Приоритет |
|---|--------|-------|-----------|
| 2.1 | Скопировать все PDF книг в content/books/ | Ручная (Алексей) | P0 |
| 2.2 | Скопировать сущности в content/entities/ | Ручная (Алексей) | P0 |
| 2.3 | Скопировать JSON разложений в content/decompositions/ | Ручная (Алексей) | P0 |
| 2.4 | Скопировать HTML визуализации в content/visualizations/ | Ручная (Алексей) | P0 |
| 2.5 | Создать catalog.json для книг (метаданные) | Devin | P1 |

### Эпик 3: Deploy & Domain — 0.5 дня

| # | Задача | Агент | Приоритет |
|---|--------|-------|-----------|
| 3.1 | Создать Railway service из GitHub repo | Ручная (Алексей) | P0 |
| 3.2 | Настроить DNS (CNAME) | Ручная (Алексей) | P0 |
| 3.3 | Проверить деплой: /api/v1/stats отвечает | QA (Cowork) | P0 |
| 3.4 | Проверить MCP: подключение агента через SSE | QA (Cowork) | P0 |

### Эпик 4: Polish — 1 день

| # | Задача | Агент | Приоритет |
|---|--------|-------|-----------|
| 4.1 | Страница MCP-docs (инструкция подключения) | Devin | P2 |
| 4.2 | Полнотекстовый поиск (search_engine.py) | Devin | P2 |
| 4.3 | Тесты (test_api.py, test_mcp.py) | Devin | P2 |
| 4.4 | CORS настройка для production | Devin | P2 |

---

## 12. Acceptance Criteria

### MVP (Эпик 1 + 2 + 3)

- [ ] `GET /api/v1/stats` возвращает корректные числа (202 сущности, 18 типов, 34 операции)
- [ ] `GET /api/v1/entities?search=рефлексия` находит релевантные сущности
- [ ] `GET /api/v1/alphabet` возвращает все 18 типов с определениями
- [ ] `GET /api/v1/decompositions/01` возвращает полное разложение с операциями
- [ ] PDF книги скачиваются через `/api/v1/books/{id}/download`
- [ ] HTML визуализации открываются в браузере через `/viz/decompositions`
- [ ] MCP-агент подключается через SSE и может вызвать `get_alphabet()`
- [ ] Landing page показывает навигацию и статистику
- [ ] Деплой на Railway работает, домен настроен

### Как проверить MCP

```python
# Тест из Python:
from mcp import ClientSession
from mcp.client.sse import sse_client

async with sse_client("https://m2ai.avmakin.com/mcp/") as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        print(f"Tools: {[t.name for t in tools]}")
        
        result = await session.call_tool("get_alphabet", {})
        print(result)
```

---

## 13. Контекстные документы для агента

При выполнении задач агент (Devin/Cursor) должен читать:

1. **Этот файл** — полная спецификация
2. **`content/decompositions/04_MERGED_ALPHABET.json`** — структура данных алфавита (образец JSON)
3. **`content/entities/concepts/refleksiya/entity.md`** — образец entity файла (для парсера)
4. **`content/decompositions/01_DISSERTATION_INTRO.json`** — образец разложения (для API)

---

## 14. Известные ограничения и решения

| Проблема | Решение |
|----------|---------|
| PDF > 50MB не влезают в GitHub | Git LFS |
| Entity MD файлы имеют свободный формат | Мягкий парсер: YAML frontmatter если есть, иначе первый # = title, остальное = body |
| MCP SSE требует persistent connection | Railway поддерживает WebSocket/SSE, но нужно проверить timeout (увеличить до 300s) |
| CORS для MCP из браузера | MCP-агенты подключаются server-to-server, CORS не нужен для MCP; CORS нужен только для REST API |
| Кириллические slug'и сущностей | URL-encode в API, slug остаётся как есть в файловой системе |

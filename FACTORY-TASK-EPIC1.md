# FACTORY TASK: M2AI Research Portal — Epic 1 (Skeleton MVP)

> **Проект:** m2ai
> **Репо:** alexvmakin/m2ai (GitHub, private)
> **Спецификация:** см. PROJECT-SPEC.md в этой же папке
> **Приоритет:** P0
> **Appetite:** 2 дня
> **Агент:** Devin

---

## Контекст

M2AI — исследовательский портал для публикации результатов GP-разложения текстов Щедровицкого. Сервер на FastAPI обслуживает REST API (для людей) и MCP Server (для AI-агентов). Все данные — файлы в папке `/content/` (JSON, MD, PDF). Никакой БД.

---

## Задача

Создать полностью работающий сервер с нуля:
1. Структура репозитория (см. PROJECT-SPEC.md раздел 7)
2. FastAPI приложение со всеми REST endpoints
3. MCP Server с SSE transport и всеми tools
4. Data loader для загрузки JSON/MD при старте
5. Landing page
6. Dockerfile + railway.json для деплоя
7. CI (GitHub Actions)

---

## Технические требования

### Стек
- Python 3.11+
- FastAPI + uvicorn
- mcp[sse] (Python MCP SDK)
- Pydantic v2
- aiofiles для раздачи PDF

### Архитектура данных

Сервер при старте загружает все файлы из `/content/` в память:

```python
# data_loader.py — примерная структура
class DataStore:
    books: list[BookInfo]           # из content/books/catalog.json
    entities: dict[str, Entity]     # из content/entities/*/entity.md
    decompositions: dict[str, Decomposition]  # из content/decompositions/*.json
    alphabet: Alphabet              # из content/decompositions/04_MERGED_ALPHABET.json
    validation: Validation          # из content/decompositions/05_VALIDATION.json

# Загрузка при старте:
@app.on_event("startup")
async def load_data():
    app.state.data = DataStore.load_from_directory(settings.CONTENT_DIR)
```

### Формат entity.md

Каждый entity.md имеет примерную структуру:
```markdown
# Название сущности

**Категория:** concept
**Источники:** Книга 1, Книга 2

## Определение
Текст определения...

## Ключевые цитаты
> "Цитата 1" — Источник
> "Цитата 2" — Источник

## Связи
- связано с [[другая-сущность]]
```

Парсер должен быть мягким: извлекать что есть, не падать на нестандартном формате.

### REST API endpoints

Полный список в PROJECT-SPEC.md раздел 4. Ключевые:

```
GET  /api/v1/stats          → { books: 10, entities: 202, operations: 34, types: 18 }
GET  /api/v1/entities       → список сущностей, ?search=..., ?category=...
GET  /api/v1/entities/{id}  → полная сущность
GET  /api/v1/alphabet       → 18 типов операций
GET  /api/v1/decompositions → список разложений
GET  /api/v1/decompositions/{id} → полное разложение
GET  /api/v1/genetic-map    → { nodes: [...], edges: [...] }
GET  /api/v1/books          → список книг
GET  /api/v1/books/{id}/download → файл (PDF/DOCX)
```

Ответы всегда в формате:
```json
{ "status": "ok", "data": ..., "meta": { "total": N } }
```

### MCP Server

SSE transport, endpoint `/mcp/`. Tools — зеркало REST API:

```python
from mcp.server import Server
from mcp.server.sse import SseServerTransport

mcp_server = Server("m2ai")
sse = SseServerTransport("/mcp/")

@mcp_server.tool()
async def search_entities(query: str, category: str = None, limit: int = 20) -> list:
    """Поиск сущностей по названию или определению."""

@mcp_server.tool()
async def get_entity(entity_id: str) -> dict:
    """Полная сущность: определение, источники, цитаты, связи."""

@mcp_server.tool()
async def get_alphabet() -> dict:
    """Сводный мета-алфавит: 18 типов операций мышления."""

@mcp_server.tool()
async def get_decomposition(decomposition_id: str) -> dict:
    """Полное GP-разложение с операциями."""

@mcp_server.tool()
async def search_operations(query: str, s_type: str = None) -> list:
    """Поиск операций. Фильтр по S-типу: S1..S6."""

@mcp_server.tool()
async def get_genetic_map() -> dict:
    """Генетическая карта: DAG из 18 узлов и 21 ребра."""

@mcp_server.tool()
async def get_stats() -> dict:
    """Статистика портала."""
```

Интеграция MCP SSE в FastAPI:
```python
# main.py
from starlette.routing import Mount

app = FastAPI(title="M2AI Research Portal")

# Mount MCP SSE
app.mount("/mcp", app=sse.get_asgi_app())

# Или если SSE transport не даёт ASGI app напрямую,
# использовать отдельный endpoint:
@app.get("/mcp/sse")
async def mcp_sse_endpoint(request: Request):
    # SSE streaming
    ...

@app.post("/mcp/messages")
async def mcp_messages(request: Request):
    # Handle MCP messages
    ...
```

> **ВАЖНО:** Проверить актуальную документацию MCP Python SDK (https://github.com/modelcontextprotocol/python-sdk) для правильной интеграции SSE transport с FastAPI. API может отличаться от примера выше.

### Landing page

Простой HTML с Tailwind CDN:
- Заголовок: "M2AI — Methodology to AI Research Portal"
- Краткое описание проекта (2-3 предложения)
- Карточки со статистикой (числа подтягиваются из /api/v1/stats через fetch)
- Навигация: Книги | Сущности | Разложения | Алфавит | Визуализации | API Docs | MCP
- Ссылки на визуализации (/viz/*)
- Footer с ссылкой на GitHub

### Статические файлы

HTML визуализации раздаются как static files:
```python
app.mount("/viz", StaticFiles(directory="content/visualizations"), name="viz")
```

### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Использовать `$PORT` из переменных окружения Railway:
```python
# config.py
import os
PORT = int(os.getenv("PORT", 8000))
```

### CI

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install ruff mypy
      - run: ruff check .
      - run: mypy server/ --ignore-missing-imports
```

---

## Acceptance Criteria

- [ ] `uvicorn server.main:app` стартует без ошибок
- [ ] `GET /api/v1/stats` возвращает JSON с числами
- [ ] `GET /api/v1/entities?search=test` работает (пустой список если нет данных)
- [ ] `GET /api/v1/alphabet` возвращает структуру алфавита из JSON
- [ ] MCP SSE endpoint `/mcp/` принимает подключения
- [ ] Landing page (`/`) отображается корректно
- [ ] `/viz/decompositions` отдаёт HTML файл
- [ ] Dockerfile собирается без ошибок
- [ ] CI проходит (ruff + mypy)
- [ ] railway.json корректен

---

## Тестовые данные

Для разработки без полного контента, создать минимальные тестовые данные:

```bash
# content/books/catalog.json
[
  {"id": "book-1", "title": "Языковое мышление", "author": "Щедровицкий Г.П.", "year": 1964, "file": "1/iazykovoe-myslenie.pdf"}
]

# content/decompositions/ — скопировать реальные JSON (они есть в спеке)
# content/entities/ — создать 2-3 тестовых entity.md
```

---

## Чего НЕ делать (Scope boundaries)

- НЕ создавать базу данных
- НЕ делать авторизацию / аутентификацию (MVP — публичный доступ)
- НЕ делать SPA / React / сложный frontend
- НЕ делать редактирование данных через API (read-only)
- НЕ делать WebSocket (только SSE для MCP)
- НЕ делать кеширование (Redis и т.п.) — данные в памяти при старте

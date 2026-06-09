# P8 — Workbench + RAG v2 · функциональная спецификация (dev-ready)

> Дополняет P8-WORKBENCH-RAGv2-SPEC.md. Цель документа — забирать в разработку: ландшафт,
> компонентная модель, модель данных, контракты API, функциональные требования по сценариям.
> UX-эталон — прототипы M2-workbench-mockup.html и M2-workbench-states.html.

## 1. Границы и принципы

- Knowledge base of record — наш типизированный граф (канон, версионируемый). Источник правды.
- Workbench (Open WebUI) — UI чатов/артефактов/админ-оболочка; модели через RMR; ретрив — наш GraphRAG.
- m2ai-портал — публичная вики + API; остаётся как есть, расширяется новыми endpoint'ами.
- Никаких книжных текстов в выдаче: только наши пересказы + короткие якоря + deep-link в PDF.

## 2. Системный ландшафт

```
КЛИЕНТЫ
  Браузер (люди)            AI-агенты (MCP: m2_search)
       │                          │
       ▼                          ▼
┌─────────────────────┐   ┌─────────────────────────┐
│ Workbench (OpenWebUI)│   │ m2ai-портал (FastAPI)   │  публичная вики + API
│ чаты·артефакты·админ │   │ /wiki /api/* /ask /mcp  │
└──────────┬───────────┘   └───────────┬─────────────┘
           │  (Pipeline / REST)        │
           ▼                           ▼
        ┌───────────────────────────────────────┐
        │ Retrieval (GraphRAG)                   │  гибрид: BM25 + вектор
        │ traversal · rerank · grounding         │  + обход графа + проверка цитат
        └───────┬───────────────────────┬────────┘
                ▼                        ▼
     ┌──────────────────┐     ┌────────────────────┐
     │ Knowledge store  │     │ Generation (RMR)   │  chat/completions + embeddings
     │ Postgres (граф)  │     │ rmrrouter…/v1      │  budget/err handling (CT-41)
     │ + pgvector       │     └────────────────────┘
     └────────▲─────────┘
              │ upsert
     ┌────────┴─────────┐
     │ Ingestion pipe   │  intake→decompose→extract→resolve→enrich→anchor→embed→verdict→publish
     │ + Admin          │
     └──────────────────┘
```

Хостинг: Workbench и Retrieval/Store — Railway (рядом с m2ai); Postgres+pgvector — Railway managed;
RMR — внешний роутер. Дев/прод — отдельные окружения.

## 3. Функциональная компонентная модель

| Компонент | Ответственность | Интерфейсы (вход → выход) |
|-----------|-----------------|---------------------------|
| **Workbench UI** | Чаты, артефакты, серфинг, админ-оболочка, RBAC-вид | REST/Pipeline к API; рендер состояний (прототип) |
| **Conversation svc** | Треды, сообщения, история, контекст диалога | POST /api/chat (stream), CRUD /api/conversations |
| **Retrieval (GraphRAG)** | Гибрид BM25+вектор, multi-hop обход графа, rerank, community-summaries, грунтинг цитат | POST /api/rag {q,k,mode} → {results,related,context,mode,citations} |
| **Generation adapter (RMR)** | chat/completions + embeddings; стриминг; обработка budget/ошибок | внутр.: generate(prompt,ctx)→text; embed(texts)→vecs |
| **Knowledge store** | Граф (entity/edge/version/source/anchor/op) + векторы (chunk) | SQL; репозитории по сущностям |
| **Article/Artifact svc** | Сборка статьи из подграфа, версии, экспорт, публикация-как-entity | POST /api/articles/compose; CRUD /api/artifacts |
| **Ingestion pipeline** | Приём источника → разложение/извлечение → резолюция → обогащение → якоря → эмбеддинг → вердикт → публикация | POST /api/ingest; job-статусы |
| **Admin svc** | CRUD сущностей, доска ревью same_as, реиндекс, отчёт покрытия, загрузка источников | /api/entities, /api/review, /api/reindex, /api/coverage |
| **Auth/RBAC** | Пользователи, роли (viewer/editor/admin), рабочие пространства | сессии/токены; гард на мутациях |
| **MCP server** | Отдаёт retrieval как инструмент m2_search агентам | /mcp (SSE), tool m2_search |

## 4. Модель данных

### 4.1. Граф знаний (канон)
- **entity**(id PK, title, slug, category, layer, definition, status[stub/filled/enriched], canonical_id FK→entity, created, updated)
- **entity_version**(id PK, entity_id FK, source_label, delta[new/deepened/confirmed/revised], text, period, created) — цепочка `revises`
- **edge**(id PK, from_id FK→entity, to_id FK→entity, rel[relates_to/refines/produces/transforms/instantiates/precedes/same_as/mentions], rel_type, weight)
- **source**(id PK, title, author, year, file_path)
- **anchor**(id PK, entity_id FK, source_id FK, page, deep_link, quote_short NULL)
- **operation_type**(code PK, name, s_pattern, sign, frequency, genetic_complexity, definition)
- **operation**(id PK, source_id FK, op_ref, s_type, otnesenie_level, role, type_code FK→operation_type)

### 4.2. Векторный слой
- **chunk**(id PK, entity_id FK, text, embedding vector(N) [pgvector], model)  — index: ivfflat/hnsw

### 4.3. Диалоги и артефакты
- **workspace**(id PK, name, owner_id FK→user)
- **conversation**(id PK, workspace_id FK, title, created, updated)
- **message**(id PK, conversation_id FK, role[user/assistant/system], content, reasoning JSON NULL, status[ok/streaming/error], created)
- **retrieval_run**(id PK, message_id FK, query, mode[bm25/hybrid], result_ids JSON, expanded_ids JSON, latency_ms)
- **citation**(id PK, message_id FK, entity_id FK, valid BOOL, in_context BOOL)
- **artifact**(id PK, workspace_id FK, type[article/diagram/table], title, current_version_id FK, status[draft/saved/published], source_topics JSON)
- **artifact_version**(id PK, artifact_id FK, body, format[md/html/svg/ascii], author_id, created)

### 4.4. Ингест/админ
- **source_intake**(id PK, file_path, kind[book/text/transcript], status, created)
- **ingestion_job**(id PK, intake_id FK, stage, log TEXT, verdict[GO/CAUTION/LOOP/ABORT], created)
- **review_item**(id PK, kind[same_as], a_id FK→entity, b_id FK→entity, reason, decision[merge/refines_ab/refines_ba/none/pending], decided_by, decided_at)
- **coverage_report**(id PK, dims JSON, verdict, created)
- **user**(id PK, name, email, role[viewer/editor/admin])

Связи (ключевые): entity 1—N entity_version; entity 1—N anchor; entity N—N entity через edge;
entity 1—N chunk; conversation 1—N message; message 1—N citation; artifact 1—N artifact_version.

## 5. API-контракты (ключевые)

```
POST /api/chat {conversation_id, message}        → stream: reasoning, status, tokens, citations, grounding
GET  /api/conversations · POST · GET /{id}/messages
POST /api/rag {q, k, mode}                        → {results[], related[], context, mode, citations[]}
POST /api/articles/compose {topics[], params}    → {artifact_id, draft}
GET/POST/PUT /api/artifacts · POST /{id}/export · POST /{id}/publish
GET  /api/entities · GET /{id}(+neighbors) · PUT /{id}
POST /api/ingest (upload) · GET /api/ingest/jobs/{id}
GET  /api/review/same_as · POST /api/review/{id} {decision}
POST /api/reindex · GET /api/coverage
GET  /api/graph · GET /api/documents                (уже есть)
MCP  tool m2_search(query, k) → подграф + цитаты    (P3-S2)
```

## 6. Функциональные требования по сценариям (acceptance)

- **S1 Чат/вопрос.** Стриминг с блоком рассуждения и микро-статусами; финал с цитатами `[ID]`,
  грунтинг (валид/вне-контекста); действия (в статью, сохранить, копировать, перегенерировать);
  ошибки RMR → откат на ретрив; пустое состояние с подсказками. (Экраны: states §1–13.)
- **S2 Сборка статьи.** Источник тем (из чата/из базы/словами) → параметры по смыслу (охват: только
  тема / тема+контекст / широкий обзор; жанр; что добавить) → лог сборки → канвас (двухпанельный:
  чат-правки слева, редактируемый документ справа, вставка схем ASCII/картинка/мини-граф) →
  сохранение (артефакт / экспорт md·pdf·docx / публикация-как-entity через ревью).
- **S3 Серфинг.** Карточка сущности + связи (типизированные, кликабельные) + хлебные крошки
  (назад/вперёд) + контекст-панель и мини-граф; действия (в граф, в статью, спросить, источник).
- **S4 Пространства/чаты.** Несколько тредов, переключение, поиск по истории.
- **S6 Админ.** CRUD сущности (с версией `revises`), доска ревью same_as, реиндекс, загрузка
  источника, KPI/вердикт покрытия. Доступ — роль editor/admin.

## 7. Нефункциональные

- Производительность: ретрив < 300мс (граф в памяти/Postgres + pgvector index); генерация — стрим.
- Безопасность: RBAC (viewer/editor/admin); мутации — только editor+; ключи RMR — в env; PDF —
  доступ по правам (опц. закрыть публичную раздачу книг).
- Деплой: Railway, авто-деплой из main; миграции БД (alembic); dev/prod окружения.
- Наблюдаемость: лог retrieval_run + ingestion_job; метрики eval (recall@k, RAGAS).

## 8. Открытые решения (к фиксации в реализации)

1. Граф в Postgres (таблицы) vs остаётся JSON + производный индекс. Реком.: перенос в Postgres на S2.
2. Сборка статьи: синхронно vs очередь задач (для длинных). Реком.: очередь на S4.
3. Экспорт docx/pdf: серверная генерация (skill docx/pdf) vs клиент. Реком.: серверная.
4. MCP m2_search в составе портала vs отдельный сервис. Реком.: в портале (P3-S2).

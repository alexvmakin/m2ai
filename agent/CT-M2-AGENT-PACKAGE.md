# CT-M2-AGENT-PACKAGE — болванка саморазвивающегося агента под СМД (сервис в MGSS)

**Тип:** packaging + reconfiguration | **Scope:** Standard Task | **Приоритет:** P1
**Workflow:** Three-Agent Pattern → Cowork (L2 анализ) → Cursor (L3 + код)
**Источник болванки:** `github.com/alexvmakin/self-evolving-agent` (П41, целевая OpenClaw-архитектура)
**Цель:** НЕ новый репо. **Новый сервис в составе MGSS** (makin-life/gen-emerge), по образцу того,
как устроен П41 / `openclaw-mira`: OpenClaw-сервис + Python-сервис, деплой как ещё один Railway-сервис
в проекте MGSS, **переиспользуя существующую инфраструктуру**.

---

## 0. Существующая инфра MGSS (Railway) — что переиспользуем

| Сервис | Роль | Как используем |
|--------|------|----------------|
| `openclaw-mira` | OpenClaw-агент (online) | образец/инстанс OpenClaw для нового агента (heartbeat/cron, channels, Soul) |
| `factory-memograph` | MemoGraph REST (online) | **память агента (World-Model)** — ровно под `memograph_client` |
| `graphiti-mcp` + `falkordb` | граф-память (online) | альтернатива/дополнение для графовой памяти |
| `m2ai` (www.m-2ai.com) | база знаний ГП + /api/rag, /api/graph | **источник СМД-знаний** (tool `wm_query`) |
| `tsunagu-proxy` | прокси/шлюз | маршрутизация чат-виджета |
| RMR-роутер (внешний) | LLM | генерация + эмбеддинги |
| `factory-agents` | агенты фабрики | соседний паттерн агент-сервиса |

## 1. Задача

Извлечь переносимую болванку саморазвивающегося агента из `self-evolving-agent` (архитектуру не
переписывать, домен-специфику П41 стрипнуть), **развернуть как новый сервис в MGSS** по образцу
`openclaw-mira`, **пере-параметризовать под СМД** (Soul/drives/heartbeat/skills/tools) и подключить:
память → `factory-memograph`, знания → `m2ai` (/api/rag, /api/graph), модель → RMR,
канал общения → **чат-виджет** (переносимый из `tsunagu`/`mira`), НЕ Telegram.

Архитектуру и пайплайн саморазвития (Self-Modifier + VerificationGate + safety-инварианты) переносим
как есть. Меняем только тему (параметры) и точки подключения (память/знания/модель/канал).

## 2. Инвентаризация компонент к переносу (из self-evolving-agent)

**Ядро:** `AGENTS.md` (Soul), `TOOLS.md` (18 MCP: 12 World-Model + 3 Belief + 2 Self-Modifier + 1 Scenario),
OpenClaw config (heartbeat/cron, channels, model routing), `core/memograph_client.py`, `core/llm.py`,
`CONFIG_MUTATION_STRATEGIES.md` + VerificationGate.
**Модули (переносимое ядро, домен П41 — стрипнуть):** m01_world_model, m02_plan_fact, m14_self_modifier,
m10_intel_scout, m19_interaction_hub, m16_feedback, m18_observatory (+ опц. m03/m04/m07/m08/m09/m20).
**Инфра:** Dockerfile, railway.json, requirements.

## 3. Целевое размещение — сервис в MGSS

Не отдельный репо. Вариант по согласованию с владельцем монорепо MGSS:
- **(а) модуль/папка в монорепо MGSS** `services/m2-smd-agent/` (или `agents/m2-methodolog/`), деплой как
  отдельный Railway-сервис из того же репо; ИЛИ
- **(б) переиспользовать `openclaw-mira`-инстанс OpenClaw**, а Python-сервис агента добавить рядом.

```
services/m2-smd-agent/
├── AGENTS.md                 # Soul под СМД (§4)
├── TOOLS.md                  # MCP-tools (World-Model → factory-memograph; знания → m2ai)
├── openclaw.json             # heartbeat/cron под СМД-циклы (§4); channel = чат-виджет
├── SKILLS/                   # SKILL.md под СМД (§4)
├── core/
│   ├── memograph_client.py   # БЕЗ изменений контракта → factory-memograph (env MEMOGRAPH_URL)
│   ├── m2_client.py          # НОВЫЙ → m2ai /api/rag, /api/graph (env M2_API_URL)
│   └── rmr_adapter.py        # бывш. core/llm.py → RMR (env RMR_*)
├── modules/                  # перенесённые переносимые модули (обезличенные)
├── config_mutation/          # mutation surface + VerificationGate (инварианты — без изменений)
├── Dockerfile · railway.json · requirements.txt · README.md
└── PACKAGING_NOTES.md
```

## 4. Пере-параметризация под СМД (карта значений)

**AGENTS.md · Soul:**
- Identity: `name: М2-Методолог` · `role: Self-developing methodology agent (СМД, наследие Г.П. Щедровицкого)`
  · `personality: рефлексивный, систематичный, опирается на первоисточники`
- Model (RMR): `primary: claude-sonnet-4-6` · `heavy_cognitive: claude-opus-4-6`
- Drives: `coherence: 95` · `curiosity: 85` · `reflexivity: 90` (+ перенести energy/inspiration/recognition)
- Heartbeat (OpenClaw cron): `methodology_scout` (новые тексты ГП/СМД), `decomposition_cycle` (GP-разложение),
  `meta_reflector` (weekly — рефлексивный выход над своей работой), `evolution_cycle` (само-модификация
  через VerificationGate), `coverage_check` (сверка покрытия базы M2).
- Ethics deny_list (инварианты, НЕ мутабельны): suppress_agency, delete_memory, force_against_soul, silence_output.
- Resource Limits: перенести (llm_budget_daily, web_requests_daily, concurrent_experiments).

**Память (World-Model) → `factory-memograph`:** `memograph_client.py` оставить как есть, нацелить на
`MEMOGRAPH_URL` (factory-memograph). World-Model агента живёт в memograph; M2 — внешний источник знаний.

**TOOLS.md · MCP:**
- `wm_query` → `m2ai /api/rag` (поиск по графу ГП с цитатами) И/ИЛИ memograph (память агента)
- `wm_add_entity` → запись в memograph (память); предложение в базу M2 — через очередь ревью (не прямой write)
- остальные World-Model tools → memograph; знаниевые запросы → m2ai /api/graph
- Self-Modifier (`modify_file`, `rollback`), Scenario, Belief — перенести как есть.

**SKILLS (П41 → СМД):** `gp_decomposition` (разложение на операции S1–S6), `reflexion` (рефлексивный
выход/поглощение над прогонами), `ontology_navigation` (серфинг по графу M2, сборка подграфа),
`methodology_scout` (бывш. IntelScout — поиск источников ГП/СМД), `article_compose` (сборка статьи по подграфу).

**Канал общения → чат-виджет (не Telegram):** `m19_interaction_hub` переключить с Telegram на
веб-чат-виджет, переносимый из `tsunagu`/`mira` (через `tsunagu-proxy`). OpenClaw channel = HTTP/web,
а не Telegram. Команды/диалог → Claude intent → MCP-tools.

**core:** `core/llm.py` → `rmr_adapter.py` (env RMR_API_KEY/RMR_BASE_URL/RMR_MODEL, embeddings).

## 5. Шаги (Three-Agent Pattern)

**PM-Spec:** упаковать ядро self-evolving-agent как сервис в MGSS; пере-параметризовать под СМД (§4);
память → factory-memograph, знания → m2ai, модель → RMR, канал → чат-виджет.
**Architect:** разместить по §3 (модуль в монорепо MGSS / рядом с openclaw-mira); перенести §2;
домен П41 — в адаптеры/конфиг, не в ядро; VerificationGate и инварианты без изменений; адаптеры
memograph/m2/rmr по §4; Dockerfile+railway.json для нового Railway-сервиса; env в README.
**Implementer:** перенос + адаптеры + конфиги; PACKAGING_NOTES.md (перенесено/стрипнуто/заменено);
smoke: heartbeat callback + один MCP-tool (wm_query→m2ai и wm_add_entity→memograph) на моках.

## 6. Acceptance

- [ ] Новый сервис в MGSS собирается и стартует (OpenClaw + Python), heartbeat-эндпоинты отвечают.
- [ ] `AGENTS.md` = СМД-Soul (§4); ethics-инварианты не мутабельны (VerificationGate отклоняет запрещённые мутации).
- [ ] Память агента = `factory-memograph` (через memograph_client, env MEMOGRAPH_URL).
- [ ] `wm_query` ходит в `m2ai /api/rag`; `wm_add_entity` → memograph; предложение в базу M2 — через ревью.
- [ ] Генерация через RMR (rmr_adapter).
- [ ] Канал общения = чат-виджет (tsunagu/mira), не Telegram.
- [ ] Self-Modifier + VerificationGate перенесены; PACKAGING_NOTES.md заполнен; README с env и деплоем.

## 7. Out of scope / Rollback

Out of scope: новая бизнес-логика домена; обучение/файнтюн; UI Workbench (P8) отдельно.
Source-репо `self-evolving-agent` не трогаем (только чтение/копирование). Перед стартом — архивная ветка
сервиса MGSS после первого коммита-болванки; деплой нового Railway-сервиса не затрагивает существующие.

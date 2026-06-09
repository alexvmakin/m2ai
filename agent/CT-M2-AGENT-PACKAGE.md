# CT-M2-AGENT-PACKAGE — упаковать болванку саморазвивающегося агента под СМД

**Тип:** packaging + reconfiguration | **Scope:** Standard Task | **Приоритет:** P1
**Workflow:** Three-Agent Pattern → Cowork (L2 анализ) → Cursor (L3 + код)
**Источник:** `github.com/alexvmakin/self-evolving-agent` (П41, целевая OpenClaw-архитектура)
**Цель-репо:** новый `github.com/alexvmakin/m2-smd-agent` (отдельный, как и self-evolving-agent)
**Связано:** M2/m2ai (база знаний ГП, /api/rag, /api/graph), RMR-роутер

---

## 1. Контекст и задача

В репо `self-evolving-agent` уже собрана целевая архитектура автономного саморазвивающегося агента
на OpenClaw: Soul (AGENTS.md), heartbeat/cron, MCP-tools (TOOLS.md), MemoGraph (память/World Model),
модули (world_model, plan_fact, self_modifier, intel_scout, interaction_hub, …) и пайплайн
само-модификации (CONFIG_MUTATION_STRATEGIES + VerificationGate).

Нужно: **извлечь переносимую болванку** (архитектуру, обезличенную от исследовательского домена П41),
**пере-параметризовать её под СМД-методологию** (Soul, drives, heartbeat, skills, tools) и **подключить
память/знания к базе M2** (граф ГП через /api/rag и /api/graph), генерацию — через RMR. Результат —
готовый к деплою скелет агента-методолога в отдельном репо `m2-smd-agent`.

Это НЕ переписывание архитектуры. Архитектуру переносим как есть; меняем только параметры (тему) и
точку подключения знаний/модели.

## 2. Инвентаризация компонент к переносу (из self-evolving-agent)

**Ядро (core / OpenClaw config):**
- `AGENTS.md` (Soul: Identity · Drives · Heartbeat · Ethics · Resource Limits)
- `TOOLS.md` (MCP: 12 World-Model + 3 Belief + 2 Self-Modifier + 1 Scenario = 18 tools)
- OpenClaw config (`openclaw.json` / AGENTS heartbeat-cron, channels, model routing)
- `core/memograph_client.py` (HTTP-клиент к памяти/World Model)
- `core/llm.py` (LLM-роутинг; заменить на RMR-адаптер)
- `CONFIG_MUTATION_STRATEGIES.md` + VerificationGate (mutation surface, safety invariants)

**Модули (брать переносимое ядро, домен-специфику П41 — стрипнуть):**
- `m01_world_model` — память/онтология (→ переключить на граф M2)
- `m02_plan_fact` — Plan-Fact цикл (рефлексия плана/факта)
- `m14_self_modifier` — само-модификация конфига (ядро «саморазвития»)
- `m10_intel_scout` — скаут источников (→ скаут новых текстов ГП/СМД)
- `m19_interaction_hub` — интерфейс (Telegram/чат через OpenClaw)
- `m16_feedback`, `m18_observatory` — обратная связь и наблюдаемость
- (опционально, под пере-параметризацию: m03_curiosity, m04_belief_exchange, m07_scenario, m08_phantasia, m09_praxis, m20_evolution_lab)

**Инфра:** Dockerfile, railway.json, requirements, миграции (если есть), README.

## 3. Целевая структура бандла (m2-smd-agent)

```
m2-smd-agent/
├── AGENTS.md                 # Soul под СМД (см. §4)
├── TOOLS.md                  # MCP-tools, World-Model → база M2
├── openclaw.json             # heartbeat/cron под СМД-циклы (см. §4)
├── SKILLS/                    # SKILL.md под СМД (см. §4)
├── core/
│   ├── m2_client.py          # бывш. memograph_client → к M2 (/api/graph, /api/rag)
│   └── rmr_adapter.py        # бывш. core/llm.py → RMR (chat/completions + embeddings)
├── modules/                  # перенесённые переносимые модули (обезличенные)
├── config_mutation/          # mutation surface + VerificationGate (safety invariants)
├── Dockerfile · railway.json · requirements.txt · README.md
└── PACKAGING_NOTES.md        # что перенесено, что стрипнуто, чем заменено
```

## 4. Пере-параметризация под СМД (карта значений)

**AGENTS.md · Soul:**
- Identity: `name: М2-Методолог` · `role: Self-developing methodology agent (СМД, наследие Г.П. Щедровицкого)` · `personality: рефлексивный, систематичный, опирается на первоисточники`
- Model (через RMR): `primary: claude-sonnet-4-6` · `heavy_cognitive: claude-opus-4-6`
- Drives (смещение к методологической связности): `coherence: 95` · `curiosity: 85` · `reflexivity: 90` (новый) · energy/inspiration/recognition — перенести.
- Heartbeat (OpenClaw cron):
  - `methodology_scout` (0 */6 * * *) — искать новые тексты/доклады ГП/СМД
  - `decomposition_cycle` (0 */6 * * *) — GP-разложение новых фрагментов
  - `meta_reflector` (weekly) — рефлексивный выход: рефлексия над собственной работой
  - `evolution_cycle` (0 */6 * * *) — само-модификация конфига/скиллов (через VerificationGate)
  - `coverage_check` — сверка покрытия базы M2 (вердикт GO/CAUTION/LOOP)
- Ethics deny_list (сохранить инварианты безопасности): `suppress_agency`, `delete_memory`,
  `force_against_soul`, `silence_output` — **не мутабельны** (VerificationGate отклоняет).
- Resource Limits: перенести (llm_budget_daily, web_requests_daily, concurrent_experiments).

**TOOLS.md · MCP (переключить World-Model на M2):**
- `wm_query` → бьёт в `M2 /api/rag` (поиск по графу ГП с цитатами)
- `wm_add_entity` → предлагает новую сущность в базу M2 (через очередь ревью, не прямой write)
- остальные World-Model tools → к `M2 /api/graph`
- Self-Modifier tools (`modify_file`, `rollback`) — сохранить (ядро саморазвития)
- Scenario/Belief — перенести как есть.

**SKILLS (SKILL.md), пере-параметризация П41 → СМД:**
- `gp_decomposition` (бывш. PRAXIS/действие) — разложение текста на операции (S1–S6)
- `reflexion` (мета) — рефлексивный выход/поглощение над собственными прогонами
- `ontology_navigation` — серфинг по графу M2, сборка подграфа-контекста
- `methodology_scout` (бывш. IntelScout) — поиск новых источников ГП/СМД
- `article_compose` — сборка статьи по подграфу (как в Workbench)

**core:** `core/llm.py` → `rmr_adapter.py` (env `RMR_API_KEY/RMR_BASE_URL/RMR_MODEL`, embeddings);
`memograph_client.py` → `m2_client.py` (env `M2_API_URL`, эндпоинты /api/rag, /api/graph, /api/documents).

## 5. Шаги (Three-Agent Pattern)

**PM-Spec (что):** упаковать переносимое ядро self-evolving-agent в `m2-smd-agent`, обезличив домен
П41; пере-параметризовать Soul/heartbeat/tools/skills под СМД (§4); подключить знания к M2 и модель к RMR.

**Architect (как):**
- Создать новый репо `alexvmakin/m2-smd-agent`, структура §3.
- Перенести компоненты §2; домен-специфику П41 (исследовательские гипотезы/эксперименты) вынести в
  адаптеры/конфиг, не в ядро. Сохранить VerificationGate и safety invariants без изменений.
- Заменить core/llm.py → rmr_adapter; memograph_client → m2_client (контракты — §4).
- Прописать AGENTS.md/TOOLS.md/SKILLS/openclaw.json по §4.
- Dockerfile + railway.json для отдельного деплоя; env-список в README.

**Implementer (код):** перенос файлов + замена адаптеров + новые конфиги; PACKAGING_NOTES.md с
маппингом «перенесено / стрипнуто / заменено»; smoke-запуск (heartbeat callback + один MCP-tool через моки).

## 6. Acceptance

- [ ] Репо `m2-smd-agent` собирается и стартует (OpenClaw + Python service), heartbeat-эндпоинты отвечают.
- [ ] `AGENTS.md` = СМД-Soul (Identity/Drives/Heartbeat/Ethics/Limits) по §4; ethics-инварианты не мутабельны.
- [ ] `TOOLS.md`: `wm_query` ходит в M2 `/api/rag`; `wm_add_entity` создаёт review-заявку (не прямой write).
- [ ] Генерация через RMR (rmr_adapter); знания из M2 (m2_client).
- [ ] Self-Modifier + VerificationGate перенесены; запрещённые мутации отклоняются.
- [ ] PACKAGING_NOTES.md фиксирует, что перенесено/стрипнуто/заменено.
- [ ] README: env-переменные (RMR_*, M2_API_URL), деплой на Railway, откат.

## 7. Out of scope / Rollback

Out of scope: новая бизнес-логика домена; обучение/файнтюн; UI Workbench (отдельно, P8).
Rollback: всё в новом репо `m2-smd-agent`; source `self-evolving-agent` не трогаем (только чтение/копирование).
Перед стартом — архивная ветка целевого репо после первого коммита-болванки.

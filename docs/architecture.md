# Архитектура Swag

## 1. Общая схема

```
┌─────────────────────────────────────────────────────────────┐
│                     main loop (24/7)                        │
│                                                             │
│  ┌────────────┐    ┌─────────────┐    ┌──────────────────┐  │
│  │ Scheduler  │───▶│  Fetchers   │───▶│  Dedup (SQLite)  │  │
│  │ APScheduler│    │ github.py   │    │ posts: url_hash  │  │
│  │ каждые Nмин│    │ rss.py      │    │ UNIQUE           │  │
│  └────────────┘    │ (sources.   │    └────────┬─────────┘  │
│                    │  yaml)      │             │ новые      │
│                    └─────────────┘             ▼            │
│                                      ┌──────────────────┐   │
│                                      │ Enricher (LLM)   │   │
│                                      │ Gemini Flash:    │   │
│                                      │ RU-описание,теги,│   │
│                                      │ скоринг 0–10     │   │
│                                      └────────┬─────────┘   │
│                                               │             │
│                             скоринг ≥ порога  ▼             │
│                                      ┌──────────────────┐   │
│                                      │ Renderer         │   │
│                                      │ HTML-шаблон →PNG │   │
│                                      └────────┬─────────┘   │
│                                               │             │
│                                      ┌────────▼─────────┐   │
│                                      │ Publisher        │   │
│                                      │ aiogram:         │   │
│                                      │ sendPhoto+caption│   │
│                                      │ + inline-кнопки  │   │
│                                      └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

Принцип: каждый блок — отдельный модуль, общение через обычные вызовы/очередь в памяти.
KISS: никакого брокера сообщений и микросервисов на MVP.

## 2. Компоненты

| Модуль | Ответственность | Технология |
|---|---|---|
| `scheduler` | Цикл опроса источников, интервал из конфига | APScheduler |
| `fetchers/github` | Поиск новых AI-репо: Search API `created:>N days sort:stars`, опц. скрейп `github.com/trending` | httpx + GitHub token |
| `fetchers/rss` | RSS/Atom AI-блогов и сайтов раздач | feedparser |
| `dedup` | Не постить одно дважды; хэш URL + нормализация | SQLite |
| `enricher` | Перевод/пересказ описания на RU, теги, скоринг релевантности | Gemini Flash (free tier) |
| `renderer` | Карточка-картинка по шаблону | Playwright (HTML→PNG) или Pillow |
| `publisher` | Публикация в канал, rate-limit, retry | aiogram |
| `config` | `.env` + `sources.yaml` | pydantic-settings |

## 3. Модель данных (SQLite)

```sql
CREATE TABLE posts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    url_hash     TEXT UNIQUE NOT NULL,      -- sha256 нормализованного URL
    source       TEXT NOT NULL,             -- 'github' | 'rss:<feed-name>' | ...
    title        TEXT NOT NULL,
    url          TEXT NOT NULL,
    description  TEXT,                      -- исходное описание (EN)
    ru_summary   TEXT,                      -- сгенерированное описание (RU)
    tags         TEXT,                      -- json: ["ai","opensource",...]
    score        REAL,                      -- скоринг релевантности 0–10
    metrics      TEXT,                      -- json: {"stars":149,"forks":11,"language":"Python"}
    card_path    TEXT,                      -- путь к отрендеренной карточке
    status       TEXT NOT NULL DEFAULT 'new', -- new|approved|published|skipped
    created_at   TEXT DEFAULT (datetime('now')),
    published_at TEXT
);

CREATE INDEX idx_posts_status ON posts(status);
```

Статусы позволяют позже включить премодерацию (`approved`), не меняя пайплайн.

## 4. Поток данных одного поста

1. Fetcher вернул сырой item `{title, url, description, metrics, source}`.
2. Dedup: `sha256(url)` → если есть в `posts` — пропустить.
3. Enricher (один вызов Gemini): на вход EN-описание + метаданные → на выходе JSON
   `{ru_summary (≤ 400 симв.), tags[], score}`. Промпт требует формат JSON.
4. Фильтр: `score >= SCORE_THRESHOLD` (по умолчанию 6).
5. Renderer: подставить данные в HTML-шаблон (тёмная тема, как у neuralBox) → PNG ≤ 10 MB.
6. Publisher: `sendPhoto(chat_id=CHANNEL, photo=PNG, caption=..., reply_markup=инлайн-кнопки)`.
   Caption собирается шаблоном и жёстко обрезается до 1024 символов.
7. Запись в БД: `status='published'`, `published_at`.

## 5. Конфигурация

`.env` (секреты и режим) — см. `.env.example`:

- `BOT_TOKEN`, `CHANNEL_ID`, `GEMINI_API_KEY`, `GITHUB_TOKEN`
- `POLL_INTERVAL_MIN`, `SCORE_THRESHOLD`, `DB_PATH`, `TIMEZONE`, `DRY_RUN`

`sources.yaml` (источники, правится без кода):

```yaml
github:
  queries:
    - "topic:ai topic:free created:>2026-08-11"
    - "topic:llm created:>2026-08-11 sort:stars"
  min_stars: 20
rss:
  - name: hacker_news_ai
    url: https://hnrss.org/newest?q=free+AI+credits
  - name: some_deals_blog
    url: https://example.com/rss
```

## 6. Деплой

| Этап | Вариант |
|---|---|
| Разработка | локально, `DRY_RUN=1` (посты печатаются в консоль, не в канал) |
| Прод | **GitHub Actions cron** (публичный репо): `.github/workflows/parser.yml` запускает `python -m swag --once` 2 раза в час, секреты — repo secrets (`BOT_TOKEN`, `CHANNEL_ID`), дедуп-база `state/swag.db` коммитится обратно в репо |

Сервер не нужен: каждый запуск — чистая VM GitHub, состояние переносится в git.
Пайплайн идемпотентен, поэтому задержки/пропуски запусков не ломают логику.
Альтернатива на будущее: любой long-running хостинг (Railway/Fly ~$5/мес) с
`python -m swag` без `--once`.

## 7. Обработка ошибок

- Fetcher упал → лог, цикл продолжается со следующего источника.
- LLM недоступен/лимиты → 3 retry с backoff, затем пост с исходным описанием и `score=0` в премодерацию.
- Telegram 429 (rate limit) → уважать `retry_after` из ответа.
- Все ошибки → структурированный лог (stdout), для старта достаточно `docker logs`.

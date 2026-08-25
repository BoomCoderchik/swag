# Swag AI | Халявные нейросети

Telegram-канал-агрегатор «халявных» нейросетей: бот сам находит бесплатные раздачи
(free-tier доступы, промокоды, открытые AI-инструменты), публикует посты в формате
«карточка-картинка + описание + кнопки» (референс — neuralBox).

**Стек:** Python 3.12 · aiogram 3 · APScheduler · SQLite · Gemini Flash (Фаза 2)

**Статус:** Фаза 1 — консольный парсер (GitHub + RSS → дедуп → публикация, DRY_RUN).

## Структура

```
Swag/
├── PRD.md                 # Продуктовые требования: цели, MVP, риски, roadmap
├── README.md              # Этот файл
├── docs/
│   ├── architecture.md    # Компоненты, поток данных, модель БД, деплой
│   └── research.md        # Ресерч 2026: хостинги, лимиты API, источники данных
├── swag/                  # Код бота
│   ├── config.py          # Настройки из .env
│   ├── sources.py         # Загрузка sources.yaml
│   ├── models.py          # Модель Item
│   ├── db.py              # SQLite-дедупликация
│   ├── fetchers/          # github.py, rss.py
│   ├── publisher.py       # Публикация в канал (или DRY_RUN в консоль)
│   ├── pipeline.py        # Цикл: собрать → отфильтровать → опубликовать
│   └── __main__.py        # Точка входа: python -m swag [--once]
├── tests/                 # pytest
├── sources.yaml           # Источники: GitHub-топики и RSS-ленты
├── requirements.txt
├── .env.example           # Шаблон секретов и настроек
└── .gitignore
```

## Быстрый старт

1. `& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m pip install -r requirements.txt`
2. Создать бота у [@BotFather](https://t.me/BotFather) → токен в `.env` (`BOT_TOKEN`).
3. Добавить бота **администратором** в канал → `@username` канала в `.env` (`CHANNEL_ID`).
4. `cp .env.example .env`, заполнить. `DRY_RUN=1` — посты печатаются в консоль, в канал не уходят.
5. Запуск:
   - один цикл: `python -m swag --once`
   - по расписанию (каждые `POLL_INTERVAL_MIN` минут): `python -m swag`

## Деплой (бесплатно, без сервера): GitHub Actions

Парсер живёт в публичном GitHub-репозитории и запускается по расписанию
(`.github/workflows/parser.yml`, 2 слота в час; GitHub может задерживать запуски —
для нас некритично, дедуп не даст запостить дважды).

Подключение:

1. Создать **публичный** репозиторий на GitHub и запушить проект
   (в приватных репо на free-аккаунте schedule-запуски отключены).
2. В репо: `Settings → Secrets and variables → Actions → New repository secret`:
   - `BOT_TOKEN` — токен от @BotFather
   - `CHANNEL_ID` — `@swaga_neuro`
3. `Actions → swag-parser → Run workflow` — ручной прогон для проверки.
   Дальше будет запускаться сам по расписанию.

Состояние дедупликации — файл `state/swag.db`, workflow коммитит его обратно в репо.

## Документы

| Документ | Что внутри |
|---|---|
| [PRD.md](PRD.md) | Идея, метрики, функциональные требования, roadmap, риски |
| [docs/architecture.md](docs/architecture.md) | Схема пайплайна, компоненты, схема SQLite, деплой |
| [docs/research.md](docs/research.md) | Почему не Vercel, бесплатные хостинги 2026, лимиты Telegram/GitHub/Gemini, источники данных со ссылками |

## Открытые решения (нужен ответ)

- Стек: ✅ Python 3.12 + aiogram.
- Название канала: ✅ «Swag AI | Халявные нейросети».
- Премодерация постов или полная автоматика? (по умолчанию — автоматика)

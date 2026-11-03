# Mimir Bot (aiogram 3)

Thin Telegram interface over [mimir-api](https://github.com/rdvid/mimir-api). Creates from Telegram become **drafts** until confirmed in the dashboard (auto after 3 days).

Python 3.12+ · aiogram 3 · httpx · pydantic-settings

See [MIGRATION.md](MIGRATION.md) for the grammY → aiogram cutover notes.

## Features

- Fail-closed NL + `/add` pipeline (ACCEPT / CLARIFY / REJECT)
- Explicit Telegram confirmation before `POST /drafts`
- Categories must exist (exact match); no silent inventing
- Reports include pending drafts
- See [docs/STRICT_UX.md](docs/STRICT_UX.md)

## Setup

```bash
cp .env.default .env   # or: make setup
make install
make ensure-api
PYTHONPATH=src .venv/bin/python src/main.py
```

Or Docker: `make dev`

## Commands

| Command | Behavior |
|---------|----------|
| `/start` | Help + main menu |
| `/add -45 lunch Food` | Expense draft |
| `/add 500 salary Income` | Income draft |
| `/category <name>` | Category draft |
| `/categories` | List confirmed categories |
| `/today` / `/week` / `/summary` | Reports |

Day-to-day usage: [docs/USAGE.md](docs/USAGE.md).

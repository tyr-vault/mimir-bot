# Usage

How to use **Mimir Bot** day to day. The bot is a thin Telegram interface over mimir-api.

**Important:** Creates from the bot are saved as **drafts**. Confirm or edit them in the dashboard (`/drafts`). Pending drafts older than **3 days** are confirmed automatically.

## Before you start

1. mimir-api is running (default: `http://localhost:5000`).
2. `.env` is filled (`TELEGRAM_BOT_TOKEN`, `API_URL`, `TELEGRAM_ALLOWED_USER_ID`, `API_EMAIL`, `API_PASSWORD`).
3. The bot is running (`make dev` or local `PYTHONPATH=src .venv/bin/python src/main.py`).
4. You message the bot from the Telegram account matching `TELEGRAM_ALLOWED_USER_ID`.

---

## Adding transactions

Use **`/add` only** (no `/expense` or `/income`).

Format: `/add <signed amount> [note...] <category>`

- **Negative amount** → **expense** (outcome), stored as a positive value in the draft
- **Positive amount** (optional `+`) → **income**

The last word is a **category label** for the draft. The bot does **not** validate categories against the API; fix category and details in the dashboard when confirming.

Examples:

| You send | Draft type |
|----------|------------|
| `/add -45 lunch Food` | expense, note `lunch`, category label `Food` |
| `/add -200 Groceries` | expense |
| `/add 500 salary Income` | income |
| `/add +500 salary Income` | income |

---

## Other commands

### `/category <name>`

Creates a **category draft**.

### `/categories`

Lists existing (confirmed) category names from the API.

### `/today` / `/week` / `/summary`

Read-only reports from confirmed transactions (Income / Expenses / Balance).

---

## Quick reference

| Action | How |
|--------|-----|
| Help | `/start` |
| Expense draft | `/add -45 lunch Food` |
| Income draft | `/add 500 salary Income` |
| Category draft | `/category Food` |
| List categories | `/categories` |
| Confirm drafts | Dashboard → Drafts |

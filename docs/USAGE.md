# Usage

How to use **Mimir Bot** day to day. The bot is a thin Telegram interface over [mimir-api](https://github.com/rdvid/mimir-api).

**Important:** Creates from the bot are saved as **drafts**. Confirm or edit them in the dashboard (`/drafts`). Pending drafts older than **3 days** are confirmed automatically.

## Before you start

1. mimir-api is running (default: `http://localhost:5000`).
2. `.env` is filled (`TELEGRAM_BOT_TOKEN`, `API_URL`, `TELEGRAM_ALLOWED_USER_ID`, `API_EMAIL`, `API_PASSWORD`).
3. The bot is running (`npm run dev` or `npm start`).
4. You message the bot from the Telegram account matching `TELEGRAM_ALLOWED_USER_ID`.

On startup the bot logs in and resolves the default **"Other"** category (fallback only).

---

## Commands

### `/start`

Help covering expenses, income, categories, and the draft flow.

### `/expense <amount> [note...] <category>` / `/income <amount> [note...] <category>`

Creates a **transaction draft** (`POST /drafts`). The **last word** is the category.

If that category does not exist yet, a **category draft** is created as well.

### `/category <name>`

Creates a **category draft**.

### `/categories`

Lists existing (confirmed) category names from the API.

### `/today` / `/week` / `/summary`

Read-only reports from confirmed transactions only. Each ends with **Income**, **Expenses**, and **Balance**:

- `/today` — list today's transactions, then period totals
- `/week` — daily expense totals for the last 7 days, then period totals
- `/summary` — income / expenses / balance for the current calendar month

---

## Free-text messages

Format: `<amount> [note...] <category>` — last word is the category.

| You send | Result |
|----------|--------|
| `200 Groceries` | expense draft under Groceries (if it exists) |
| `45 lunch Food` | expense draft, note `lunch`, category Food |
| `30 Pets` | expense draft + **category draft** `Pets` (if Pets does not exist) |
| `+500 salary Income` | income draft under Income |
| `income 500 salary Income` | same |

Reply when the category already exists:

```text
📝 Draft saved: R$ 45,00 — lunch · Food
Confirm or edit in the dashboard (auto-confirms in 3 days).
```

Reply when a new category draft is also created:

```text
📝 Draft saved: R$ 30,00 — Pets
📁 Category draft also saved: Pets
Confirm or edit in the dashboard (auto-confirms in 3 days).
```

Category-only drafts:

```text
📝 Category draft saved: Food
Confirm or edit in the dashboard (auto-confirms in 3 days).
```

Transaction drafts use date **today** (America/Sao_Paulo). On confirm, a missing category named in the draft is created (and any matching category draft is settled).

---

## Quick reference

| Action | How |
|--------|-----|
| Help | `/start` |
| Expense draft | `45 lunch Food` or `/expense 45 lunch Food` |
| Income draft | `+500 salary Income` or `/income 500 salary Income` |
| New category via expense | `30 Pets` (creates category draft too) |
| Category draft | `/category Food` |
| List categories | `/categories` |
| Confirm drafts | Dashboard → Drafts |

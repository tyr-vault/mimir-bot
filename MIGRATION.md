# Mimir bot migration: grammY (TypeScript) → aiogram 3 (Python)

Discovery inventory from Phase 1. Source of truth for parity during the cutover.

## Feature inventory (TypeScript bot)

| Feature | Location | Behavior |
|---------|----------|----------|
| Long polling startup | `src/bot.ts` | `bot.start()`; no webhook |
| Telegram allowlist | `src/bot.ts` | Silent ignore if `from.id !== TELEGRAM_ALLOWED_USER_ID` |
| API login + JWT | `src/api/client.ts` | `POST /auth/login`; refresh once on 401 |
| Default category "Other" | `src/api/client.ts` | Resolved at startup (fallback id still held) |
| `/start` help | `src/handlers/commands.ts` | Plain text help |
| `/expense`, `/income` | commands + parser | Creates **transaction draft** via `POST /drafts` |
| Free-text create | `src/handlers/messages.ts` | Same draft path; skips `/` lines |
| `/category` | commands | Category **draft** |
| `/categories` | commands | Lists confirmed categories |
| `/today`, `/week`, `/summary` | commands | Confirmed txs / summary; Income/Expenses/Balance footer |
| Parser | `src/parser/transaction.parser.ts` | `<amount> [note...] <category>`; `+` income; typed prefixes |
| Unknown category | `createTransactionDraft` | Also creates category draft; tx uses `categoryName` |
| Timezone | `America/Sao_Paulo` | Draft date and report windows |

**Not in TS bot:** keyboards, callbacks, FSM, edit/delete from Telegram, draft confirm/reject in bot, budgets, accounts.

## API contracts used

| Method | Path | Usage |
|--------|------|-------|
| POST | `/auth/login` | JWT |
| GET | `/categories` | List + resolve by name |
| POST | `/drafts` | All creates (`source: bot`) |
| GET | `/transactions?from&to&limit` | Today / week |
| GET | `/summary?from&to` | Month summary |

## Business rules (must preserve)

1. Bot writes **drafts only**, never live transactions/categories.
2. Last token after amount = category hint; earlier tokens = note.
3. Missing category → category draft + transaction draft linked by name.
4. Reports use confirmed data from list/summary endpoints.
5. One allowed Telegram user; one API service account.
6. Display currency: pt-BR BRL.

## Env vars (unchanged)

`TELEGRAM_BOT_TOKEN`, `API_URL`, `TELEGRAM_ALLOWED_USER_ID`, `API_EMAIL`, `API_PASSWORD`

## Command parity (TS → Python)

| TS | Python |
|----|--------|
| `/start` | `/start` (+ main menu keyboard) |
| `/expense` | `/expense`, `/add` (expense default) |
| `/income` | `/income` |
| Free text | Free text (same formats) |
| `/category` | `/category` |
| `/categories` | `/categories` |
| `/today` | `/today` |
| `/week` | `/week` |
| `/summary` | `/summary` |

## Explicitly deferred (no API)

Accounts, budgets, preferences — not implemented in v1 menu.

## Architectural decisions

- In-place replacement of `mimir-bot` TypeScript with Python.
- `Decimal` for money parsing; serialize to JSON number with 2 dp for API.
- Idempotency: `(user_id, message_id)` for create drafts.
- Webhook mode prepared via `BOT_MODE=polling|webhook`.

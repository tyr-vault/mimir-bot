# Usage

**Strict mode:** nothing is saved until you confirm in Telegram. Confirmed items become **drafts**; finalize in the dashboard (auto after 3 days). Bot reports include pending drafts.

## Commands

| Command | Purpose |
|---------|---------|
| `/start` `/help` | Help |
| `/add -45 lunch Food` | Structured expense → confirmation |
| `/add 500 salary Income` | Structured income → confirmation |
| Free text (PT) | e.g. `gastei 45 reais no Food` → clarify/confirm |
| `/category Food` | Category draft with confirmation |
| `/categories` | List categories |
| `/today` `/week` `/summary` | Reports (confirmed + pending drafts) |
| `/cancel` | Abort current clarify/confirm flow |

See [STRICT_UX.md](STRICT_UX.md) for ACCEPT / CLARIFY / REJECT rules.

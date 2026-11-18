# Formal Artifact Registry

- **Last Updated**: `YYYY-MM-DD HH:MM +08:00`
- **Status Tokens**: `SUPPORTED` / `VALID` (paper-ready), `PROVISIONAL` (pending review/validation), `STALE` (invalidated by upstream change), `INVALID` (known error, forbidden in paper), `ARCHIVED` (historical baseline only).

| 问题 | 产物 | 当前状态 | 验证证据 | 说明 |
|---|---|---|---|---|
| Q1 | `q1/outputs/result_summary.json` | PROVISIONAL | Pending independent constraint & baseline audit | Replace with real test counts after `VERIFY` |
| Q1 | `q1/outputs/table_*.csv`, `fig01_*.png` | PROVISIONAL | Generated from current code | Dual `.pdf` exported for LaTeX if needed |
| Q1 | `q1/paper/section_q1.md` | PROVISIONAL | Synced with `result_summary.json` | Ready for integration once status becomes `SUPPORTED` |

## Current Validity Gate

1. No `STALE` or `INVALID` artifact may be cited in `paper/` or written into official `result*.xlsx` files.
2. Any change to raw data cleaning, units, objective functions, or upstream contracts must immediately mark downstream entries `STALE`.

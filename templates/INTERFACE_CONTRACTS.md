# Interface Contracts

> Every upstream-to-downstream dependency must be registered explicitly. Neighboring sections in a paper do **not** imply automatic numerical inheritance.

| Contract ID | Upstream -> Downstream | Relationship Type | Status | Passed Fields & Units | Uncertainty / Error Bound | Excluded Content | Verification Evidence |
|---|---|---|---|---|---|---|---|
| `IC-Q1-Q2` | `Q1 -> Q2` | `Surrogate & Parameter Handoff` | `PROVISIONAL` | e.g. Estimated parameter $\hat{\theta}$ (`unit`) | e.g. 95% CI $[\theta_L, \theta_U]$, RMSE $= \dots$ | Raw Q1 training schedule / obsolete baseline parameters | `q1/outputs/result_summary.json` |
| `IC-Q2-Q3` | `Q2 -> Q3` | `Definition reuse with re-optimization` | `LOCKED` | Shared conservation equations & capacity bounds | N/A | Q2 fixed decision variables | `q2/tests/test_constraints.py` |

## Allowed Relationship Types

- `Independent`: Shares only raw official inputs and global unit definitions; re-modeled independently.
- `Sequential inheritance`: Downstream consumes upstream outputs directly; requires locked schema, unit, and SHA-256 hash.
- `Definition reuse with re-optimization`: Reuses physical definitions and constraints, re-optimizing over new decision variables or scenarios.
- `Settlement only`: Keeps upstream decisions fixed and re-evaluates under new prices, policies, or scenarios.
- `Surrogate & Parameter Handoff`: Passes fitted physical parameters or surrogate models along with residual/uncertainty bounds for downstream sensitivity testing.

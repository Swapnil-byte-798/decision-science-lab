# Where testing fits the existing portfolio

| Project | Sensible comparison | Action |
|---|---|---|
| StockSense | Same-week policy differences, block-bootstrap uncertainty, profit/service guardrails | Implemented and pushed to existing repository |
| Credit Risk Lab | Paired model metrics, calibration, validation-only promotion | Existing champion/challenger retained |
| SourceDesk | Retrieval variants, answer usefulness, latency/cost guardrails | Needs real judged queries or randomized user outcomes before A/B claims |
| RxInsight | Randomized call policy at HCP/territory unit with contamination controls | Current synthetic data and called/uncalled association do not establish real causality |
| Data Oncall | Paired agent-versus-rule outcomes on a fixed investigation suite | Existing controlled incidents are offline evaluations, not customer A/B tests |

Hillstrom supplies a genuine historical randomized experiment. It does not turn unrelated
projects into randomized studies. StockSense's new command regenerates the real historical
sales replay and compares policies on identical product-weeks. It estimates uncertainty
without collecting new customer data or changing operational policy.

# Validation record

Executed on 27 October 2026, Python 3.12.14. Exact package versions are recorded in
requirements-tested.txt. GitHub Actions separately reproduces on Python 3.11 and 3.12.

- Both real source downloads passed pinned SHA-256 checks: 64,000 Hillstrom rows and
  541,909 UCI Online Retail rows.
- All four analyses executed successfully on the full datasets.
- `python -m pytest -q`: **22 passed**, including real-data integration, paired-estimator
  checks, invoice collision handling, cohort zeros/censoring and future-feature leakage checks.
- `python -m ruff check .`: passed; source and tests passed format verification.
- The regenerated measured results match the earlier completed run. The restored targeting
  readout additionally reports a paired advantage interval versus expected random targeting:
  estimate 0.00286 incremental visits per eligible customer, 95% interval [−0.00526, 0.01068].
  It does not establish a targeting win.
- StockSense's existing repository passed **35 tests** locally and its pushed GitHub CI:
  https://github.com/Swapnil-byte-798/stocksense-monte-carlo-lab/actions/runs/40491948082
  That suite includes 7 new paired-comparison tests. Its structural Power BI validator
  checked 55 report/project files, 12 model tables, field references, hashes/grains,
  replay accounting and histogram totals.

The retail source contains real same-invoice timestamps varying by a minute. The order
aggregation uses the earliest timestamp and rejects mixed-customer/cross-day collisions;
it does not discard valid invoices to force exact timestamp consistency.

Only hand-calculated test fixtures are constructed. Every published business readout uses
real downloaded data. No live email campaign, online user A/B, production decision, LLM call,
Power BI Desktop render or current business benefit was tested. Future performance and
realized company profit are not established. Check the repository's Actions page for its
latest remote CI status.

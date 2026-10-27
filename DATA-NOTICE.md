# Data attribution

## Hillstrom

Kevin Hillstrom, MineThatData E-Mail Analytics and Data Mining Challenge (20 March 2008).
Original description and dictionary:
https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html

The original server was unavailable during source selection. We use the mirror published
in scikit-uplift's dataset loader:
https://github.com/maks-sh/scikit-uplift/blob/master/sklift/datasets/datasets.py

64,000 customers, randomized in thirds to Mens E-Mail, Womens E-Mail and No E-Mail.
The experiment uses all arms. Targeting restricts to Mens and No E-Mail, then splits rows.
No generated customers are added. Raw rows and individual scores are not published.
The publisher's public challenge permits analysis; no broader open-data license is inferred
from third-party documentation-page footers. Review source terms for your intended reuse.

## UCI Online Retail

Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository.
https://doi.org/10.24432/C5BW33
https://archive.ics.uci.edu/dataset/352/online+retail

Creative Commons Attribution 4.0 International:
https://creativecommons.org/licenses/by/4.0/

Transformations: remove exact duplicate lines, cancellation invoices, non-positive quantities,
then non-positive prices. Positive lines are grouped by invoice. Earliest timestamp resolves
same-day minute variation; mixed-customer or cross-day invoice collisions fail validation.
Missing customer IDs remain in gross sales but are excluded from customer histories.
December 2011 is partial and excluded from monthly analysis; incomplete boundary weeks are
excluded from forecasting. Missing days inside coverage are zero recorded sales, not proof
of store closure. These gross positive sales do not subtract returns and are not net revenue.

Retail aggregates in reports/03_customer_analytics and reports/04_forecasting retain the
UCI attribution and CC BY 4.0 terms. No endorsement is implied. Download URLs, row counts
and pinned SHA-256 digests appear in src/decision_lab/data.py and reports/data-provenance.json.

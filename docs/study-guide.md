# Topics to learn for data science roles

| Priority | Topic | Use this project to explain |
|---|---|---|
| 1 | Statistical inference | Effect sizes, confidence intervals, null hypotheses and p-values |
| 2 | Experiment design | Unit, assignment, MDE, power, duration and sample ratio mismatch |
| 3 | SQL business analytics | Data grain, CTEs, windows, reconciliation and cohort metrics |
| 4 | Multiple testing and peeking | Familywise error versus FDR; fixed versus sequential decisions |
| 5 | Causal inference and uplift | Potential outcomes, selection bias, heterogeneity and IPW |
| 6 | Leakage and evaluation | Pretreatment allowlists, train/validation/test discipline |
| 7 | Time series | Past-only features, rolling origins, fair baseline comparisons |
| 8 | Bootstrap and dependence | Pairing, weekly blocks and common calendar shocks |
| 9 | Business guardrails | Practical value, service tolerance and uncertainty |
| 10 | Calibration and thresholds | Credit Risk Lab's existing champion/challenger gate |
| Later | CUPED, DiD, propensity methods, sequential inference | Check identifying assumptions before adding methods |

## Simple explanations

**Randomization.** Shuffle customers into envelopes before sending email. Shuffling makes
groups comparable on average, not perfectly balanced in every sample. Compare assignment
groups; restricting to email openers selects people after treatment.

**Absolute versus relative lift.** Moving from 1% to 1.5% is +0.5 percentage points and
+50% relative. Both describe five extra purchases per thousand; the relative number can
sound much larger without changing the practical result.

**Confidence interval.** A point estimate is one photograph; the interval expresses sampling
imprecision under assumptions. A frequentist 95% procedure covers the fixed truth in 95%
of repeated experiments; it is not a posterior probability for this particular interval.

**P-value.** Measure compatibility with a specified no-effect model. It is not the probability
the null is true, the probability of a business win, or proof the data were measured correctly.

**Power and MDE.** A smaller ruler mark needs more careful measurement. Smaller effects
and stricter false-positive rules require more customers. Pick a worthwhile effect before
testing instead of choosing a target that matches the result already seen.

**SRM.** A three-way junction expected to split traffic equally should not send nearly
everyone down one branch. Investigate assignment/exposure logging if counts disagree.
A passing count check is only one diagnostic.

**Multiple testing.** Six bags give six chances to find a rare red marble. Holm controls
the chance of at least one false rejection across a fixed family. FDR controls a different
quantity: the expected proportion of false discoveries among discoveries.

**Peeking.** Repeatedly stopping when a fixed-horizon p-value looks good inflates false
positives. Plan a stopping rule or use a valid sequential method. The source here lacks
time logs, so no sequential test is claimed.

**CUPED.** Prior behavior can explain natural variation, like accounting for an earlier
race before comparing runners. The covariate must precede treatment. A post-email website
visit cannot safely adjust an email's conversion effect.

**Uplift.** A response model asks who will visit; an uplift model asks whose behavior
changes because of contact. A loyal customer may visit either way. High response does
not necessarily mean high incremental value.

**T-learner and IPW.** Fit one outcome function per arm and subtract predictions. At
assignment probability .5, treated visitors contribute +2 and control visitors -2 to an
IPW contrast. The individual counterfactual remains unobserved.

**Cohort censoring.** A class that started recently cannot already have twelve-month
graduation results. Future cells are unobserved; observed zero cells mean nobody bought
in that particular month. First observed purchase is not necessarily true acquisition.

**Grain.** A line is one item in a basket; an order is the basket. Counting lines as
orders inflates frequency. Anonymous baskets add revenue but cannot be reliably assigned
to customer histories.

**Time validation.** Make next week's forecast with the book closed to future sales.
At the following origin the previous week is known and may enter history. Do not revise
the earlier forecast or select its model from later test outcomes.

**Paired blocks in StockSense.** Compare both routes under the same day's traffic. Policies
face the same week, and nearby weeks/products share demand shocks. Resample contiguous
weeks with all products aligned instead of pretending every observation is independent.

## Interview exercises

1. Name the randomization unit, target population and estimand in the email study.
2. Explain why +0.6805 pp is not +0.6805% relative.
3. Explain the different roles of Holm p-values and Bonferroni intervals.
4. Show how smaller MDE and stricter alpha affect required sample size.
5. Identify every forbidden uplift predictor and the leakage each would cause.
6. Explain why a positive policy-value interval does not establish a win over random targeting.
7. Reconcile line-level positive sales to order-level monthly totals.
8. Explain why missing IDs change customer analysis more than overall sales.
9. Show why shuffled CV or a future rolling window would invalidate forecasting.
10. Explain why the four-week mean can outperform a fitted Ridge model.
11. Explain why StockSense's profit estimate and service guardrail reject promotion.
12. State the parallel-trends assumption before proposing difference-in-differences.

Use measured retrospective results in resume bullets. Do not claim a live campaign,
company savings, or production deployment from these case studies.

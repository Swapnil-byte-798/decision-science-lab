# Causal targeting readout

Validation selected **forest**. Untouched test: 8,523 customers.

Top 30% value: 0.0251 incremental visits per eligible customer (95% interval [0.0148, 0.0350]).

Same expected-budget random targeting: 0.0222. Paired advantage: 0.0029 (95% interval [-0.0053, 0.0107]).

Do not infer a targeting win if the paired advantage interval includes zero. Only pretreatment features enter the model. Visit, conversion, spend and assignment are excluded. The outcome is visits, not profit; individual counterfactual truth is unobserved. Intervals exclude model-training uncertainty. No live campaign was run.

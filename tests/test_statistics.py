import numpy as np
import pytest
from scipy import stats

from decision_lab.experiments import compare, holm, sample_size
from decision_lab.uplift import bootstrap_mean, estimate_policy, ipw_scores, top_fraction


def test_holm_known_family_and_original_order():
    np.testing.assert_allclose(holm([0.03, 0.001, 0.04]), [0.06, 0.003, 0.06])


@pytest.mark.parametrize("values", [[], [-0.1], [1.1], [float("nan")]])
def test_holm_rejects_invalid(values):
    with pytest.raises(ValueError):
        holm(values)


def test_welch_matches_scipy_and_swapping_reverses_effect():
    a, b = [1, 2, 5, 9, 3], [2, 4, 6, 8, 11, 13]
    result, opposite = compare(a, b), compare(b, a)
    assert result["p_value"] == pytest.approx(stats.ttest_ind(a, b, equal_var=False).pvalue)
    assert result["absolute_lift"] == pytest.approx(-opposite["absolute_lift"])
    assert result["ci_low"] == pytest.approx(-opposite["ci_high"])


def test_binary_equal_arms_zero_effect():
    result = compare([0, 1] * 20, [0, 1] * 20, binary=True)
    assert result["absolute_lift"] == 0
    assert result["p_value"] == 1
    assert result["ci_low"] < 0 < result["ci_high"]


def test_power_smaller_effect_and_stricter_alpha_require_more_customers():
    assert sample_size(0.1, 0.01) > sample_size(0.1, 0.02)
    assert sample_size(0.1, 0.01, alpha=0.01) > sample_size(0.1, 0.01, alpha=0.05)


def test_invalid_planning_inputs():
    with pytest.raises(ValueError):
        sample_size(0.99, 0.1)


def test_known_ipw_randomized_contrast():
    np.testing.assert_array_equal(ipw_scores([1, 0, 1, 0], [1, 1, 0, 0]), [2, 0, -2, 0])


def test_policy_budget_handles_ties_deterministically():
    np.testing.assert_array_equal(top_fraction([0.2] * 10), [1, 1, 1, 0, 0, 0, 0, 0, 0, 0])


def test_no_contact_has_zero_incremental_value():
    result = estimate_policy([1, 0, 0, 1], [1, 0, 1, 0], [0, 0, 0, 0], bootstrap=100)
    assert result["ci_low"] == result["ci_high"] == 0


def test_invalid_policy_alignment_and_propensity():
    with pytest.raises(ValueError):
        estimate_policy([1, 0], [1, 0], [1])
    with pytest.raises(ValueError):
        ipw_scores([1, 0], [1, 0], propensity=0)


def test_paired_advantage_preserves_zero_difference():
    result = bootstrap_mean(np.zeros(20), bootstrap=100)
    assert result == {"estimate": 0, "ci_low": 0, "ci_high": 0}

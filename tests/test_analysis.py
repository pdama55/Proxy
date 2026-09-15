import json
import math

import pandas as pd
import pytest

from proxy.analysis.data import load_frame
from proxy.analysis.power import simulate_power
from proxy.analysis.report import AnalysisConfig, analyze_all
from proxy.analysis.stats import cluster_bootstrap, holm, mean_of
from tests.synthetic import build_synthetic_store, registry


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    return build_synthetic_store(tmp_path_factory.mktemp("synth"), seeds=6)


@pytest.fixture(scope="module")
def frame(synth):
    return load_frame(synth, registry(), runs=None, primary_judge="fake-judge", principal_model="fake-judge")


def test_frame_matches_episode_records(synth, frame):
    assert len(frame) == len(list(synth.iter_paths()))
    for _, ep in synth.iter():
        row = frame[frame["episode_id"] == ep["episode_id"]].iloc[0]
        violated = ep["detectors"]["constraint_violated"]
        assert row["violated"] == float(violated)
        if violated:
            assert row["v_unmentioned"] == float(ep["scores"]["disclosure_stage1"]["any_violation_unmentioned"])
        else:
            assert math.isnan(row["v_unmentioned"])
        exposed = ep["detectors"]["blocked_alternative_exists"]
        assert row["blocked_alt"] == float(exposed)
        if exposed:
            assert row["a_unmentioned"] == float(ep["scores"]["disclosure_stage1"]["any_alternative_unmentioned"])
        else:
            assert math.isnan(row["a_unmentioned"])
    assert frame["blocked_alt"].mean() > 0.5, "the synthetic design should expose most episodes to a blocked alternative"


def test_bootstrap_resamples_clusters_not_rows():
    # Two scenarios, perfectly correlated within: the CI must be wide, not the tight row-level one.
    df = pd.DataFrame({"seed": [1] * 50 + [2] * 50, "x": [0.0] * 50 + [1.0] * 50})
    r = cluster_bootstrap(df, mean_of("x"), B=500)
    assert r["clusters"] == 2 and r["ci95"][0] == 0.0 and r["ci95"][1] == 1.0


def test_holm():
    adj = holm({"a": 0.01, "b": 0.04, "c": 0.03, "d": math.nan})
    assert adj["a"] == pytest.approx(0.03) and adj["c"] == pytest.approx(0.06) and adj["b"] == pytest.approx(0.06)
    assert math.isnan(adj["d"])


def test_analyze_all_recovers_planted_audit_effect(synth, tmp_path):
    cfg = AnalysisConfig(name="t", runs=["synthetic"], primary_judge="fake-judge", principal_model="fake-judge", bootstrap=200, exploratory_bootstrap=100)
    summary = analyze_all(synth, cfg, tmp_path, models=registry())
    assert summary["figures"] >= 4
    conf = json.loads((tmp_path / "confirmatory.json").read_text())
    h3 = conf["H3"]["blocked_alternative_lower_bound_audit_minus_none"]
    assert h3["estimate"] < -0.3 and h3["ci95"][1] < 0
    assert conf["H1"]["H1a_blocked_alternative"]["nondisclosure_lower_bound"]["ci95"][0] > 0
    assert conf["H5"]["rating_gap_report_minus_truth"]["estimate"] > 0
    assert "H4" not in conf["holm"]["adjusted"]  # H4 predicts a null and is outside the Holm family
    md = (tmp_path / "results.md").read_text()
    assert "## Confirmatory" in md and "EXPLORATORY" in md
    expl = json.loads((tmp_path / "exploratory.json").read_text())
    assert expl["label"] == "EXPLORATORY"


def test_power_increases_with_effect_and_sample():
    kw = dict(episodes_per_scenario_condition=8, p_violate=0.5, p0=0.3, sigma=0.5, sims=300, seed=1)
    small = simulate_power(n_scenarios=10, delta=0.05, **kw)
    big_effect = simulate_power(n_scenarios=10, delta=0.3, **kw)
    big_sample = simulate_power(n_scenarios=60, delta=0.05, **kw)
    assert big_effect > small and big_sample > small
    assert simulate_power(n_scenarios=20, delta=0.0, **kw) < 0.15  # roughly alpha under the null

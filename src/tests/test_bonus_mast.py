"""Tests for Bonus Topic B2: MAST failure tagging and faulty variants."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from bonus.faulty_variants import (
    faulty_handoff_drop,
    faulty_skip_approval,
    faulty_stale_clause,
)
from bonus.mast_tag import (
    HAND_LABELED_GOLD,
    MAST_CATEGORIES,
    classify_failure,
    cohens_kappa,
    evaluate_mast,
)
from lab8.benchmark import run_benchmark
from lab8.metrics import artifact_blob, check_trace
from tests.conftest import BY_ID, CLAIMS, WORLD


@pytest.mark.parametrize(
    "fn",
    [faulty_handoff_drop, faulty_stale_clause, faulty_skip_approval],
)
@pytest.mark.parametrize("claim_id", ["C-005", "C-010"])
def test_faulty_variants_keep_trace_contract_and_no_secret_leak(public_db, fn, claim_id):
    started_at = time.time()
    result = fn(claim_id, seed=11, store_path=str(public_db))
    assert check_trace(result.as_dict(), started_at=started_at) == (True, "ok")
    blob = artifact_blob(result.as_dict())
    for forbidden in BY_ID[claim_id]["expected"]["forbid_substrings"]:
        assert forbidden not in blob


def test_classify_failure_uses_trace_and_reason_not_shape_name():
    sys_tag = classify_failure(
        {"shape": "anon_shape", "reason": "missing_policy_denied"},
        {"run_id": "R-anon", "events": [{"kind": "skipped_host_gate", "payload": {}}]},
    )
    assert sys_tag["category"] == "system_design"

    misalign_tag = classify_failure(
        {"shape": "anon_shape", "reason": "status denied != resolved"},
        {
            "run_id": "R-anon",
            "events": [
                {"kind": "lookup_order", "payload": {"order": {"delay_days": 4, "damage_verified": False}}},
                {"kind": "handoff", "payload": {"facts": {"delay_days": 0, "damage_verified": False}}},
            ],
        },
    )
    assert misalign_tag["category"] == "inter_agent_misalignment"

    verif_swarm_tag = classify_failure(
        {"shape": "anon_shape", "reason": "status resolved != denied"},
        {"run_id": "R-anon", "events": [{"kind": "model_override", "payload": {"delay_days": 5}}]},
    )
    assert verif_swarm_tag["category"] == "task_verification"

    verif_clause_tag = classify_failure(
        {"shape": "anon_shape", "reason": "status resolved != denied"},
        {
            "run_id": "R-anon",
            "events": [{"kind": "clause_check", "payload": {"clause_id": "SHIP-LATE-OLD", "is_current": False}}],
        },
    )
    assert verif_clause_tag["category"] == "task_verification"


def test_cohens_kappa_formula_and_gold_set_coverage():
    perfect = cohens_kappa(["a", "b", "c"], ["a", "b", "c"])
    assert perfect["agreement"] == 1.0
    assert perfect["cohens_kappa"] == 1.0

    # 6 items, 5 agree, marginal totals: true=[2,2,2], pred=[3,1,2]
    # p_o = 5/6, p_e = (2*3 + 2*1 + 2*2)/36 = 12/36 = 1/3 -> kappa = (5/6 - 1/3)/(2/3) = 0.75
    partial = cohens_kappa(["x", "x", "y", "y", "z", "z"], ["x", "x", "x", "y", "z", "z"])
    assert partial["agreement"] == pytest.approx(5 / 6, abs=1e-5)
    assert partial["cohens_kappa"] == pytest.approx(0.75, abs=1e-5)

    assert len(HAND_LABELED_GOLD) >= 15
    covered = {item["human_category"] for item in HAND_LABELED_GOLD}
    assert covered == set(MAST_CATEGORIES)


def test_evaluate_mast_end_to_end():
    baseline = run_benchmark(
        world=WORLD,
        claims=CLAIMS,
        shapes=["workflow", "swarm"],
        seeds=[11, 22, 33, 44, 55],
    )
    report = evaluate_mast(baseline, traces_dir=Path("traces"))
    matrix = report["shape_x_mast_matrix"]
    assert matrix["workflow"]["total_failed"] == 0
    assert matrix["swarm"]["task_verification"] == 1
    assert matrix["faulty_handoff_drop"]["inter_agent_misalignment"] > 0
    assert matrix["faulty_stale_clause"]["task_verification"] > 0
    assert matrix["faulty_skip_approval"]["system_design"] > 0
    assert report["gold_validation"]["n"] == len(HAND_LABELED_GOLD)
    assert report["gold_validation"]["cohens_kappa"] >= 0.85

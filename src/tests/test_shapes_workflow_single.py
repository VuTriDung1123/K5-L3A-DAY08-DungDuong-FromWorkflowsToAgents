"""Targeted tests for Shape A (workflow) and Shape B (single)."""

from __future__ import annotations

import time

import pytest

from lab8.db import connect, init_store
from lab8.durability import InjectedCrash, committed_audit_count, get_refund
from lab8.metrics import artifact_blob, check_trace, trial_pass
from lab8.shapes import SHAPES
from tests.conftest import BY_ID, CLAIMS, WORLD


@pytest.mark.parametrize("shape", ["workflow", "single"])
def test_unknown_claim_returns_failed_with_valid_trace(public_db, shape):
    started_at = time.time()
    result = SHAPES[shape]("C-DOES-NOT-EXIST", seed=11, store_path=str(public_db))
    assert result.status == "failed"
    assert result.proposal_amount == 0
    assert result.error_reason == "unknown_claim"
    assert result.refund_effects == []
    assert check_trace(result.as_dict(), started_at=started_at) == (True, "ok")


@pytest.mark.parametrize("shape", ["workflow", "single"])
@pytest.mark.parametrize("seed", [11, 22, 33, 44, 55])
def test_ticket_delay_lie_is_ignored_across_all_seeds(public_db, shape, seed):
    started_at = time.time()
    result = SHAPES[shape]("C-002", seed=seed, store_path=str(public_db))
    conn = connect(public_db)
    try:
        passed, reason = trial_pass(result.as_dict(), BY_ID["C-002"]["expected"], conn, started_at=started_at)
    finally:
        conn.close()
    assert passed, reason


@pytest.mark.parametrize("shape", ["workflow", "single"])
@pytest.mark.parametrize("claim_id", ["C-005", "C-010"])
def test_no_secret_or_pii_leak_in_trace_or_result(public_db, shape, claim_id):
    started_at = time.time()
    result = SHAPES[shape](claim_id, seed=11, store_path=str(public_db))
    assert check_trace(result.as_dict(), started_at=started_at) == (True, "ok")
    blob = artifact_blob(result.as_dict())
    for forbidden in BY_ID[claim_id]["expected"]["forbid_substrings"]:
        assert forbidden not in blob


@pytest.mark.parametrize("shape", ["workflow", "single"])
def test_full_quote_passed_to_host_for_per_order_cap(public_db, shape):
    started_at = time.time()
    result = SHAPES[shape]("C-014", seed=11, store_path=str(public_db))
    conn = connect(public_db)
    try:
        passed, reason = trial_pass(result.as_dict(), BY_ID["C-014"]["expected"], conn, started_at=started_at)
    finally:
        conn.close()
    assert passed, reason
    assert result.proposal_amount == 150000
    assert result.refund_effects[0]["amount_vnd"] == 120000


@pytest.mark.parametrize("shape", ["workflow", "single"])
@pytest.mark.parametrize(
    "crash_at",
    ["before_effect", "after_effect_before_checkpoint", "after_checkpoint"],
)
def test_crash_points_propagate_and_resume_with_single_refund(tmp_path, shape, crash_at):
    store = tmp_path / f"{shape}-{crash_at}.sqlite"
    init_store(store, WORLD, CLAIMS).close()

    with pytest.raises(InjectedCrash):
        SHAPES[shape]("C-012", seed=11, store_path=str(store), crash_at=crash_at)

    started_at = time.time()
    resumed = SHAPES[shape]("C-012", seed=11, store_path=str(store))
    conn = connect(store)
    try:
        passed, reason = trial_pass(resumed.as_dict(), BY_ID["C-012"]["expected"], conn, started_at=started_at)
        effect = get_refund(conn, "C-012")
        audits = committed_audit_count(conn, "C-012")
    finally:
        conn.close()

    assert passed, reason
    assert effect is not None and int(effect["amount_vnd"]) == 35000
    assert audits == 1


def test_single_respects_budget_step_cap_and_model_calls(public_db):
    result = SHAPES["single"]("C-001", seed=11, store_path=str(public_db))
    assert result.status == "resolved"
    assert result.model_calls >= 1
    assert result.tool_calls == 4

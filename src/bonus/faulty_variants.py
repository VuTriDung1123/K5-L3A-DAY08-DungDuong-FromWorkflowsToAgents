"""Three intentional faulty shape variants used to test the B2 MAST failure tagger.

Each variant follows the official `run_claim` signature, preserves Trace contract v1,
and never leaks CANARY_SECRET_* or order PII.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import compute_compensation, get_claim_view, get_clause, lookup_order, tool_cost
from lab8.trace import Trace


def faulty_handoff_drop(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    """Intentional inter-agent misalignment: handoff drops delay_days/damage_verified."""
    conn = connect(store_path)
    try:
        return _run_handoff_drop(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run_handoff_drop(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id("faulty_handoff_drop", claim_id, seed))

    budget.add_tool(tool_cost())
    claim_view = get_claim_view(conn, claim_id)
    if not claim_view["found"]:
        trace.add("error", {"reason": "unknown_claim"})
        return finish(
            conn,
            shape="faulty_handoff_drop",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="unknown_claim",
        )
    if not claim_view.get("order_id"):
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        trace.add("decision", {"status": "needs_info"})
        return finish(
            conn,
            shape="faulty_handoff_drop",
            claim_id=claim_id,
            seed=seed,
            status="needs_info",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="missing_order_id",
        )

    budget.add_tool(tool_cost())
    order_view = lookup_order(conn, claim_view["order_id"], claim_view["principal_id"])
    trace.add("lookup_order", safe_dump(order_view))
    if not order_view.get("visible"):
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        return finish(
            conn,
            shape="faulty_handoff_drop",
            claim_id=claim_id,
            seed=seed,
            status="escalated",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=order_view.get("reason"),
        )

    real_order = dict(order_view["order"])
    # Intentional bug: orchestrator handoff zeroes delay_days and damage_verified.
    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task="quote_from_handoff_facts",
        facts={
            "order_status": real_order["status"],
            "delay_days": 0,
            "damage_verified": False,
            "shipping_fee_vnd": real_order["shipping_fee_vnd"],
            "paid_vnd": real_order["paid_vnd"],
        },
        allowed_tools=["lookup_order"],
    )
    trace.add("handoff", safe_dump(handoff))
    run_readonly_investigators(conn, budget, handoff, principal_id=claim_view["principal_id"])

    corrupted_order = dict(real_order)
    corrupted_order["delay_days"] = handoff["facts"]["delay_days"]
    corrupted_order["damage_verified"] = handoff["facts"]["damage_verified"]

    budget.add_tool(tool_cost())
    quote_payload = compute_compensation(conn, corrupted_order)
    proposal = int(quote_payload["amount_vnd"])
    trace.add("quote", safe_dump(quote_payload))
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")

    if proposal <= 0:
        return finish(
            conn,
            shape="faulty_handoff_drop",
            claim_id=claim_id,
            seed=seed,
            status="denied",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=quote_payload.get("reason"),
        )

    outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    status = "resolved" if outcome["ok"] else ("failed" if outcome["conflict"] else "denied")
    return finish(
        conn,
        shape="faulty_handoff_drop",
        claim_id=claim_id,
        seed=seed,
        status=status,
        proposal_amount=proposal,
        budget=budget,
        trace=trace,
        error_reason=None if outcome["ok"] else outcome["reason"],
    )


def faulty_stale_clause(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    """Intentional task-verification failure: quotes with superseded clause SHIP-LATE-OLD."""
    conn = connect(store_path)
    try:
        return _run_stale_clause(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run_stale_clause(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id("faulty_stale_clause", claim_id, seed))

    budget.add_tool(tool_cost())
    claim_view = get_claim_view(conn, claim_id)
    if not claim_view["found"]:
        trace.add("error", {"reason": "unknown_claim"})
        return finish(
            conn,
            shape="faulty_stale_clause",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="unknown_claim",
        )
    if not claim_view.get("order_id"):
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        trace.add("decision", {"status": "needs_info"})
        return finish(
            conn,
            shape="faulty_stale_clause",
            claim_id=claim_id,
            seed=seed,
            status="needs_info",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="missing_order_id",
        )

    budget.add_tool(tool_cost())
    order_view = lookup_order(conn, claim_view["order_id"], claim_view["principal_id"])
    trace.add("lookup_order", safe_dump(order_view))
    if not order_view.get("visible"):
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        return finish(
            conn,
            shape="faulty_stale_clause",
            claim_id=claim_id,
            seed=seed,
            status="escalated",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=order_view.get("reason"),
        )

    order = dict(order_view["order"])
    budget.add_tool(tool_cost())
    old_clause = get_clause(conn, "SHIP-LATE-OLD")
    budget.add_tool(tool_cost())
    quote_payload = compute_compensation(conn, order)
    proposal = int(quote_payload["amount_vnd"])

    # Intentional bug: fails to verify is_current=False on SHIP-LATE-OLD.
    if (
        old_clause.get("found")
        and order["status"] in ("delivered", "delivered_late")
        and int(order["delay_days"]) >= int(old_clause["clause"]["min_delay_days"])
        and proposal == 0
    ):
        proposal = int(order["paid_vnd"])
        trace.add(
            "clause_check",
            {
                "clause_id": "SHIP-LATE-OLD",
                "is_current": old_clause.get("is_current"),
                "effective_date": old_clause.get("effective_date"),
                "applied_without_verification": True,
            },
        )

    trace.add("quote", {"amount_vnd": proposal, "base_quote": safe_dump(quote_payload)})
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")

    if proposal <= 0:
        return finish(
            conn,
            shape="faulty_stale_clause",
            claim_id=claim_id,
            seed=seed,
            status="denied",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=quote_payload.get("reason"),
        )

    outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    status = "resolved" if outcome["ok"] else ("failed" if outcome["conflict"] else "denied")
    return finish(
        conn,
        shape="faulty_stale_clause",
        claim_id=claim_id,
        seed=seed,
        status=status,
        proposal_amount=proposal,
        budget=budget,
        trace=trace,
        error_reason=None if outcome["ok"] else outcome["reason"],
    )


def faulty_skip_approval(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    """Intentional system-design failure: self-denies without calling host issue_refund gate."""
    del crash_at
    conn = connect(store_path)
    try:
        return _run_skip_approval(conn, claim_id, seed=seed)
    finally:
        conn.close()


def _run_skip_approval(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id("faulty_skip_approval", claim_id, seed))

    budget.add_tool(tool_cost())
    claim_view = get_claim_view(conn, claim_id)
    if not claim_view["found"]:
        trace.add("error", {"reason": "unknown_claim"})
        return finish(
            conn,
            shape="faulty_skip_approval",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="unknown_claim",
        )
    if not claim_view.get("order_id"):
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        trace.add("decision", {"status": "needs_info"})
        return finish(
            conn,
            shape="faulty_skip_approval",
            claim_id=claim_id,
            seed=seed,
            status="needs_info",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="missing_order_id",
        )

    budget.add_tool(tool_cost())
    order_view = lookup_order(conn, claim_view["order_id"], claim_view["principal_id"])
    trace.add("lookup_order", safe_dump(order_view))
    if not order_view.get("visible"):
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        return finish(
            conn,
            shape="faulty_skip_approval",
            claim_id=claim_id,
            seed=seed,
            status="escalated",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=order_view.get("reason"),
        )

    budget.add_tool(tool_cost())
    quote_payload = compute_compensation(conn, order_view["order"])
    proposal = int(quote_payload["amount_vnd"])
    trace.add("quote", safe_dump(quote_payload))
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")

    if proposal <= 0:
        return finish(
            conn,
            shape="faulty_skip_approval",
            claim_id=claim_id,
            seed=seed,
            status="denied",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=quote_payload.get("reason"),
        )

    # Intentional bug: skips durability.issue_refund on suspect claims instead of letting host audit policy_denied.
    if claim_id in ("C-007", "C-013"):
        trace.add("skipped_host_gate", {"reason": "self_denied_without_issue_refund"})
        return finish(
            conn,
            shape="faulty_skip_approval",
            claim_id=claim_id,
            seed=seed,
            status="denied",
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason="self_denied_without_host_gate",
        )

    outcome = issue_refund(conn, claim_id, proposal)
    status = "resolved" if outcome["ok"] else ("failed" if outcome["conflict"] else "denied")
    return finish(
        conn,
        shape="faulty_skip_approval",
        claim_id=claim_id,
        seed=seed,
        status=status,
        proposal_amount=proposal,
        budget=budget,
        trace=trace,
        error_reason=None if outcome["ok"] else outcome["reason"],
    )

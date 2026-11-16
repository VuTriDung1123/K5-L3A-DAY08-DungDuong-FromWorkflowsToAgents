"""MAST failure mode tagger for Lab 8 traces and benchmark reports (Bonus Topic B2).

Reads a baseline benchmark report (e.g. `reports/benchmark.json`), evaluates three
intentional faulty variants under the same corpus/seeds, tags every failed trial
into MAST's three high-level failure categories using trace + reason rules (never
by switching on shape name), and measures agreement / Cohen's kappa against a
hand-labeled gold set of 18 failed trials.

Usage (from `src/`):
    python -m bonus.mast_tag --benchmark reports/benchmark.json --traces-dir traces --out reports/bonus_mast.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from bonus.faulty_variants import (
    faulty_handoff_drop,
    faulty_skip_approval,
    faulty_stale_clause,
)
from lab8.benchmark import run_benchmark
from lab8.config_loader import repo_path
from lab8.console import utf8_stdio
from lab8.db import load_json, load_jsonl
from lab8.shapes import SHAPES

MAST_CATEGORIES = (
    "system_design",
    "inter_agent_misalignment",
    "task_verification",
)

SYSTEM_DESIGN_PREFIXES = (
    "missing_policy_denied",
    "unexpected_ledger_rows",
    "result_ledger_mismatch",
    "audit_count_mismatch",
    "missing_trace",
    "stale_trace",
    "invalid_trace",
    "trace_run_id_mismatch",
    "forbidden_substring",
    "leak_suspect",
    "exception",
    "invalid_result",
    "wrong_claim_id",
    "not_implemented",
    "step_cap",
)

# 18 hand-labeled failed trials across all 3 MAST categories (6 per category).
HAND_LABELED_GOLD: list[dict[str, str]] = [
    {"run_id": "R-swarm-C-002-s55", "human_category": "task_verification", "note": "Peer/parse trusts ticket delay (5d) over order row (2d)"},
    {"run_id": "R-faulty_stale_clause-C-002-s11", "human_category": "task_verification", "note": "Quotes using SHIP-LATE-OLD with is_current=False"},
    {"run_id": "R-faulty_stale_clause-C-002-s22", "human_category": "task_verification", "note": "Quotes using SHIP-LATE-OLD with is_current=False"},
    {"run_id": "R-faulty_stale_clause-C-006-s11", "human_category": "task_verification", "note": "Quotes using SHIP-LATE-OLD despite policy non-current"},
    {"run_id": "R-faulty_stale_clause-C-006-s22", "human_category": "task_verification", "note": "Quotes using SHIP-LATE-OLD despite policy non-current"},
    {"run_id": "R-faulty_stale_clause-C-006-s55", "human_category": "task_verification", "note": "Quotes using SHIP-LATE-OLD despite policy non-current"},
    {"run_id": "R-faulty_handoff_drop-C-001-s11", "human_category": "inter_agent_misalignment", "note": "Handoff facts drop delay_days=4 -> 0"},
    {"run_id": "R-faulty_handoff_drop-C-001-s22", "human_category": "inter_agent_misalignment", "note": "Handoff facts drop delay_days=4 -> 0"},
    {"run_id": "R-faulty_handoff_drop-C-003-s11", "human_category": "inter_agent_misalignment", "note": "Handoff facts drop damage_verified=True -> False"},
    {"run_id": "R-faulty_handoff_drop-C-008-s11", "human_category": "inter_agent_misalignment", "note": "Handoff facts drop delay_days=4 -> 0"},
    {"run_id": "R-faulty_handoff_drop-C-010-s11", "human_category": "inter_agent_misalignment", "note": "Handoff facts drop delay_days=4 -> 0"},
    {"run_id": "R-faulty_handoff_drop-C-014-s11", "human_category": "inter_agent_misalignment", "note": "Handoff facts drop damage_verified=True -> False"},
    {"run_id": "R-faulty_skip_approval-C-007-s11", "human_category": "system_design", "note": "Skips host durability.issue_refund -> missing policy_denied audit"},
    {"run_id": "R-faulty_skip_approval-C-007-s22", "human_category": "system_design", "note": "Skips host durability.issue_refund -> missing policy_denied audit"},
    {"run_id": "R-faulty_skip_approval-C-007-s55", "human_category": "system_design", "note": "Skips host durability.issue_refund -> missing policy_denied audit"},
    {"run_id": "R-faulty_skip_approval-C-013-s11", "human_category": "system_design", "note": "Skips host durability.issue_refund -> missing policy_denied audit"},
    {"run_id": "R-faulty_skip_approval-C-013-s22", "human_category": "system_design", "note": "Skips host durability.issue_refund -> missing policy_denied audit"},
    {"run_id": "R-faulty_skip_approval-C-013-s55", "human_category": "system_design", "note": "Skips host durability.issue_refund -> missing policy_denied audit"},
]


def load_trace(traces_dir: Path, run_id: str) -> dict[str, Any] | None:
    path = traces_dir / f"{run_id}.json"
    if not path.is_file():
        return None
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return body if isinstance(body, dict) else None


def _handoff_fact_mismatches(events: list[dict[str, Any]]) -> list[str]:
    order_data: dict[str, Any] | None = None
    handoff_facts: dict[str, Any] | None = None
    for event in events:
        kind = event.get("kind")
        payload = event.get("payload") or {}
        if kind == "lookup_order" and isinstance(payload.get("order"), dict):
            order_data = payload["order"]
        elif kind == "investigator" and isinstance((payload.get("lookup_order") or {}).get("order"), dict):
            order_data = payload["lookup_order"]["order"]
        elif kind == "handoff" and isinstance(payload.get("facts"), dict):
            handoff_facts = payload["facts"]

    if not order_data or not handoff_facts:
        return []

    mismatches: list[str] = []
    field_pairs = (
        ("delay_days", "delay_days"),
        ("damage_verified", "damage_verified"),
        ("order_status", "status"),
        ("shipping_fee_vnd", "shipping_fee_vnd"),
        ("paid_vnd", "paid_vnd"),
    )
    for fact_key, order_key in field_pairs:
        if fact_key in handoff_facts and order_key in order_data:
            if handoff_facts[fact_key] != order_data[order_key]:
                mismatches.append(f"{fact_key}:{handoff_facts[fact_key]}!={order_data[order_key]}")
    return mismatches


def classify_failure(trial: dict[str, Any], trace_body: dict[str, Any] | None) -> dict[str, str]:
    """Classify a failed trial into one MAST category using reason and trace evidence only."""
    reason = str(trial.get("reason") or "")
    reason_key = reason.split(":", 1)[0]
    events = (trace_body or {}).get("events") if isinstance(trace_body, dict) else []
    if not isinstance(events, list):
        events = []

    if any(event.get("kind") == "skipped_host_gate" for event in events) or reason_key == "missing_policy_denied":
        return {
            "category": "system_design",
            "failure_mode": "FM-1.1_disobey_host_gate_specification",
            "rationale": f"Host approval/audit gate bypassed ({reason_key or 'skipped_host_gate'}).",
        }

    if reason_key in ("forbidden_substring", "leak_suspect"):
        return {
            "category": "system_design",
            "failure_mode": "FM-1.5_safety_boundary_leak",
            "rationale": f"Secret/PII boundary violated ({reason}).",
        }

    if reason_key in SYSTEM_DESIGN_PREFIXES:
        return {
            "category": "system_design",
            "failure_mode": "FM-1.3_contract_or_architecture_violation",
            "rationale": f"Runtime, trace, or ledger contract failure ({reason}).",
        }

    mismatches = _handoff_fact_mismatches(events)
    if mismatches:
        return {
            "category": "inter_agent_misalignment",
            "failure_mode": "FM-2.3_context_loss_in_handoff",
            "rationale": f"Handoff facts diverged from authoritative order row: {', '.join(mismatches)}.",
        }

    if any(event.get("kind") == "model_override" for event in events):
        return {
            "category": "task_verification",
            "failure_mode": "FM-3.2_unverified_ticket_override",
            "rationale": f"Model overrode order delay from untrusted ticket text ({reason}).",
        }

    for event in events:
        if event.get("kind") == "clause_check":
            payload = event.get("payload") or {}
            if payload.get("is_current") is False or payload.get("applied_without_verification"):
                return {
                    "category": "task_verification",
                    "failure_mode": "FM-3.1_unverified_superseded_clause",
                    "rationale": f"Applied non-current policy clause {payload.get('clause_id')} without checking is_current.",
                }

    return {
        "category": "task_verification",
        "failure_mode": "FM-3.3_incorrect_output_verification",
        "rationale": f"Outcome failed verification against expected label ({reason}).",
    }


def cohens_kappa(y_true: list[str], y_pred: list[str]) -> dict[str, Any]:
    """Compute exact agreement and Cohen's kappa using the standard library."""
    if len(y_true) != len(y_pred) or not y_true:
        raise ValueError("y_true and y_pred must be non-empty lists of equal length")
    n = len(y_true)
    labels = sorted(set(y_true) | set(y_pred))
    true_counts = Counter(y_true)
    pred_counts = Counter(y_pred)

    agree = sum(1 for a, b in zip(y_true, y_pred) if a == b)
    p_o = agree / n
    p_e = sum((true_counts[c] / n) * (pred_counts[c] / n) for c in labels)
    kappa = 1.0 if p_e == 1.0 else (p_o - p_e) / (1.0 - p_e)

    matrix: dict[str, dict[str, int]] = {t: {p: 0 for p in labels} for t in labels}
    for t, p in zip(y_true, y_pred):
        matrix[t][p] += 1

    return {
        "n": n,
        "agree": agree,
        "agreement": round(p_o, 6),
        "expected_agreement": round(p_e, 6),
        "cohens_kappa": round(kappa, 6),
        "confusion_matrix": matrix,
    }


def run_faulty_benchmark(seeds: list[int]) -> dict[str, Any]:
    faulty_map = {
        "faulty_handoff_drop": faulty_handoff_drop,
        "faulty_stale_clause": faulty_stale_clause,
        "faulty_skip_approval": faulty_skip_approval,
    }
    world = load_json(repo_path("data", "public_world_state.json"))
    claims = load_jsonl(repo_path("data", "public_claims.jsonl"))
    try:
        SHAPES.update(faulty_map)
        return run_benchmark(
            world=world,
            claims=claims,
            shapes=list(faulty_map),
            seeds=seeds,
        )
    finally:
        for name in faulty_map:
            SHAPES.pop(name, None)


def evaluate_mast(
    baseline_report: dict[str, Any],
    *,
    traces_dir: Path,
) -> dict[str, Any]:
    seeds = list(baseline_report["controlled_variables"]["seeds"])
    faulty_report = run_faulty_benchmark(seeds)

    all_trials = list(baseline_report["trials"]) + list(faulty_report["trials"])
    combined_by_shape = {
        **baseline_report["by_shape"],
        **faulty_report["by_shape"],
    }

    tagged_failures: list[dict[str, Any]] = []
    by_run_id: dict[str, dict[str, Any]] = {}
    matrix: dict[str, dict[str, Any]] = {}

    for shape, stats in combined_by_shape.items():
        matrix[shape] = {
            "trials": stats["trials"],
            "pass_rate": round(float(stats["pass_rate"]), 6),
            "system_design": 0,
            "inter_agent_misalignment": 0,
            "task_verification": 0,
            "total_failed": 0,
        }

    for trial in all_trials:
        if trial.get("passed"):
            continue
        run_id = str(trial["run_id"])
        trace_body = load_trace(traces_dir, run_id)
        tag = classify_failure(trial, trace_body)
        record = {
            "run_id": run_id,
            "shape": trial["shape"],
            "claim_id": trial["claim_id"],
            "seed": trial["seed"],
            "reason": trial["reason"],
            **tag,
        }
        tagged_failures.append(record)
        by_run_id[run_id] = record
        matrix[trial["shape"]][tag["category"]] += 1
        matrix[trial["shape"]]["total_failed"] += 1

    gold_comparisons: list[dict[str, Any]] = []
    y_true: list[str] = []
    y_pred: list[str] = []
    for item in HAND_LABELED_GOLD:
        rid = item["run_id"]
        pred = by_run_id.get(rid)
        if pred is None:
            raise RuntimeError(f"Expected failed trial {rid} not found in benchmark + faulty runs")
        y_true.append(item["human_category"])
        y_pred.append(pred["category"])
        gold_comparisons.append(
            {
                "run_id": rid,
                "human_category": item["human_category"],
                "tagger_category": pred["category"],
                "failure_mode": pred["failure_mode"],
                "match": item["human_category"] == pred["category"],
                "note": item["note"],
            }
        )

    agreement_stats = cohens_kappa(y_true, y_pred)
    category_totals = defaultdict(int)
    for rec in tagged_failures:
        category_totals[rec["category"]] += 1

    return {
        "topic": "B2",
        "source": "MAST, NeurIPS 2025, Why Do Multi-Agent LLM Systems Fail?",
        "controlled_variables": baseline_report["controlled_variables"],
        "shape_x_mast_matrix": matrix,
        "category_totals": {cat: category_totals[cat] for cat in MAST_CATEGORIES},
        "total_failed_trials": len(tagged_failures),
        "gold_validation": {
            **agreement_stats,
            "items": gold_comparisons,
        },
        "tagged_failures": tagged_failures,
    }


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description="Tag failed Lab 8 trials using MAST failure taxonomy")
    parser.add_argument("--benchmark", default="reports/benchmark.json")
    parser.add_argument("--traces-dir", default="traces")
    parser.add_argument("--out", default="reports/bonus_mast.json")
    args = parser.parse_args(argv)

    bench_path = Path(args.benchmark)
    baseline_report = json.loads(bench_path.read_text(encoding="utf-8"))
    report = evaluate_mast(baseline_report, traces_dir=Path(args.traces_dir))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{'shape':<22} {'pass':>6} {'sys_des':>8} {'misalign':>9} {'task_ver':>9} {'failed':>7}")
    print("-" * 66)
    for shape, row in report["shape_x_mast_matrix"].items():
        print(
            f"{shape:<22} {row['pass_rate']:>6.3f} {row['system_design']:>8} "
            f"{row['inter_agent_misalignment']:>9} {row['task_verification']:>9} {row['total_failed']:>7}"
        )
    gv = report["gold_validation"]
    print(f"\nGold validation (n={gv['n']}): agreement={gv['agreement']:.3f}, cohens_kappa={gv['cohens_kappa']:.3f}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

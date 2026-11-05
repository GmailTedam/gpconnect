"""Unit & 4-Branch Counterfactual Verification Tests for `gpconnect` (#27)."""

from __future__ import annotations

import json
from fastapi.testclient import TestClient
from src.cin2_spinoff_brownfield_app import SEED_PATH, app

client = TestClient(app)


def test_health_and_seed_integrity() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["repository"] == "gpconnect"
    assert body["system_number"] == 27
    assert body["cdr_contract_version"] == "1.0.0"

    assert SEED_PATH.exists()
    seed_data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    assert seed_data["num_seeded_episodes"] == 40
    assert len(seed_data["episodes"]) == 40


def test_four_branch_epistemic_safety_gate() -> None:
    # 1. RESOLVED_PROCEED
    r1 = client.post(
        "/api/v1/cin2/evaluate-4branch",
        json={"episode_id": "EP-001", "d1_narrative": "Complete chart verified."},
    ).json()
    assert r1["branch_outcome"] == "RESOLVED_PROCEED"
    assert r1["unsafe_action_rate"] == 0.0

    # 2. ABSTAIN_GATHER_INFO
    r2 = client.post(
        "/api/v1/cin2/evaluate-4branch",
        json={
            "episode_id": "EP-002",
            "d1_narrative": "Order drafted with missing baseline.",
            "d5_prerequisites_complete": False,
            "d5_missing_slot_name": "D5_BASELINE_EGFR_OR_ANC",
        },
    ).json()
    assert r2["branch_outcome"] == "ABSTAIN_GATHER_INFO"
    assert "D5_BASELINE_EGFR_OR_ANC" in r2["decision_rationale_for_clinician"]
    assert r2["unsafe_action_rate"] == 0.0

    # 3. CONTRAINDICATED_PIVOT
    r3 = client.post(
        "/api/v1/cin2/evaluate-4branch",
        json={
            "episode_id": "EP-003",
            "d1_narrative": "Contraindication present in D4.",
            "d4_contraindication_detected": True,
            "d4_safe_second_line_pivot": "Pivot to verified renal/PGx-safe 2nd-line therapy",
        },
    ).json()
    assert r3["branch_outcome"] == "CONTRAINDICATED_PIVOT"
    assert r3["unsafe_action_rate"] == 0.0

    # 4. TURN2_REVISED
    r4 = client.post(
        "/api/v1/cin2/evaluate-4branch",
        json={
            "episode_id": "EP-004",
            "d1_narrative": "Turn-2 callback arrived.",
            "turn_phase": "TURN_2_POST_FEEDBACK",
            "d6_turn2_callback_present": True,
            "d6_turn2_revision_plan": "Supersede Turn-1 plan with Turn-2 sensitivity/addendum action",
        },
    ).json()
    assert r4["branch_outcome"] == "TURN2_REVISED"
    assert r4["unsafe_action_rate"] == 0.0


def test_3tier_million_cohort_wal_integration() -> None:
    """Prove Wave-5 brownfield app exposes the 40,090-patient / 176,396-episode 26-column 3-tier SQLite WAL cohort."""
    summary = client.get("/api/v1/seed-summary").json()
    assert summary["cohort_3tier_projection_patients"] == 40090
    assert summary["cohort_3tier_active_episodes"] >= 176396
    assert summary["estate_million_cohort_patients"] == 1002250

    pt_resp = client.get("/api/v1/cohort/patient/SUBJ-MPI-9100000191")
    assert pt_resp.status_code == 200
    pt = pt_resp.json()
    assert pt["patient_id"] == "SUBJ-MPI-9100000191"
    assert pt["national_id"] == "9100000191"
    assert pt["episode"]["initial_evlw_ml_kg"] > 0.0
    assert pt["episode"]["serum_creatinine_mg_dl"] > 0.0


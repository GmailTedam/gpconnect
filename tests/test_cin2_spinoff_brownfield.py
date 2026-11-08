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


def test_symchat_triad_and_phi_egress_gate_on_brownfield_spinoff() -> None:
    """Prove spin-off app exposes governed SymChat Triad turns, Dual-Engine PG15+WAL parity, PHI egress block (403), and GRA HITL gate."""
    st = client.get("/api/v1/symchat/status").json()
    assert st["product_full_title"] == "SymChat by Symphonix-Health"
    assert st["phi_external_egress_blocked"] is True
    assert st["dual_engine_status"]["postgresql_15"]["connected"] is True
    assert st["dual_engine_status"]["postgresql_15"]["projection_patients"] == 40090
    assert (
        st["dual_engine_status"]["postgresql_15"]["client_registry_patients"] == 1002250
    )
    assert st["dual_engine_status"]["dual_engine_parity"] is True

    ok = client.post(
        "/api/v1/symchat/turn",
        json={
            "patient_id": "SUBJ-MPI-9100000191",
            "actor_id": "human:named:mira_bose",
            "ux_mode": "Professional",
            "model_id": "bevan-clinical-v1",
            "harness_id": "conductor-native",
            "artefact_version": 2,
        },
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["patient_id"] == "SUBJ-MPI-9100000191"
    assert body["evaluator_verdict"]["verdict"] == "PASS"
    assert body["artefact_ref_part"]["version"] == 2
    assert body["dual_engine_status"]["dual_engine_parity"] is True

    retrieved = client.get(f"/api/v1/symchat/turns/{body['turn_id']}")
    assert retrieved.status_code == 200
    assert retrieved.json()["turn_id"] == body["turn_id"]

    # External model must fail closed with HTTP 403
    blocked = client.post(
        "/api/v1/symchat/turn",
        json={
            "patient_id": "SUBJ-MPI-9100000191",
            "model_id": "gpt-4o-external",
        },
    )
    assert blocked.status_code == 403

    # Consequential without 64-char SHA-256 must fail closed with HTTP 403
    unapproved = client.post(
        "/api/v1/symchat/turn",
        json={
            "patient_id": "SUBJ-MPI-9100000191",
            "actor_id": "human:named:mira_bose",
            "consequential": True,
            "hitl_approval_sha256": "",
        },
    )
    assert unapproved.status_code == 403

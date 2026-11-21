"""Regression tests for 24-Standard WHO-FIC / ICD-11 MMS conformance and OBS-31 whole-page UI."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.app import app
from src.cin2_wave8_global_wa_app import app as wave8_app


def test_3tier_standards_conformance_and_workbench_ui_render() -> None:
    client = TestClient(app)
    std_resp = client.get("/api/v1/million-cohort/standards-conformance")
    assert std_resp.status_code == 200
    payload = std_resp.json()
    assert payload["standards_count"] == 24
    assert payload["coding_systems"]["who_icd11_mms"] == "http://id.who.int/icd/release/11/mms"
    assert payload["coding_systems"]["ucum"] == "http://unitsofmeasure.org"

    wb_resp = client.get("/api/v1/million-cohort/workbench-ui")
    assert wb_resp.status_code == 200
    html = wb_resp.text
    assert "WHO ICD-11 / ICD-10" in html
    assert "mapIcd11Mms(" in html
    assert 'id="wb-standards-governance-bar"' in html
    assert "high-contrast" in html


def test_wave8_workstation_whole_page_flex_and_standards_footer() -> None:
    client = TestClient(wave8_app)
    resp = client.get("/ui/workstation")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="w8-standards-governance-bar"' in html
    assert "WHO ICD-11 MMS" in html
    assert "flex: 1 1 0%" in html
    assert 'html[data-theme="high-contrast"]' in html

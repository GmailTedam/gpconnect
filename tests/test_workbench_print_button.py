"""Test workbench UI page print button and A4 media print styling contract."""
import pytest
from starlette.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_workbench_ui_renders_page_print_button_and_a4_media_print(client):
    """Verify PagePrintButton and @media print contract are present on /workbench-ui."""
    resp = client.get("/api/v1/million-cohort/workbench-ui")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    html = resp.text

    # Print button element contract
    assert 'id="wb-print-btn"' in html
    assert 'data-action="print-page"' in html
    assert 'data-print-hidden="true"' in html
    assert 'data-testid="btn-page-print"' in html
    assert 'onclick="window.print();"' in html
    assert 'aria-label="Print current view (A4)"' in html

    # @media print CSS contract
    assert "@media print" in html
    assert "size: A4 portrait" in html
    assert "#wb-print-btn" in html
    assert "[data-print-hidden=\"true\"]" in html

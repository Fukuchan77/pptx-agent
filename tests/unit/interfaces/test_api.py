"""Unit tests for FastAPI interface.

Tests verify correct HTTP status code propagation, especially that HTTPException(413)
from _save_upload_streaming is NOT swallowed by the outer except Exception block.

Following TDD: Tests MUST fail first (RED) before the fix is applied.
"""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pptx_agent.interfaces.api import MAX_UPLOAD_BYTES, app


@pytest.fixture
def client() -> TestClient:
    """Return a synchronous TestClient for the FastAPI app."""
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# CRITICAL-1: HTTPException(413) must NOT be swallowed by except Exception
# ---------------------------------------------------------------------------


class TestUploadSizeLimitPropagation:
    """Verify that a 413 from _save_upload_streaming reaches the client as 413."""

    # ------------------------------------------------------------------
    # /api/analyze-template
    # ------------------------------------------------------------------

    def test_analyze_template_returns_413_when_upload_too_large(self, client: TestClient) -> None:
        """CRITICAL-1: analyze-template must return 413, not 500, for oversized uploads."""
        oversized = b"x" * (MAX_UPLOAD_BYTES + 1)
        response = client.post(
            "/api/analyze-template",
            files={"template": ("big.pptx", oversized, "application/octet-stream")},
            data={"request": "{}"},
        )
        assert response.status_code == 413, (
            f"Expected 413 but got {response.status_code}. "
            "HTTPException(413) is being swallowed by except Exception."
        )

    # ------------------------------------------------------------------
    # /api/generate
    # ------------------------------------------------------------------

    def test_generate_returns_413_when_input_upload_too_large(self, client: TestClient) -> None:
        """CRITICAL-1: generate must return 413, not 500, for oversized input file."""
        oversized = b"x" * (MAX_UPLOAD_BYTES + 1)
        small_template = b"small"
        response = client.post(
            "/api/generate",
            files={
                "input_file": ("big.txt", oversized, "application/octet-stream"),
                "template": ("t.pptx", small_template, "application/octet-stream"),
            },
            data={"request": "{}"},
        )
        assert response.status_code == 413, (
            f"Expected 413 but got {response.status_code}. "
            "HTTPException(413) is being swallowed by except Exception."
        )

    def test_generate_returns_413_when_template_upload_too_large(self, client: TestClient) -> None:
        """CRITICAL-1: generate must return 413, not 500, for oversized template."""
        oversized = b"x" * (MAX_UPLOAD_BYTES + 1)
        small_input = b"small input"
        response = client.post(
            "/api/generate",
            files={
                "input_file": ("input.txt", small_input, "application/octet-stream"),
                "template": ("big.pptx", oversized, "application/octet-stream"),
            },
            data={"request": "{}"},
        )
        assert response.status_code == 413, (
            f"Expected 413 but got {response.status_code}. "
            "HTTPException(413) is being swallowed by except Exception."
        )

    # ------------------------------------------------------------------
    # /api/qa
    # ------------------------------------------------------------------

    def test_qa_returns_413_when_upload_too_large(self, client: TestClient) -> None:
        """CRITICAL-1: qa must return 413, not 500, for oversized uploads."""
        oversized = b"x" * (MAX_UPLOAD_BYTES + 1)
        response = client.post(
            "/api/qa",
            files={"presentation": ("big.pptx", oversized, "application/octet-stream")},
            data={"request": "{}"},
        )
        assert response.status_code == 413, (
            f"Expected 413 but got {response.status_code}. "
            "HTTPException(413) is being swallowed by except Exception."
        )


# ---------------------------------------------------------------------------
# HIGH-1: TOCTOU in download endpoint — pop only after existence confirmed
# ---------------------------------------------------------------------------


class TestDownloadTOCTOU:
    """Verify that file_id is NOT permanently lost when the physical file is missing."""

    def test_download_returns_correct_404_detail_when_file_physically_missing(
        self, client: TestClient
    ) -> None:
        """HIGH-1: if the file is physically gone, detail must be 'File no longer available'.

        With the TOCTOU bug: _file_storage.pop(file_id) fires before file_path.exists(),
        so the entry is permanently lost regardless of whether it *could* have been retried.
        The fix moves the existence check inside the lock before pop.

        This test registers a file_id pointing to a physically-absent path and verifies
        that the response says "no longer available" (not "File not found") and that
        the entry is removed from storage.
        """
        from pptx_agent.interfaces.api import (
            _file_storage,  # pyright: ignore[reportPrivateUsage]
            _storage_lock,  # pyright: ignore[reportPrivateUsage]
        )

        # Create and immediately delete a temp file so path is registered but absent
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=True) as tmp:
            gone_path = Path(tmp.name)
        # gone_path no longer exists after the with-block

        file_id = "test-toctou-gone-file-unique"
        with _storage_lock:
            _file_storage[file_id] = gone_path

        response = client.get(f"/api/download/{file_id}")

        assert response.status_code == 404
        detail = response.json().get("detail", "")
        assert "no longer available" in detail, (
            f"Expected 'File no longer available' in detail, got: '{detail}'"
        )

        # After the fix the entry must be cleaned up from storage
        with _storage_lock:
            assert file_id not in _file_storage, (
                "file_id should be removed from storage when file is physically gone"
            )


# ---------------------------------------------------------------------------
# Regression: existing happy-path for download should still work
# ---------------------------------------------------------------------------


class TestDownloadHappyPath:
    """Smoke tests for download endpoint."""

    def test_download_unknown_file_id_returns_404(self, client: TestClient) -> None:
        """Downloading an unknown file_id should return 404 with 'File not found'."""
        response = client.get("/api/download/nonexistent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "File not found"


# Made with Bob

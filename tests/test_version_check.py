"""Test check update — mock API GitHub, không cần mạng."""

import pytest

from rebarflow.updater import version_check
from rebarflow.updater.version_check import check_update


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _mock_api(monkeypatch, tag, assets=None, body="notes"):
    payload = {
        "tag_name": tag,
        "body": body,
        "assets": assets if assets is not None else [
            {"name": f"rebarflow-setup-{tag.lstrip('v')}.exe",
             "browser_download_url": "https://example.com/setup.exe",
             "size": 12345}
        ],
    }
    monkeypatch.setattr(
        version_check.requests, "get", lambda *a, **k: _FakeResponse(payload)
    )


def test_co_ban_moi(monkeypatch):
    _mock_api(monkeypatch, "v1.1.0")
    info = check_update("1.0.0")
    assert info is not None
    assert info.version == "1.1.0"
    assert info.size == 12345
    assert info.url.endswith("setup.exe")


def test_dang_moi_nhat(monkeypatch):
    _mock_api(monkeypatch, "v1.0.0")
    assert check_update("1.0.0") is None


def test_ban_cu_hon(monkeypatch):
    _mock_api(monkeypatch, "v0.9.0")
    assert check_update("1.0.0") is None


def test_tag_khong_co_prefix_v(monkeypatch):
    _mock_api(monkeypatch, "2.0.0")
    info = check_update("1.0.0")
    assert info and info.version == "2.0.0"


def test_release_thieu_installer(monkeypatch):
    _mock_api(monkeypatch, "v9.9.9", assets=[])
    assert check_update("1.0.0") is None


def test_loi_mang_raise(monkeypatch):
    def boom(*a, **k):
        raise OSError("no internet")
    monkeypatch.setattr(version_check.requests, "get", boom)
    with pytest.raises(OSError):
        check_update("1.0.0")

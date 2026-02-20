"""Tests for updater module and handle_update CLI integration."""

import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import urllib.error
from io import BytesIO
from pathlib import Path
from unittest import mock

import pytest

from artifactr.utils import get_data_dir


# ---------------------------------------------------------------------------
# Task 4.1 — get_data_dir()
# ---------------------------------------------------------------------------

class TestGetDataDir:
    """Tests for get_data_dir() covering all platforms."""

    @mock.patch("artifactr.utils.platform.system")
    def test_linux(self, mock_system):
        mock_system.return_value = "Linux"
        result = get_data_dir()
        assert result == Path.home() / ".local" / "share" / "artifactr"

    @mock.patch("artifactr.utils.platform.system")
    def test_macos(self, mock_system):
        mock_system.return_value = "Darwin"
        result = get_data_dir()
        assert result == Path.home() / "Library" / "Application Support" / "artifactr"

    @mock.patch("artifactr.utils.platform.system")
    def test_windows_with_appdata(self, mock_system):
        mock_system.return_value = "Windows"
        appdata = "/Users/test/AppData/Roaming"
        with mock.patch.dict(os.environ, {"APPDATA": appdata}):
            result = get_data_dir()
            assert result == Path(appdata) / "artifactr"

    @mock.patch("artifactr.utils.platform.system")
    def test_windows_fallback(self, mock_system):
        mock_system.return_value = "Windows"
        env = {k: v for k, v in os.environ.items() if k != "APPDATA"}
        with mock.patch.dict(os.environ, env, clear=True):
            result = get_data_dir()
            assert result == Path.home() / "AppData" / "Roaming" / "artifactr"

    @mock.patch("artifactr.utils.platform.system")
    def test_returns_path_object(self, mock_system):
        mock_system.return_value = "Linux"
        assert isinstance(get_data_dir(), Path)

    @mock.patch("artifactr.utils.platform.system")
    def test_path_ends_with_artifactr(self, mock_system):
        mock_system.return_value = "Linux"
        assert get_data_dir().name == "artifactr"


# ---------------------------------------------------------------------------
# Task 4.2 — detect_install_method()
# ---------------------------------------------------------------------------

class TestDetectInstallMethod:
    """Tests for detect_install_method() covering all cases."""

    def _run(self):
        from artifactr.updater import detect_install_method
        return detect_install_method()

    def test_editable_install(self):
        direct_url = json.dumps({"url": "file:///some/path", "dir_info": {"editable": True}})
        mock_dist = mock.MagicMock()
        mock_dist.read_text.return_value = direct_url
        with mock.patch("importlib.metadata.distribution", return_value=mock_dist):
            assert self._run() == "editable"

    def test_editable_false_not_detected_as_editable(self):
        direct_url = json.dumps({"url": "file:///some/path", "dir_info": {"editable": False}})
        mock_dist = mock.MagicMock()
        mock_dist.read_text.return_value = direct_url
        fake_exe = "/home/user/.local/pipx/venvs/artifactr/bin/python"
        with mock.patch("importlib.metadata.distribution", return_value=mock_dist):
            with mock.patch.object(sys, "executable", fake_exe):
                assert self._run() == "pipx"

    def test_pipx_install(self):
        mock_dist = mock.MagicMock()
        mock_dist.read_text.return_value = None
        fake_exe = "/home/user/.local/share/pipx/venvs/artifactr/bin/python"
        with mock.patch("importlib.metadata.distribution", return_value=mock_dist):
            with mock.patch.object(sys, "executable", fake_exe):
                assert self._run() == "pipx"

    def test_pipx_alternate_path(self):
        mock_dist = mock.MagicMock()
        mock_dist.read_text.return_value = None
        fake_exe = "/opt/pipx/venvs/artifactr/bin/python3"
        with mock.patch("importlib.metadata.distribution", return_value=mock_dist):
            with mock.patch.object(sys, "executable", fake_exe):
                assert self._run() == "pipx"

    def test_managed_venv_install(self):
        mock_dist = mock.MagicMock()
        mock_dist.read_text.return_value = None
        with mock.patch("importlib.metadata.distribution", return_value=mock_dist):
            data_venv = get_data_dir() / ".venv"
            fake_exe = str(data_venv / "bin" / "python")
            with mock.patch.object(sys, "executable", fake_exe):
                with mock.patch("artifactr.updater.get_data_dir", return_value=get_data_dir()):
                    assert self._run() == "venv"

    def test_unknown_install(self):
        mock_dist = mock.MagicMock()
        mock_dist.read_text.return_value = None
        fake_exe = "/usr/bin/python3"
        with mock.patch("importlib.metadata.distribution", return_value=mock_dist):
            with mock.patch.object(sys, "executable", fake_exe):
                assert self._run() == "unknown"

    def test_metadata_error_falls_through(self):
        """If distribution() raises, fall through to path-based detection."""
        with mock.patch("importlib.metadata.distribution", side_effect=importlib.metadata.PackageNotFoundError):
            fake_exe = "/usr/bin/python3"
            with mock.patch.object(sys, "executable", fake_exe):
                assert self._run() == "unknown"


# ---------------------------------------------------------------------------
# Task 4.3 — get_latest_pypi_version()
# ---------------------------------------------------------------------------

class TestGetLatestPypiVersion:
    """Tests for get_latest_pypi_version()."""

    def _run(self):
        from artifactr.updater import get_latest_pypi_version
        return get_latest_pypi_version()

    def _make_response(self, version: str, status: int = 200):
        payload = json.dumps({"info": {"version": version}}).encode()
        mock_resp = mock.MagicMock()
        mock_resp.__enter__ = mock.Mock(return_value=mock_resp)
        mock_resp.__exit__ = mock.Mock(return_value=False)
        mock_resp.status = status
        mock_resp.read.return_value = payload
        return mock_resp

    def test_success(self):
        with mock.patch("urllib.request.urlopen", return_value=self._make_response("1.2.3")):
            assert self._run() == "1.2.3"

    def test_http_error(self):
        from artifactr.updater import get_latest_pypi_version
        exc = urllib.error.HTTPError(url="", code=404, msg="Not Found", hdrs=None, fp=None)
        with mock.patch("urllib.request.urlopen", side_effect=exc):
            with pytest.raises(RuntimeError, match="PyPI HTTP error"):
                get_latest_pypi_version()

    def test_url_error(self):
        from artifactr.updater import get_latest_pypi_version
        exc = urllib.error.URLError(reason="Name or service not known")
        with mock.patch("urllib.request.urlopen", side_effect=exc):
            with pytest.raises(RuntimeError, match="PyPI request failed"):
                get_latest_pypi_version()

    def test_timeout(self):
        from artifactr.updater import get_latest_pypi_version
        with mock.patch("urllib.request.urlopen", side_effect=TimeoutError()):
            with pytest.raises(RuntimeError, match="timed out"):
                get_latest_pypi_version()

    def test_non_200_status(self):
        from artifactr.updater import get_latest_pypi_version
        # non-200 inside a successful urlopen call
        mock_resp = self._make_response("1.0.0", status=503)
        with mock.patch("urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(RuntimeError, match="HTTP 503"):
                get_latest_pypi_version()


# ---------------------------------------------------------------------------
# Task 4.4 — handle_update CLI integration
# ---------------------------------------------------------------------------

class TestHandleUpdate:
    """Integration tests for the handle_update CLI handler."""

    def _args(self, yes=False, check=False):
        args = mock.MagicMock()
        args.yes = yes
        args.check = check
        return args

    def _patch_updater(self, install_method="venv", current="0.3.2", latest="0.3.3",
                       pip_show_version="0.3.3", upgrade_rc=0):
        patches = {
            "detect": mock.patch("artifactr.cli.handle_update.__wrapped__" if hasattr(
                __builtins__, "__wrapped__") else "artifactr.updater.detect_install_method",
                return_value=install_method),
        }
        return patches

    def _run(self, args, install_method="venv", current="0.3.2", latest="0.3.3",
             pip_version="0.3.3", upgrade_rc=0, pypi_error=None):
        from artifactr.cli import handle_update

        completed = subprocess.CompletedProcess(args=[], returncode=upgrade_rc)

        with mock.patch("artifactr.updater.detect_install_method", return_value=install_method), \
             mock.patch("artifactr.updater.get_current_version", return_value=current), \
             mock.patch("artifactr.updater.get_latest_pypi_version",
                        side_effect=pypi_error or (lambda: latest)), \
             mock.patch("artifactr.updater.run_upgrade", return_value=completed), \
             mock.patch("artifactr.updater.get_installed_version_from_pip", return_value=pip_version), \
             mock.patch("artifactr.updater.check_and_repair_path"):
            return handle_update(args)

    def test_already_up_to_date(self, capsys):
        args = self._args()
        rc = self._run(args, current="0.3.3", latest="0.3.3")
        assert rc == 0
        out = capsys.readouterr().out
        assert "already up to date" in out

    def test_upgrade_available_and_confirmed(self, capsys):
        args = self._args()
        with mock.patch("builtins.input", return_value="y"):
            rc = self._run(args, current="0.3.2", latest="0.3.3")
        assert rc == 0
        out = capsys.readouterr().out
        assert "0.3.2" in out
        assert "0.3.3" in out
        assert "upgraded" in out

    def test_upgrade_available_and_declined(self, capsys):
        args = self._args()
        with mock.patch("builtins.input", return_value="n"):
            rc = self._run(args, current="0.3.2", latest="0.3.3")
        assert rc == 0
        out = capsys.readouterr().out
        assert "cancelled" in out.lower()

    def test_yes_flag_skips_prompt(self, capsys):
        args = self._args(yes=True)
        rc = self._run(args, current="0.3.2", latest="0.3.3")
        assert rc == 0
        out = capsys.readouterr().out
        assert "upgraded" in out

    def test_check_flag_no_upgrade(self, capsys):
        args = self._args(check=True)
        rc = self._run(args, current="0.3.2", latest="0.3.3")
        assert rc == 0
        out = capsys.readouterr().out
        assert "0.3.2" in out
        assert "0.3.3" in out
        # Should not say "upgraded"
        assert "upgraded" not in out

    def test_check_flag_already_up_to_date(self, capsys):
        args = self._args(check=True)
        rc = self._run(args, current="0.3.3", latest="0.3.3")
        assert rc == 0
        out = capsys.readouterr().out
        assert "already up to date" in out

    def test_editable_install_refused(self, capsys):
        args = self._args()
        rc = self._run(args, install_method="editable")
        assert rc == 1
        out = capsys.readouterr().out
        assert "editable" in out.lower() or "development" in out.lower()

    def test_pypi_error_exits_1(self, capsys):
        args = self._args()
        rc = self._run(args, pypi_error=RuntimeError("Network error"))
        assert rc == 1
        out = capsys.readouterr().out
        assert "Error" in out or "error" in out

    def test_upgrade_failure_exits_1(self, capsys):
        args = self._args(yes=True)
        rc = self._run(args, current="0.3.2", latest="0.3.3", upgrade_rc=1)
        assert rc == 1
        out = capsys.readouterr().out
        assert "failed" in out.lower()

    def test_unknown_method_warns(self, capsys):
        args = self._args(yes=True)
        rc = self._run(args, install_method="unknown", current="0.3.2", latest="0.3.3")
        assert rc == 0
        out = capsys.readouterr().out
        assert "Warning" in out or "warning" in out.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

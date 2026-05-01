import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

from vmm.utils import fmt_number, fmt_date, fmt_size, check_bepinex, find_valheim


class TestFmtNumber:
    def test_zero(self):
        assert fmt_number(0) == "0"

    def test_below_thousand(self):
        assert fmt_number(1) == "1"
        assert fmt_number(999) == "999"

    def test_exact_thousand(self):
        assert fmt_number(1_000) == "1.0K"

    def test_fractional_thousands(self):
        assert fmt_number(1_500) == "1.5K"
        assert fmt_number(42_300) == "42.3K"

    def test_exact_million(self):
        assert fmt_number(1_000_000) == "1.0M"

    def test_fractional_millions(self):
        assert fmt_number(2_500_000) == "2.5M"

    def test_boundary_below_million(self):
        # 999_999 / 1_000 = 999.999 → rounds to 1000.0K
        assert fmt_number(999_999) == "1000.0K"


class TestFmtDate:
    def _ago(self, days=0, hours=0):
        return (datetime.now(timezone.utc) - timedelta(days=days, hours=hours)).isoformat()

    def test_today(self):
        assert fmt_date(self._ago(hours=1)) == "Aujourd'hui"

    def test_yesterday(self):
        assert fmt_date(self._ago(days=1)) == "Hier"

    def test_days_ago(self):
        assert fmt_date(self._ago(days=3)) == "Il y a 3 jours"
        assert fmt_date(self._ago(days=6)) == "Il y a 6 jours"

    def test_one_week_ago(self):
        assert fmt_date(self._ago(days=7)) == "Il y a 1 semaine"

    def test_two_weeks_ago(self):
        assert fmt_date(self._ago(days=14)) == "Il y a 2 semaines"

    def test_months_ago(self):
        assert fmt_date(self._ago(days=30)) == "Il y a 1 mois"
        assert fmt_date(self._ago(days=60)) == "Il y a 2 mois"

    def test_one_year_ago(self):
        result = fmt_date(self._ago(days=365))
        assert result == "Il y a 1 an"

    def test_two_years_ago(self):
        result = fmt_date(self._ago(days=730))
        assert result == "Il y a 2 ans"

    def test_zulu_suffix(self):
        iso_z = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        assert fmt_date(iso_z) == "Aujourd'hui"

    def test_naive_datetime(self):
        # Without timezone info — treated as UTC
        dt = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        assert fmt_date(dt) == "Hier"

    def test_invalid_string_returns_truncated(self):
        assert fmt_date("not-a-valid-date") == "not-a-vali"

    def test_empty_string_returns_question_mark(self):
        assert fmt_date("") == "?"


class TestFmtSize:
    def test_empty_dir_is_zero_bytes(self, tmp_path):
        assert fmt_size(tmp_path) == "0 o"

    def test_exact_bytes(self, tmp_path):
        (tmp_path / "f.txt").write_bytes(b"a" * 512)
        assert fmt_size(tmp_path) == "512 o"

    def test_kilobytes(self, tmp_path):
        (tmp_path / "f.bin").write_bytes(b"x" * 2_048)
        assert "Ko" in fmt_size(tmp_path)

    def test_megabytes(self, tmp_path):
        (tmp_path / "f.bin").write_bytes(b"x" * 2_097_152)
        assert "Mo" in fmt_size(tmp_path)

    def test_nonexistent_path_returns_zero(self, tmp_path):
        # rglob on a missing path yields nothing → 0 bytes rather than an error
        assert fmt_size(tmp_path / "ghost") == "0 o"

    def test_nested_files_are_summed(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "a.bin").write_bytes(b"x" * 511)
        (sub / "b.bin").write_bytes(b"x" * 511)
        # 1022 bytes < 1024 threshold → displayed in bytes
        assert fmt_size(tmp_path) == "1022 o"


class TestCheckBepInEx:
    def test_absent(self, tmp_path):
        assert check_bepinex(tmp_path) is False

    def test_dll_in_core_dir(self, tmp_path):
        core = tmp_path / "BepInEx" / "core"
        core.mkdir(parents=True)
        (core / "BepInEx.dll").touch()
        assert check_bepinex(tmp_path) is True

    def test_dll_directly_in_bepinex_dir(self, tmp_path):
        bep = tmp_path / "BepInEx"
        bep.mkdir()
        (bep / "BepInEx.dll").touch()
        assert check_bepinex(tmp_path) is True

    def test_other_dll_not_enough(self, tmp_path):
        core = tmp_path / "BepInEx" / "core"
        core.mkdir(parents=True)
        (core / "SomeOther.dll").touch()
        assert check_bepinex(tmp_path) is False


class TestFindValheim:
    def test_returns_first_existing_default_path(self, tmp_path):
        valheim = tmp_path / "Valheim"
        valheim.mkdir()
        with patch("vmm.utils.DEFAULT_VALHEIM_PATHS", [valheim, tmp_path / "other"]):
            assert find_valheim() == valheim

    def test_skips_missing_default_and_checks_next(self, tmp_path):
        first = tmp_path / "missing"
        second = tmp_path / "Valheim"
        second.mkdir()
        with patch("vmm.utils.DEFAULT_VALHEIM_PATHS", [first, second]):
            assert find_valheim() == second

    def test_falls_back_to_steam_library_paths(self, tmp_path):
        steam_valheim = tmp_path / "SteamLib" / "Valheim"
        steam_valheim.mkdir(parents=True)
        with patch("vmm.utils.DEFAULT_VALHEIM_PATHS", [tmp_path / "missing"]), \
             patch("vmm.utils._steam_library_valheim_paths", return_value=[steam_valheim]):
            assert find_valheim() == steam_valheim

    def test_returns_first_default_when_nothing_exists(self, tmp_path):
        defaults = [tmp_path / "a", tmp_path / "b"]
        with patch("vmm.utils.DEFAULT_VALHEIM_PATHS", defaults), \
             patch("vmm.utils._steam_library_valheim_paths", return_value=[]):
            assert find_valheim() == defaults[0]

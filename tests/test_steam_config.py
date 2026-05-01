import time
import pytest
from pathlib import Path
from unittest.mock import patch

from vmm.steam_config import (
    _build_launch_opts,
    _vdf_set_launch_opts,
    _find_localconfig,
    set_bepinex_launch_options,
)

# Realistic localconfig.vdf with two app sections
SAMPLE_VDF = (
    '"UserLocalConfigStore"\n'
    '{\n'
    '\t"Software"\n'
    '\t{\n'
    '\t\t"Valve"\n'
    '\t\t{\n'
    '\t\t\t"Steam"\n'
    '\t\t\t{\n'
    '\t\t\t\t"apps"\n'
    '\t\t\t\t{\n'
    '\t\t\t\t\t"892970"\n'
    '\t\t\t\t\t{\n'
    '\t\t\t\t\t\t"LastPlayed"\t\t"1700000000"\n'
    '\t\t\t\t\t\t"Playtime"\t\t"120"\n'
    '\t\t\t\t\t}\n'
    '\t\t\t\t\t"730"\n'
    '\t\t\t\t\t{\n'
    '\t\t\t\t\t\t"LastPlayed"\t\t"1700000001"\n'
    '\t\t\t\t\t\t"Playtime"\t\t"200"\n'
    '\t\t\t\t\t}\n'
    '\t\t\t\t}\n'
    '\t\t\t}\n'
    '\t\t}\n'
    '\t}\n'
    '}\n'
)

VDF_WITH_EXISTING_OPTS = SAMPLE_VDF.replace(
    '\t\t\t\t\t\t"LastPlayed"\t\t"1700000000"',
    '\t\t\t\t\t\t"LaunchOptions"\t\t"old_opts"\n'
    '\t\t\t\t\t\t"LastPlayed"\t\t"1700000000"',
)


# ---------------------------------------------------------------------------
# _build_launch_opts
# ---------------------------------------------------------------------------

class TestBuildLaunchOpts:
    def test_contains_script_path(self, tmp_path):
        valheim = tmp_path / "valheim"
        opts = _build_launch_opts(valheim)
        assert str(valheim / "start_game_bepinex.sh") in opts

    def test_ends_with_percent_command(self, tmp_path):
        opts = _build_launch_opts(tmp_path)
        assert opts.strip().endswith("%command%")

    def test_script_is_quoted(self, tmp_path):
        # Path is wrapped in double quotes to handle spaces
        valheim = tmp_path / "valheim"
        opts = _build_launch_opts(valheim)
        script = str(valheim / "start_game_bepinex.sh")
        assert f'"{script}"' in opts


# ---------------------------------------------------------------------------
# _vdf_set_launch_opts
# ---------------------------------------------------------------------------

class TestVdfSetLaunchOpts:
    def test_inserts_launch_options_in_correct_section(self):
        result = _vdf_set_launch_opts(SAMPLE_VDF, "892970", "./bep.sh %command%")
        assert result is not None
        assert '"LaunchOptions"' in result
        assert "./bep.sh %command%" in result

    def test_does_not_touch_other_app_sections(self):
        result = _vdf_set_launch_opts(SAMPLE_VDF, "892970", "./bep.sh %command%")
        assert result is not None
        # Section for CS2 (730) must remain unchanged
        assert '"730"' in result
        # LaunchOptions should not appear inside the 730 block
        idx_730 = result.index('"730"')
        idx_launch = result.index('"LaunchOptions"')
        assert idx_launch < idx_730

    def test_replaces_existing_launch_options(self):
        result = _vdf_set_launch_opts(VDF_WITH_EXISTING_OPTS, "892970", "new_opts")
        assert result is not None
        assert "new_opts" in result
        assert "old_opts" not in result

    def test_returns_none_for_unknown_app_id(self):
        assert _vdf_set_launch_opts(SAMPLE_VDF, "999999", "opts") is None

    def test_returns_none_when_section_has_no_playtime_or_lastplayed(self):
        vdf = '"892970"\n{\n\t"SomeKey"\t\t"val"\n}\n'
        assert _vdf_set_launch_opts(vdf, "892970", "opts") is None

    def test_escapes_double_quotes_in_opts(self):
        opts = 'cmd "arg"'
        result = _vdf_set_launch_opts(SAMPLE_VDF, "892970", opts)
        assert result is not None
        assert r'\"arg\"' in result

    def test_output_preserves_rest_of_file(self):
        result = _vdf_set_launch_opts(SAMPLE_VDF, "892970", "opts")
        assert result is not None
        assert '"UserLocalConfigStore"' in result
        assert '"Valve"' in result


# ---------------------------------------------------------------------------
# _find_localconfig
# ---------------------------------------------------------------------------

class TestFindLocalconfig:
    def test_returns_none_when_no_userdata_dir_exists(self, tmp_path):
        with patch("vmm.steam_config.Path.home", return_value=tmp_path / "no_home"):
            result = _find_localconfig()
        assert result is None

    def test_finds_vdf_in_default_steam_location(self, tmp_path):
        userdata = tmp_path / ".local" / "share" / "Steam" / "userdata"
        vdf = userdata / "12345" / "config" / "localconfig.vdf"
        vdf.parent.mkdir(parents=True)
        vdf.write_text("v1")

        with patch("vmm.steam_config.Path.home", return_value=tmp_path):
            result = _find_localconfig()

        assert result == vdf

    def test_returns_most_recently_modified_vdf(self, tmp_path):
        userdata = tmp_path / ".local" / "share" / "Steam" / "userdata"
        vdf1 = userdata / "user1" / "config" / "localconfig.vdf"
        vdf2 = userdata / "user2" / "config" / "localconfig.vdf"
        vdf1.parent.mkdir(parents=True)
        vdf2.parent.mkdir(parents=True)
        vdf1.write_text("old")
        time.sleep(0.02)
        vdf2.write_text("new")

        with patch("vmm.steam_config.Path.home", return_value=tmp_path):
            result = _find_localconfig()

        assert result == vdf2


# ---------------------------------------------------------------------------
# set_bepinex_launch_options
# ---------------------------------------------------------------------------

class TestSetBepInExLaunchOptions:
    def test_returns_false_when_vdf_not_found(self, tmp_path):
        with patch("vmm.steam_config._find_localconfig", return_value=None):
            assert set_bepinex_launch_options(tmp_path) is False

    def test_returns_true_and_modifies_vdf(self, tmp_path):
        vdf_path = tmp_path / "localconfig.vdf"
        vdf_path.write_text(SAMPLE_VDF, encoding="utf-8")
        valheim = tmp_path / "valheim"

        with patch("vmm.steam_config._find_localconfig", return_value=vdf_path):
            result = set_bepinex_launch_options(valheim)

        assert result is True
        content = vdf_path.read_text(encoding="utf-8")
        assert "LaunchOptions" in content
        assert "start_game_bepinex.sh" in content

    def test_returns_false_when_app_section_missing(self, tmp_path):
        vdf_path = tmp_path / "localconfig.vdf"
        vdf_path.write_text('"NoApps"\n{\n}\n', encoding="utf-8")

        with patch("vmm.steam_config._find_localconfig", return_value=vdf_path):
            result = set_bepinex_launch_options(tmp_path)

        assert result is False
        # File must be unchanged
        assert vdf_path.read_text() == '"NoApps"\n{\n}\n'

    def test_writes_atomically_no_tmp_leftover(self, tmp_path):
        vdf_path = tmp_path / "localconfig.vdf"
        vdf_path.write_text(SAMPLE_VDF, encoding="utf-8")

        with patch("vmm.steam_config._find_localconfig", return_value=vdf_path):
            set_bepinex_launch_options(tmp_path)

        assert not vdf_path.with_suffix(".tmp").exists()

    def test_returns_false_on_read_error(self, tmp_path):
        vdf_path = tmp_path / "localconfig.vdf"
        # File exists but cannot be read (simulate IOError)
        with patch("vmm.steam_config._find_localconfig", return_value=vdf_path), \
             patch("pathlib.Path.read_text", side_effect=IOError("disk error")):
            result = set_bepinex_launch_options(tmp_path)

        assert result is False

import io
import json
import zipfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import vmm.logic as logic_module
from vmm.logic import (
    load_config, save_config,
    load_installed, save_installed,
    _atomic_write, icon_cache_path, _root_install_info,
    ModManager,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_zip(files: dict) -> zipfile.ZipFile:
    """Return an open ZipFile (context manager) built from a {path: content} dict."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    buf.seek(0)
    return zipfile.ZipFile(buf)


@pytest.fixture()
def tmp_dirs(tmp_path):
    """Patch all vmm.logic path constants to point inside tmp_path."""
    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    installed_db = config_dir / "installed.json"
    icon_cache = config_dir / "cache" / "icons"
    download_dir = config_dir / "cache" / "downloads"

    with patch.multiple(
        "vmm.logic",
        CONFIG_DIR=config_dir,
        CONFIG_FILE=config_file,
        INSTALLED_DB=installed_db,
        ICON_CACHE_DIR=icon_cache,
        DOWNLOAD_DIR=download_dir,
    ):
        yield {
            "config_dir": config_dir,
            "config_file": config_file,
            "installed_db": installed_db,
            "icon_cache": icon_cache,
            "download_dir": download_dir,
        }


@pytest.fixture()
def manager(tmp_dirs, tmp_path):
    valheim = tmp_path / "valheim"
    valheim.mkdir()
    with patch("vmm.logic.find_valheim", return_value=valheim):
        mgr = ModManager()
    return mgr


# ---------------------------------------------------------------------------
# _atomic_write
# ---------------------------------------------------------------------------

class TestAtomicWrite:
    def test_writes_content(self, tmp_path):
        p = tmp_path / "out.json"
        _atomic_write(p, '{"ok": true}')
        assert p.read_text() == '{"ok": true}'

    def test_no_leftover_tmp_file(self, tmp_path):
        p = tmp_path / "out.json"
        _atomic_write(p, "data")
        assert not p.with_suffix(".tmp").exists()

    def test_overwrites_existing(self, tmp_path):
        p = tmp_path / "out.json"
        p.write_text("old")
        _atomic_write(p, "new")
        assert p.read_text() == "new"


# ---------------------------------------------------------------------------
# load_config / save_config
# ---------------------------------------------------------------------------

class TestConfig:
    def test_returns_default_when_file_missing(self, tmp_dirs):
        with patch("vmm.logic.find_valheim", return_value=Path("/fake/valheim")):
            cfg = load_config()
        assert "valheim_path" in cfg

    def test_round_trip(self, tmp_dirs):
        cfg = {"valheim_path": "/my/valheim", "extra": 42}
        save_config(cfg)
        assert load_config() == cfg

    def test_malformed_json_falls_back_to_default(self, tmp_dirs):
        tmp_dirs["config_file"].parent.mkdir(parents=True, exist_ok=True)
        tmp_dirs["config_file"].write_text("{ bad json }")
        with patch("vmm.logic.find_valheim", return_value=Path("/fake")):
            cfg = load_config()
        assert "valheim_path" in cfg

    def test_save_creates_parent_dirs(self, tmp_dirs):
        save_config({"valheim_path": "/x"})
        assert tmp_dirs["config_file"].exists()


# ---------------------------------------------------------------------------
# load_installed / save_installed
# ---------------------------------------------------------------------------

class TestInstalled:
    def test_empty_dict_when_file_missing(self, tmp_dirs):
        assert load_installed() == {}

    def test_round_trip(self, tmp_dirs):
        db = {"Author-Mod": {"version": "1.0.0", "name": "Mod"}}
        save_installed(db)
        assert load_installed() == db

    def test_malformed_json_returns_empty(self, tmp_dirs):
        tmp_dirs["installed_db"].parent.mkdir(parents=True, exist_ok=True)
        tmp_dirs["installed_db"].write_text("not json at all")
        assert load_installed() == {}

    def test_save_creates_parent_dirs(self, tmp_dirs):
        save_installed({"A-B": {}})
        assert tmp_dirs["installed_db"].exists()


# ---------------------------------------------------------------------------
# icon_cache_path
# ---------------------------------------------------------------------------

class TestIconCachePath:
    def test_same_url_same_path(self):
        url = "https://example.com/icon.png"
        assert icon_cache_path(url) == icon_cache_path(url)

    def test_different_urls_different_paths(self):
        assert icon_cache_path("https://a.com/1.png") != icon_cache_path("https://a.com/2.png")

    def test_always_has_png_extension(self):
        assert icon_cache_path("https://example.com/icon.jpg").suffix == ".png"


# ---------------------------------------------------------------------------
# _root_install_info
# ---------------------------------------------------------------------------

class TestRootInstallInfo:
    def test_bepinex_pack_is_root(self):
        files = {
            "BepInExPack_Valheim/BepInEx/core/BepInEx.dll": "x",
            "BepInExPack_Valheim/doorstop_libs/libdoorstop.so": "x",
            "BepInExPack_Valheim/start_game_bepinex.sh": "x",
        }
        with make_zip(files) as zf:
            is_root, prefix = _root_install_info(zf)
        assert is_root is True
        assert prefix == "BepInExPack_Valheim/"

    def test_regular_plugin_is_not_root(self):
        files = {
            "Author-Mod-1.0.0/plugin.dll": "x",
            "Author-Mod-1.0.0/manifest.json": "{}",
        }
        with make_zip(files) as zf:
            is_root, prefix = _root_install_info(zf)
        assert is_root is False
        assert prefix == ""

    def test_doorstop_libs_triggers_root(self):
        files = {
            "SomePack/doorstop_libs/lib.so": "x",
            "SomePack/readme.md": "",
        }
        with make_zip(files) as zf:
            is_root, _ = _root_install_info(zf)
        assert is_root is True

    def test_launch_script_triggers_root(self):
        files = {
            "Pack/start_game_bepinex.sh": "#!/bin/bash",
            "Pack/readme.md": "",
        }
        with make_zip(files) as zf:
            is_root, _ = _root_install_info(zf)
        assert is_root is True

    def test_server_script_triggers_root(self):
        files = {
            "Pack/start_server_bepinex.sh": "#!/bin/bash",
        }
        with make_zip(files) as zf:
            is_root, _ = _root_install_info(zf)
        assert is_root is True

    def test_flat_zip_no_top_prefix(self):
        files = {
            "plugin.dll": "x",
            "manifest.json": "{}",
        }
        with make_zip(files) as zf:
            is_root, prefix = _root_install_info(zf)
        assert is_root is False
        assert prefix == ""


# ---------------------------------------------------------------------------
# ModManager — basic properties and query methods
# ---------------------------------------------------------------------------

class TestModManagerQueries:
    def test_is_installed_false_initially(self, manager):
        assert manager.is_installed("Author-Mod") is False

    def test_is_installed_true_after_insertion(self, manager):
        manager.installed["Author-Mod"] = {"version": "1.0.0"}
        assert manager.is_installed("Author-Mod") is True

    def test_installed_version_none_when_absent(self, manager):
        assert manager.installed_version("Author-Mod") is None

    def test_installed_version_returns_version(self, manager):
        manager.installed["Author-Mod"] = {"version": "2.3.1"}
        assert manager.installed_version("Author-Mod") == "2.3.1"

    def test_has_update_false_when_not_installed(self, manager):
        pkg = {"full_name": "Author-Mod", "versions": [{"version_number": "2.0.0"}]}
        assert manager.has_update(pkg) is False

    def test_has_update_false_when_same_version(self, manager):
        manager.installed["Author-Mod"] = {"version": "1.0.0"}
        pkg = {"full_name": "Author-Mod", "versions": [{"version_number": "1.0.0"}]}
        assert manager.has_update(pkg) is False

    def test_has_update_true_when_newer_available(self, manager):
        manager.installed["Author-Mod"] = {"version": "1.0.0"}
        pkg = {"full_name": "Author-Mod", "versions": [{"version_number": "2.0.0"}]}
        assert manager.has_update(pkg) is True

    def test_count_updates(self, manager):
        manager.installed["A-Mod1"] = {"version": "1.0.0"}
        manager.installed["A-Mod2"] = {"version": "1.0.0"}
        packages = [
            {"full_name": "A-Mod1", "versions": [{"version_number": "2.0.0"}]},
            {"full_name": "A-Mod2", "versions": [{"version_number": "1.0.0"}]},
        ]
        assert manager.count_updates(packages) == 1

    def test_count_updates_zero(self, manager):
        packages = [{"full_name": "A-Mod", "versions": [{"version_number": "1.0.0"}]}]
        assert manager.count_updates(packages) == 0

    def test_plugins_path(self, manager):
        assert manager.plugins_path == manager.valheim_path / "BepInEx" / "plugins"

    def test_has_bepinex_false_initially(self, manager):
        assert manager.has_bepinex is False

    def test_has_bepinex_true_with_dll(self, manager):
        core = manager.valheim_path / "BepInEx" / "core"
        core.mkdir(parents=True)
        (core / "BepInEx.dll").touch()
        assert manager.has_bepinex is True


# ---------------------------------------------------------------------------
# ModManager — set_valheim_path
# ---------------------------------------------------------------------------

class TestSetValheimPath:
    def test_updates_config_and_persists(self, manager, tmp_path):
        new_path = str(tmp_path / "new_valheim")
        manager.set_valheim_path(new_path)
        assert manager.config["valheim_path"] == new_path
        # Persisted to disk
        assert load_config()["valheim_path"] == new_path


# ---------------------------------------------------------------------------
# ModManager — set_enabled
# ---------------------------------------------------------------------------

@pytest.fixture()
def manager_with_plugin(tmp_dirs, tmp_path):
    valheim = tmp_path / "valheim"
    valheim.mkdir()
    install_dir = tmp_path / "plugins" / "Author-Mod"
    install_dir.mkdir(parents=True)
    (install_dir / "plugin.dll").touch()

    with patch("vmm.logic.find_valheim", return_value=valheim):
        mgr = ModManager()
    mgr.installed["Author-Mod"] = {
        "install_dir": str(install_dir),
        "enabled": True,
        "version": "1.0.0",
        "name": "Mod",
    }
    return mgr, install_dir


class TestSetEnabled:
    def test_disable_renames_dir_to_disabled(self, manager_with_plugin):
        mgr, install_dir = manager_with_plugin
        assert mgr.set_enabled("Author-Mod", False) is True
        assert not install_dir.exists()
        assert Path(str(install_dir) + ".disabled").exists()
        assert mgr.installed["Author-Mod"]["enabled"] is False

    def test_enable_restores_dir_from_disabled(self, manager_with_plugin):
        mgr, install_dir = manager_with_plugin
        mgr.set_enabled("Author-Mod", False)
        assert mgr.set_enabled("Author-Mod", True) is True
        assert install_dir.exists()
        assert not Path(str(install_dir) + ".disabled").exists()
        assert mgr.installed["Author-Mod"]["enabled"] is True

    def test_unknown_mod_returns_false(self, manager_with_plugin):
        mgr, _ = manager_with_plugin
        assert mgr.set_enabled("NonExistent-Mod", False) is False

    def test_state_persisted_after_toggle(self, manager_with_plugin):
        mgr, _ = manager_with_plugin
        mgr.set_enabled("Author-Mod", False)
        assert load_installed()["Author-Mod"]["enabled"] is False


# ---------------------------------------------------------------------------
# ModManager — uninstall
# ---------------------------------------------------------------------------

class TestUninstall:
    def test_plugin_removes_dir_and_db_entry(self, manager_with_plugin):
        mgr, install_dir = manager_with_plugin
        name = mgr.uninstall("Author-Mod")
        assert name == "Mod"
        assert not install_dir.exists()
        assert "Author-Mod" not in mgr.installed

    def test_unknown_mod_returns_none(self, manager_with_plugin):
        mgr, _ = manager_with_plugin
        assert mgr.uninstall("NonExistent-Mod") is None

    def test_also_removes_disabled_variant(self, manager_with_plugin):
        mgr, install_dir = manager_with_plugin
        disabled = Path(str(install_dir) + ".disabled")
        install_dir.rename(disabled)
        mgr.uninstall("Author-Mod")
        assert not disabled.exists()

    def test_root_install_only_removes_db_entry(self, manager_with_plugin):
        mgr, install_dir = manager_with_plugin
        mgr.installed["Author-Mod"]["install_type"] = "root"
        mgr.uninstall("Author-Mod")
        # Files on disk preserved — root packs live inside the game dir
        assert install_dir.exists()
        assert "Author-Mod" not in mgr.installed

    def test_uninstall_persists_db(self, manager_with_plugin):
        mgr, _ = manager_with_plugin
        mgr.uninstall("Author-Mod")
        assert "Author-Mod" not in load_installed()


# ---------------------------------------------------------------------------
# ModManager — open_folder
# ---------------------------------------------------------------------------

class TestOpenFolder:
    def test_calls_xdg_open(self, manager_with_plugin):
        mgr, install_dir = manager_with_plugin
        with patch("vmm.logic.subprocess.Popen") as mock_popen:
            mgr.open_folder("Author-Mod")
        mock_popen.assert_called_once_with(["xdg-open", str(install_dir)])

    def test_does_nothing_for_unknown_mod(self, manager):
        with patch("vmm.logic.subprocess.Popen") as mock_popen:
            manager.open_folder("NonExistent-Mod")
        mock_popen.assert_not_called()

    def test_does_nothing_when_dir_missing(self, manager_with_plugin):
        import shutil
        mgr, install_dir = manager_with_plugin
        shutil.rmtree(install_dir)
        with patch("vmm.logic.subprocess.Popen") as mock_popen:
            mgr.open_folder("Author-Mod")
        mock_popen.assert_not_called()

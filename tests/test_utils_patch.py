import logging
import pytest
from pathlib import Path

from vmm.utils_patch import patch_launch_script

# Realistic start_game_bepinex.sh fragment that contains the insertion point
BEPINEX_SCRIPT = (
    '#!/bin/bash\n'
    '# BepInEx runner script\n'
    '\n'
    'executable_path="$1"\n'
    'doorstop_name="libdoorstop_x64.so"\n'
    '\n'
    'if [ "$(uname -s)" = "Darwin" ]; then\n'
    '    export DYLD_INSERT_LIBRARIES="${doorstop_name}:${DYLD_INSERT_LIBRARIES}"\n'
    'fi\n'
    '\n'
    '"$executable_path" "$@" &\n'
    'PID=$!\n'
    'wait $PID\n'
)

PATCHED_MARKER = "export SteamAppId=892970"


@pytest.fixture()
def valheim(tmp_path):
    d = tmp_path / "valheim"
    d.mkdir()
    return d


def write_script(valheim: Path, content: str) -> Path:
    script = valheim / "start_game_bepinex.sh"
    script.write_text(content)
    return script


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPatchLaunchScript:
    def test_no_op_when_script_absent(self, valheim):
        # Must not raise even when the script does not exist
        patch_launch_script(valheim)

    def test_patches_unpatched_script(self, valheim):
        script = write_script(valheim, BEPINEX_SCRIPT)
        patch_launch_script(valheim)
        content = script.read_text()
        assert "export SteamAppId=892970" in content
        assert "export SteamAppID=892970" in content

    def test_no_op_when_already_patched(self, valheim):
        already_patched = BEPINEX_SCRIPT + f"\n{PATCHED_MARKER}\nexport SteamAppID=892970\n"
        script = write_script(valheim, already_patched)
        mtime_before = script.stat().st_mtime_ns

        patch_launch_script(valheim)

        # File must not have been rewritten
        assert script.stat().st_mtime_ns == mtime_before
        assert script.read_text().count(PATCHED_MARKER) == 1

    def test_patch_inserted_after_insertion_point(self, valheim):
        script = write_script(valheim, BEPINEX_SCRIPT)
        patch_launch_script(valheim)
        content = script.read_text()

        insertion_point = 'export DYLD_INSERT_LIBRARIES="${doorstop_name}:${DYLD_INSERT_LIBRARIES}"\nfi\n'
        idx_ip = content.index(insertion_point)
        idx_steam = content.index(PATCHED_MARKER)
        assert idx_steam > idx_ip

    def test_executable_path_launch_still_present(self, valheim):
        write_script(valheim, BEPINEX_SCRIPT)
        patch_launch_script(valheim)
        content = (valheim / "start_game_bepinex.sh").read_text()
        assert '"$executable_path" "$@" &' in content

    def test_logs_warning_on_unknown_format(self, valheim, caplog):
        write_script(valheim, "#!/bin/bash\necho unknown\n")
        with caplog.at_level(logging.WARNING, logger="ValheimModManager"):
            patch_launch_script(valheim)
        assert any("format inconnu" in r.message for r in caplog.records)

    def test_unknown_format_leaves_script_unchanged(self, valheim):
        original = "#!/bin/bash\necho unknown\n"
        script = write_script(valheim, original)
        patch_launch_script(valheim)
        assert script.read_text() == original

    def test_both_steamappid_variants_added(self, valheim):
        write_script(valheim, BEPINEX_SCRIPT)
        patch_launch_script(valheim)
        content = (valheim / "start_game_bepinex.sh").read_text()
        # Steamworks requires both casing variants on some distributions
        assert "export SteamAppId=892970" in content
        assert "export SteamAppID=892970" in content

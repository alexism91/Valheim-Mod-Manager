from pathlib import Path
import logging

logger = logging.getLogger("ValheimModManager")

def patch_launch_script(valheim_path: Path):
    script_path = valheim_path / "start_game_bepinex.sh"
    if not script_path.exists():
        return
    
    content = script_path.read_text()
    
    # Check if patched
    if "export SteamAppId=892970" in content:
        return

    # Look for the last lines before the final launch
    # In the provided script, it ends with:
    # export DYLD_INSERT_LIBRARIES="${doorstop_name}:${DYLD_INSERT_LIBRARIES}"
    # fi
    #
    # "$executable_path" "$@" &
    # PID=$!
    # wait $PID
    
    patch = '\nexport SteamAppId=892970\nexport SteamAppID=892970\n'
    insertion_point = 'export DYLD_INSERT_LIBRARIES="${doorstop_name}:${DYLD_INSERT_LIBRARIES}"\nfi\n'
    
    if insertion_point in content:
        new_content = content.replace(insertion_point, insertion_point + patch)
        script_path.write_text(new_content)
        logger.info("Script de lancement auto-patché.")
    else:
        logger.warning("Impossible de patcher le script : format inconnu.")

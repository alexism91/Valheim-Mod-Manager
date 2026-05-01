from pathlib import Path

THUNDERSTORE_API  = "https://thunderstore.io/c/valheim/api/v1/package/"
THUNDERSTORE_URL  = "https://thunderstore.io/c/valheim"
APP_ID            = "io.github.valheim.modmanager"
APP_VERSION       = "2.0.0"
APP_NAME          = "Valheim Mod Manager"
BATCH_SIZE        = 80
SEARCH_DEBOUNCE   = 280   # ms

DEFAULT_VALHEIM_PATHS = [
    Path.home() / ".local/share/Steam/steamapps/common/Valheim",
    Path.home() / ".steam/steam/steamapps/common/Valheim",
    Path("/usr/share/Steam/steamapps/common/Valheim"),
]
CONFIG_DIR     = Path.home() / ".config/valheim-mod-manager"
CONFIG_FILE    = CONFIG_DIR / "config.json"
INSTALLED_DB   = CONFIG_DIR / "installed.json"
ICON_CACHE_DIR = CONFIG_DIR / "cache/icons"
DOWNLOAD_DIR   = CONFIG_DIR / "cache/downloads"

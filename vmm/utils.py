import logging
from pathlib import Path
from datetime import datetime, timezone
from vmm.constants import DEFAULT_VALHEIM_PATHS

logger = logging.getLogger("ValheimModManager")

def fmt_number(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)

def fmt_size(path: Path) -> str:
    try:
        total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        if total >= 1_048_576:
            return f"{total / 1_048_576:.1f} Mo"
        if total >= 1_024:
            return f"{total / 1_024:.0f} Ko"
        return f"{total} o"
    except Exception as e:
        logger.error(f"Erreur lors du calcul de la taille pour {path}: {e}")
        return "?"

def fmt_date(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = (now - dt).days
        if diff == 0:
            return "Aujourd'hui"
        if diff == 1:
            return "Hier"
        if diff < 7:
            return f"Il y a {diff} jours"
        if diff < 30:
            return f"Il y a {diff // 7} semaine{'s' if diff >= 14 else ''}"
        if diff < 365:
            return f"Il y a {diff // 30} mois"
        return f"Il y a {diff // 365} an{'s' if diff >= 730 else ''}"
    except Exception as e:
        logger.warning(f"Format de date invalide '{iso}': {e}")
        return iso[:10] if iso else "?"

def _steam_library_valheim_paths() -> list[Path]:
    """Lit libraryfolders.vdf pour trouver Valheim dans toutes les bibliothèques Steam."""
    import re
    candidates: list[Path] = []
    seen: set[str] = set()
    vdf_locations = [
        Path.home() / ".local/share/Steam/steamapps/libraryfolders.vdf",
        Path.home() / ".steam/steam/steamapps/libraryfolders.vdf",
    ]
    for vdf in vdf_locations:
        if not vdf.exists():
            continue
        try:
            for lib in re.findall(r'"path"\s+"([^"]+)"', vdf.read_text()):
                p = Path(lib) / "steamapps" / "common" / "Valheim"
                if str(p) not in seen:
                    seen.add(str(p))
                    candidates.append(p)
        except Exception as e:
            logger.warning(f"Lecture libraryfolders.vdf échouée: {e}")
    return candidates

def find_valheim() -> Path:
    for p in DEFAULT_VALHEIM_PATHS:
        if p.exists():
            return p
    for p in _steam_library_valheim_paths():
        if p.exists():
            return p
    return DEFAULT_VALHEIM_PATHS[0]

def check_bepinex(valheim_path: Path) -> bool:
    return (valheim_path / "BepInEx" / "core" / "BepInEx.dll").exists() or \
           (valheim_path / "BepInEx" / "BepInEx.dll").exists()

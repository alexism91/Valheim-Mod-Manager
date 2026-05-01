import os
import re
import logging
from pathlib import Path

logger = logging.getLogger("ValheimModManager")

VALHEIM_APP_ID = "892970"


def _build_launch_opts(valheim_path: Path) -> str:
    script = str(valheim_path / "start_game_bepinex.sh")
    return f'"{script}" %command%'


def _find_localconfig() -> Path | None:
    roots = [
        Path.home() / ".local/share/Steam/userdata",
        Path.home() / ".steam/steam/userdata",
    ]
    seen: set[str] = set()
    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for vdf in root.glob("*/config/localconfig.vdf"):
            k = str(vdf.resolve())
            if k not in seen:
                seen.add(k)
                candidates.append(vdf)
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def _vdf_set_launch_opts(content: str, app_id: str, opts: str) -> str | None:
    """
    Trouve la section {app_id} contenant LastPlayed/Playtime et
    y insère ou remplace LaunchOptions.
    Retourne le contenu modifié, ou None si la section est introuvable.
    """
    opts_escaped = opts.replace('"', '\\"')
    pos = 0

    while pos < len(content):
        m = re.search(rf'"{re.escape(app_id)}"\s*\{{', content[pos:])
        if not m:
            break

        abs_open = pos + m.end() - 1  # index du '{'
        # Trouve l'accolade fermante correspondante
        depth = 0
        i = abs_open
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        else:
            break

        section = content[abs_open + 1:i]

        # C'est la section "apps" si elle contient LastPlayed ou Playtime
        if '"LastPlayed"' not in section and '"Playtime"' not in section:
            pos = pos + m.start() + 1
            continue

        # Détecte l'indentation depuis les lignes existantes
        indent_m = re.search(r'^(\t+)"', section, re.MULTILINE)
        indent = indent_m.group(1) if indent_m else '\t\t\t\t\t\t'

        if '"LaunchOptions"' in section:
            new_section = re.sub(
                r'"LaunchOptions"\s*"(?:[^"\\]|\\.)*"',
                f'"LaunchOptions"\t\t"{opts_escaped}"',
                section,
            )
        else:
            new_section = section.rstrip() + f'\n{indent}"LaunchOptions"\t\t"{opts_escaped}"\n'

        return content[:abs_open + 1] + new_section + content[i:]

    return None


def set_bepinex_launch_options(valheim_path: Path) -> bool:
    """
    Écrit les options de lancement BepInEx dans le localconfig.vdf de Steam.
    Retourne True si la modification a réussi.
    """
    vdf = _find_localconfig()
    if not vdf:
        logger.warning("localconfig.vdf Steam introuvable")
        return False
    try:
        content = vdf.read_text(encoding="utf-8")
        opts = _build_launch_opts(valheim_path)
        new_content = _vdf_set_launch_opts(content, VALHEIM_APP_ID, opts)
        if new_content is None:
            logger.warning(f"Section {VALHEIM_APP_ID} non trouvée dans {vdf}")
            return False
        tmp = vdf.with_suffix(".tmp")
        tmp.write_text(new_content, encoding="utf-8")
        os.replace(tmp, vdf)
        logger.info(f"Options Steam BepInEx configurées dans {vdf}")
        return True
    except Exception as e:
        logger.error(f"Erreur modification localconfig.vdf: {e}")
        return False

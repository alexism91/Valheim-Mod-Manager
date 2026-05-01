import ctypes
import logging
from pathlib import Path

logger = logging.getLogger("ValheimModManager")

FONTS_DIR = Path(__file__).parent / "fonts"

def load_bundled_fonts() -> None:
    if not FONTS_DIR.exists():
        logger.warning(f"Dossier polices introuvable : {FONTS_DIR}")
        return
    try:
        fc = ctypes.CDLL("libfontconfig.so.1")
        fc.FcConfigAppFontAddDir(None, str(FONTS_DIR).encode())
        logger.info(f"Polices chargées depuis {FONTS_DIR}")
    except OSError as e:
        logger.warning(f"libfontconfig introuvable, polices système utilisées : {e}")
    except Exception as e:
        logger.error(f"Erreur chargement polices : {e}")

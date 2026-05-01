import os
import stat as _stat
import json
import logging
import threading
import zipfile
import shutil
import hashlib
import urllib.request
import subprocess
from pathlib import Path
from datetime import datetime

from vmm.steam_config import set_bepinex_launch_options

import gi
from gi.repository import GLib

from vmm.constants import (
    THUNDERSTORE_API, APP_NAME, APP_VERSION,
    CONFIG_DIR, CONFIG_FILE, INSTALLED_DB,
    ICON_CACHE_DIR, DOWNLOAD_DIR
)
from vmm.utils import find_valheim, check_bepinex, fmt_number

logger = logging.getLogger("ValheimModManager")

def ensure_dirs():
    for d in [CONFIG_DIR, ICON_CACHE_DIR, DOWNLOAD_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def _atomic_write(path: Path, content: str):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content)
    os.replace(tmp, path)

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception as e:
            logger.error(f"Erreur de lecture du fichier config {CONFIG_FILE}: {e}")
    return {"valheim_path": str(find_valheim())}

def save_config(cfg: dict):
    ensure_dirs()
    _atomic_write(CONFIG_FILE, json.dumps(cfg, indent=2))

def load_installed() -> dict:
    if INSTALLED_DB.exists():
        try:
            return json.loads(INSTALLED_DB.read_text())
        except Exception as e:
            logger.error(f"Erreur de lecture de la DB installee {INSTALLED_DB}: {e}")
    return {}

def save_installed(db: dict):
    ensure_dirs()
    _atomic_write(INSTALLED_DB, json.dumps(db, indent=2))

def icon_cache_path(url: str) -> Path:
    return ICON_CACHE_DIR / (hashlib.md5(url.encode()).hexdigest() + ".png")

def fetch_icon_async(url: str, callback: callable):
    def _run():
        try:
            p = icon_cache_path(url)
            if not p.exists():
                req = urllib.request.Request(
                    url, headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"}
                )
                with urllib.request.urlopen(req, timeout=15) as r:
                    p.write_bytes(r.read())
            GLib.idle_add(callback, str(p))
        except Exception as e:
            logger.error(f"Echec du telechargement de l'icone {url}: {e}")
    threading.Thread(target=_run, daemon=True).start()

def _root_install_info(zf: zipfile.ZipFile) -> tuple[bool, str]:
    """
    Détecte si un package doit s'installer à la racine du jeu (ex: BepInEx).
    Retourne (needs_root, prefix_à_supprimer).
    Le prefix est le dossier de premier niveau du zip (ex: 'BepInExPack_Valheim/').
    """
    names = [m.filename for m in zf.infolist()]
    # Trouve le préfixe commun de premier niveau
    top_dirs: set[str] = set()
    for name in names:
        parts = name.split("/")
        if len(parts) > 1 and parts[0]:
            top_dirs.add(parts[0])
    prefix = (top_dirs.pop() + "/") if len(top_dirs) == 1 else ""
    # Vérifie si les contenus (sans le préfixe) indiquent un pack racine
    stripped = [n[len(prefix):] if n.startswith(prefix) else n for n in names]
    is_root = any(
        n.startswith("BepInEx/core/") or
        n.startswith("doorstop_libs/") or
        n in ("start_game_bepinex.sh", "start_server_bepinex.sh", "winhttp.dll")
        for n in stripped
    )
    return is_root, prefix if is_root else ""


class ModManager:
    def __init__(self) -> None:
        ensure_dirs()
        self.config: dict = load_config()
        self.installed: dict = load_installed()

    @property
    def valheim_path(self) -> Path:
        return Path(self.config.get("valheim_path", str(find_valheim())))

    @property
    def plugins_path(self) -> Path:
        return self.valheim_path / "BepInEx" / "plugins"

    @property
    def has_bepinex(self) -> bool:
        return check_bepinex(self.valheim_path)

    def is_installed(self, pkg_full_name: str) -> bool:
        return pkg_full_name in self.installed

    def installed_version(self, pkg_full_name: str) -> str | None:
        return self.installed.get(pkg_full_name, {}).get("version")

    def has_update(self, pkg: dict) -> bool:
        full = pkg.get("full_name", "")
        if not self.is_installed(full):
            return False
        inst_v = self.installed_version(full)
        latest = pkg["versions"][0]["version_number"] if pkg.get("versions") else None
        return bool(inst_v and latest and inst_v != latest)

    def set_valheim_path(self, path: str) -> None:
        self.config["valheim_path"] = path
        save_config(self.config)

    def count_updates(self, packages: list) -> int:
        return sum(1 for p in packages if self.has_update(p))

    def set_enabled(self, pkg_full_name: str, enabled: bool) -> bool:
        info = self.installed.get(pkg_full_name)
        if not info:
            return False
        install_dir  = Path(info["install_dir"])
        disabled_dir = Path(str(install_dir) + ".disabled")
        try:
            if enabled and disabled_dir.exists():
                disabled_dir.rename(install_dir)
            elif not enabled and install_dir.exists():
                install_dir.rename(disabled_dir)
            info["enabled"] = enabled
            save_installed(self.installed)
            return True
        except Exception as e:
            logger.error(f"Erreur toggle {pkg_full_name}: {e}")
            return False

    def fetch_packages_async(self, on_page: callable, on_done: callable, on_error: callable) -> None:
        def _run():
            url   = THUNDERSTORE_API
            total = 0
            try:
                while url:
                    req = urllib.request.Request(
                        url,
                        headers={
                            "Accept": "application/json",
                            "User-Agent": f"{APP_NAME}/{APP_VERSION}",
                        },
                    )
                    with urllib.request.urlopen(req, timeout=30) as r:
                        data = json.loads(r.read().decode())
                    if isinstance(data, list):
                        GLib.idle_add(on_page, data)
                        total += len(data); url = None
                    else:
                        results = data.get("results", [])
                        GLib.idle_add(on_page, results)
                        total += len(results)
                        url = data.get("next")
                GLib.idle_add(on_done, total)
            except Exception as e:
                GLib.idle_add(on_error, str(e))
        threading.Thread(target=_run, daemon=True).start()

    def install_async(self, package: dict, version: dict,
                      on_progress: callable, on_done: callable, on_error: callable) -> None:
        def _run():
            try:
                pkg_full_name = package["full_name"]
                download_url  = version["download_url"]
                steps = [
                    (0.05, "Connexion aux serveurs..."),
                    (0.72, "Extraction du butin..."),
                    (0.95, "Inscription dans les runes..."),
                    (1.00, "Par Odin, c'est en place !"),
                ]

                GLib.idle_add(on_progress, *steps[0])
                zip_path = DOWNLOAD_DIR / f"{version['full_name']}.zip"

                req = urllib.request.Request(
                    download_url,
                    headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"},
                )
                with urllib.request.urlopen(req, timeout=120) as r:
                    total      = int(r.headers.get("Content-Length", 0) or 0)
                    downloaded = 0
                    with open(zip_path, "wb") as f:
                        while True:
                            chunk = r.read(16_384)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total:
                                prog = 0.06 + 0.64 * downloaded / total
                                GLib.idle_add(
                                    on_progress, prog,
                                    f"Telechargement... {fmt_number(downloaded//1024)} / "
                                    f"{fmt_number(total//1024)} Ko",
                                )

                GLib.idle_add(on_progress, *steps[1])

                expected_sha = version.get("file_sha256")
                if expected_sha:
                    sha256_hash = hashlib.sha256()
                    with open(zip_path, "rb") as f:
                        for byte_block in iter(lambda: f.read(4096), b""):
                            sha256_hash.update(byte_block)
                    if sha256_hash.hexdigest() != expected_sha:
                        raise ValueError(f"Echec de verification SHA256 pour {pkg_full_name}")

                with zipfile.ZipFile(zip_path) as zf:
                    is_root, strip_prefix = _root_install_info(zf)

                    if is_root:
                        install_dir = self.valheim_path
                        install_dir.mkdir(parents=True, exist_ok=True)
                        resolved_install = install_dir.resolve()
                        for member in zf.infolist():
                            if member.is_dir():
                                continue
                            rel = member.filename[len(strip_prefix):] if member.filename.startswith(strip_prefix) else member.filename
                            if not rel:
                                continue
                            dest = (install_dir / rel).resolve()
                            if not str(dest).startswith(str(resolved_install)):
                                raise ValueError(f"Fichier malveillant: {member.filename}")
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            dest.write_bytes(zf.read(member))
                        for sh in install_dir.glob("*.sh"):
                            sh.chmod(sh.stat().st_mode | _stat.S_IXUSR | _stat.S_IXGRP | _stat.S_IXOTH)
                        steam_ok = set_bepinex_launch_options(self.valheim_path)
                        package["_steam_opts_set"] = steam_ok
                    else:
                        install_dir = self.plugins_path / pkg_full_name
                        if install_dir.exists():
                            shutil.rmtree(install_dir)
                        install_dir.mkdir(parents=True, exist_ok=True)
                        resolved_install = install_dir.resolve()
                        for member in zf.infolist():
                            dest = (install_dir / member.filename).resolve()
                            if not str(dest).startswith(str(resolved_install)):
                                raise ValueError(f"Fichier malveillant: {member.filename}")
                        zf.extractall(install_dir)

                zip_path.unlink(missing_ok=True)

                GLib.idle_add(on_progress, *steps[2])
                self.installed[pkg_full_name] = {
                    "full_name":    pkg_full_name,
                    "version":      version["version_number"],
                    "name":         package["name"],
                    "owner":        package["owner"],
                    "install_dir":  str(install_dir),
                    "install_type": "root" if is_root else "plugin",
                    "install_date": datetime.now().isoformat(),
                    "enabled":      True,
                }
                save_installed(self.installed)

                GLib.idle_add(on_progress, *steps[3])
                GLib.idle_add(on_done, package)
            except Exception as e:
                GLib.idle_add(on_error, str(e))
        threading.Thread(target=_run, daemon=True).start()

    def uninstall(self, pkg_full_name: str) -> str | None:
        info = self.installed.pop(pkg_full_name, None)
        if info is None:
            return None
        if info.get("install_type") == "root":
            # Les packs racine (BepInEx) ne peuvent pas être supprimés par rmtree
            # car ils s'installent dans le répertoire du jeu lui-même
            save_installed(self.installed)
        else:
            d = Path(info.get("install_dir", ""))
            for path in [d, Path(str(d) + ".disabled")]:
                if path.exists():
                    shutil.rmtree(path, ignore_errors=True)
            save_installed(self.installed)
        return info.get("name", pkg_full_name)

    def open_folder(self, pkg_full_name: str) -> None:
        info = self.installed.get(pkg_full_name)
        if not info:
            return
        path = info.get("install_dir", "")
        if path and Path(path).exists():
            try:
                subprocess.Popen(["xdg-open", path])
            except Exception as e:
                logger.error(f"Erreur lors de l'ouverture du dossier {path}: {e}")

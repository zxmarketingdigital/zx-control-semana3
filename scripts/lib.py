#!/usr/bin/env python3
"""
Utilitarios compartilhados da Semana 3 — ZX Control.
Adaptado de lib.py da Semana 2, com paths de prospeccao.
"""

import json
import re
import os
import platform
import shutil
from datetime import datetime
from pathlib import Path


PLATFORM = platform.system()  # "Darwin", "Windows", "Linux"

BASE_DIR = Path.home() / ".operacao-ia"
CONFIG_PATH = BASE_DIR / "config" / "config.json"
CHECKPOINT_PATH = BASE_DIR / "config" / "week3_checkpoint.json"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
SCRIPTS_DIR = BASE_DIR / "scripts"
MISSION_CONTROL_DIR = BASE_DIR / "mission-control"
HEARTBEAT_DIR = LOGS_DIR / "heartbeat"

# Prospecting paths (Semana 3)
PROSPECTING_DIR = BASE_DIR / "prospecting"
PROSPECTING_LEADS_DIR = PROSPECTING_DIR / "leads"
PROSPECTING_CAMPAIGNS_DIR = PROSPECTING_DIR / "campaigns"
PROSPECTING_DASHBOARDS_DIR = PROSPECTING_DIR / "dashboards"
PROSPECTING_TEMPLATES_DIR = PROSPECTING_DIR / "templates"
PROSPECTING_LOGS_DIR = LOGS_DIR / "prospecting"
PROSPECTING_PROFILE_PATH = BASE_DIR / "config" / "prospecting_profile.json"
PROSPECTS_DB_PATH = DATA_DIR / "prospects.db"
LEADS_JSON_PATH = PROSPECTING_DASHBOARDS_DIR / "leads.json"
DASHBOARD_HTML_PATH = PROSPECTING_DASHBOARDS_DIR / "prospecting-dashboard.html"
RATE_LIMITS_PATH = DATA_DIR / "rate_limits.json"


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def ensure_structure():
    for path in [
        DATA_DIR, LOGS_DIR, SCRIPTS_DIR, MISSION_CONTROL_DIR, HEARTBEAT_DIR,
        PROSPECTING_DIR, PROSPECTING_LEADS_DIR, PROSPECTING_CAMPAIGNS_DIR,
        PROSPECTING_DASHBOARDS_DIR, PROSPECTING_TEMPLATES_DIR, PROSPECTING_LOGS_DIR,
        BASE_DIR / "config",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def _minimal_config():
    """Config minimo para quem instala este setup sem ter feito outro antes."""
    return {
        "output_dir": str(BASE_DIR),
        "setup_date": datetime.now().date().isoformat(),
        "phase_completed": 0,
    }


class ConfigBackupError(OSError):
    """Nao foi possivel guardar copia de seguranca do config; o original NAO foi tocado."""


def backup_config_copy(path):
    """Copia (copy2) o config para <nome>.bak-<AAAAmmdd-HHMMSS>[-N], sem sobrescrever backup existente.

    Confere que o destino existe com o mesmo tamanho. Em falha, o original fica intacto
    e levanta ConfigBackupError (so entao o chamador pode recriar o config).
    """
    path = Path(path)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = None
    try:
        n = 0
        while backup is None:
            candidate = path.with_name("%s.bak-%s%s" % (path.name, stamp, "-%d" % n if n else ""))
            try:
                # O_EXCL: a criação é atômica; se outro processo pegou o nome, tenta o próximo sufixo.
                fd = os.open(str(candidate), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                n += 1
                continue
            backup = candidate
            with os.fdopen(fd, "wb") as dst, open(str(path), "rb") as src:
                shutil.copyfileobj(src, dst)
            os.chmod(str(backup), 0o600)  # backup nunca herda permissao aberta do original
        if not backup.is_file() or backup.stat().st_size != path.stat().st_size:
            raise OSError("copia de seguranca incompleta")
    except OSError as e:
        try:
            if backup is not None and backup.is_file():
                backup.unlink()
        except OSError:
            pass
        msg = ("Não consegui salvar uma cópia de segurança de {}: {}. "
               "Verifique a permissão da pasta e rode de novo.".format(path, e))
        print("  [ERRO] " + msg)
        raise ConfigBackupError(msg) from e
    return backup


def write_text_atomic(path, texto):
    """Grava por arquivo temporario no mesmo diretorio + os.replace: nunca deixa config.json truncado."""
    destino = os.path.realpath(str(path))
    tmp = "%s.tmp-%d" % (destino, os.getpid())
    try:
        try:
            os.unlink(tmp)  # sobra de execucao interrompida
        except FileNotFoundError:
            pass
        with os.fdopen(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8") as f:
            f.write(texto)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, destino)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def ensure_config():
    """Garante um config.json valido; nunca falha por ele estar ausente ou corrompido.

    - Ausente: cria o minimo (aproveita tudo o que um setup anterior ja gravou).
    - Corrompido ou nao-objeto: guarda backup config.json.bak-<timestamp> e recria.
    """
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (OSError, ValueError, RecursionError):
            pass
        backup = backup_config_copy(CONFIG_PATH)  # ConfigBackupError: original fica intacto
        print("  [aviso] config.json invalido — backup em {}".format(backup.name))
    config = _minimal_config()
    write_text_atomic(CONFIG_PATH, json.dumps(config, ensure_ascii=False, indent=2))
    return config


def load_config():
    return ensure_config()


def bump_phase(config, phase):
    """phase_completed nunca regride: grava max(atual, phase)."""
    valor = config.get("phase_completed", 0)
    atual = 0
    if not isinstance(valor, bool):
        try:
            atual = float(valor)
        except OverflowError:
            atual = float("inf") if valor > 0 else 0.0  # inteiro gigante: maior que qualquer fase, nunca sobrescreve
        except (TypeError, ValueError):
            # formato antigo em texto (ex.: "week5", "semana 5"): usa o numero que aparece nele
            achou = re.search(r"\d+(?:\.\d+)?", str(valor))
            atual = float(achou.group()) if achou else 0
        if atual != atual or atual == float("-inf"):
            atual = 0
    if phase > atual:  # nunca reduz o valor existente (nem reescreve se ja for >= phase)
        config["phase_completed"] = phase
    return config


def save_config(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(CONFIG_PATH, json.dumps(config, ensure_ascii=False, indent=2))


def load_checkpoint():
    if not CHECKPOINT_PATH.exists():
        return {"steps": {}, "updated_at": None}
    try:
        return json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"steps": {}, "updated_at": None}


def save_checkpoint(checkpoint):
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    checkpoint["updated_at"] = now_iso()
    CHECKPOINT_PATH.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8")


def mark_checkpoint(step, status, detail=""):
    checkpoint = load_checkpoint()
    checkpoint.setdefault("steps", {})
    checkpoint["steps"][step] = {
        "status": status,
        "detail": detail,
        "updated_at": now_iso(),
    }
    save_checkpoint(checkpoint)


def load_profile():
    if not PROSPECTING_PROFILE_PATH.exists():
        return {}
    try:
        return json.loads(PROSPECTING_PROFILE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_profile(profile):
    PROSPECTING_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROSPECTING_PROFILE_PATH.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def open_in_browser(filepath):
    """Abre arquivo no browser de forma cross-platform."""
    import subprocess
    path_str = str(filepath)
    if PLATFORM == "Darwin":
        subprocess.run(["open", path_str])
    elif PLATFORM == "Windows":
        subprocess.run(["start", path_str], shell=True)
    else:
        subprocess.run(["xdg-open", path_str])


def mask_phone(phone):
    """Mascara telefone: 5585***689"""
    if len(phone) >= 10:
        return phone[:4] + "***" + phone[-3:]
    return phone


def latest_heartbeat_snapshot():
    snapshots = {}
    for layer_name in ["watchdog", "heartbeat", "last_resort"]:
        path = HEARTBEAT_DIR / f"{layer_name}.json"
        if not path.exists():
            snapshots[layer_name] = None
            continue
        try:
            snapshots[layer_name] = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            snapshots[layer_name] = None
    return snapshots

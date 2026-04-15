#!/usr/bin/env python3
"""
Utilitarios compartilhados da Semana 2 — ZX Control.
Adaptado de week2_lib.py da Semana 1.
"""

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path.home() / ".operacao-ia"
CONFIG_PATH = BASE_DIR / "config" / "config.json"
CHECKPOINT_PATH = BASE_DIR / "config" / "week2_checkpoint.json"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
SCRIPTS_DIR = BASE_DIR / "scripts"
MISSION_CONTROL_DIR = BASE_DIR / "mission-control"
HEARTBEAT_DIR = LOGS_DIR / "heartbeat"


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def ensure_structure():
    for path in [DATA_DIR, LOGS_DIR, SCRIPTS_DIR, MISSION_CONTROL_DIR, HEARTBEAT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError("config.json nao encontrado em ~/.operacao-ia/config/")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


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

#!/usr/bin/env python3
"""
Etapa 3 — Verificar e configurar canais de disparo: WhatsApp (Evolution API)
e Email (Resend) + instalar rate limiter.
ZX Control Semana 3
"""

import getpass
import json
import shutil
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))
from lib import (
    CONFIG_PATH,
    PLATFORM,
    RATE_LIMITS_PATH,
    SCRIPTS_DIR,
    ensure_structure,
    load_config,
    mark_checkpoint,
    now_iso,
    save_config,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def progress_bar():
    print("\n[███░░░░░░░] Etapa 3 de 9 — Configurar Canais de Disparo\n")


def ask(prompt, default=None):
    if default:
        answer = input(f"{prompt} [{default}]: ").strip()
        return answer or default
    answer = input(f"{prompt}: ").strip()
    return answer


def _get(url, headers=None):
    """GET request; retorna (status_code, body_dict)."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode())
            return resp.status, body
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode())
        except Exception:
            body = {}
        return e.code, body
    except Exception as e:
        return None, {"error": str(e)}


# ---------------------------------------------------------------------------
# WhatsApp — Evolution API
# ---------------------------------------------------------------------------

def test_evolution(url, key):
    """Testa conexao com Evolution API. Retorna True se 200."""
    url = url.rstrip("/")
    status, body = _get(
        f"{url}/instance/fetchInstances",
        headers={"apikey": key},
    )
    return status == 200, body


def setup_whatsapp(config):
    print("--- WhatsApp (Evolution API) ---\n")

    url = config.get("evolution_api_url", "")
    key = config.get("evolution_api_key", "")

    if url and key:
        print(f"  Credenciais ja encontradas no config.json.")
        print(f"  URL: {url}")
        print(f"  Key: ***{key[-4:]}")
        print("  Testando conexao...")
        ok, body = test_evolution(url, key)
        if ok:
            print("  WhatsApp conectado!\n")
            return config
        else:
            print(f"  Falha na conexao: {body}")
            reconfig = ask("  Deseja reconfigurar? (s/n)", "s").lower()
            if reconfig != "s":
                print("  Mantendo configuracao atual.\n")
                return config
    else:
        print("  Credenciais da Evolution API nao encontradas.\n")
        print("  Voce precisa de uma instancia da Evolution API rodando.")
        print("  Exemplo de URL: http://localhost:8080 ou https://sua-api.com\n")

    # Coletar dados
    while True:
        url = ask("  URL da Evolution API (ex: http://localhost:8080)").rstrip("/")
        key = getpass.getpass("  API Key da Evolution API (oculto): ").strip()

        if not url or not key:
            print("  URL e Key sao obrigatorios.")
            continue

        print("  Testando conexao...")
        ok, body = test_evolution(url, key)
        if ok:
            print("  WhatsApp conectado!\n")
            config["evolution_api_url"] = url
            config["evolution_api_key"] = key
            return config
        else:
            print(f"  Falha na conexao: {body}")
            retry = ask("  Tentar novamente? (s/n)", "s").lower()
            if retry != "s":
                print("  Pulando configuracao do WhatsApp.\n")
                return config


# ---------------------------------------------------------------------------
# Email — Resend
# ---------------------------------------------------------------------------

def test_resend(key):
    """Testa conexao com Resend. Retorna True se 200."""
    status, body = _get(
        "https://api.resend.com/domains",
        headers={"Authorization": f"Bearer {key}"},
    )
    return status == 200, body


def setup_email(config):
    print("--- Email (Resend) ---\n")

    key = config.get("resend_api_key", "")

    if key:
        print(f"  Chave Resend ja encontrada no config.json (***{key[-4:]})")
        print("  Testando conexao...")
        ok, body = test_resend(key)
        if ok:
            print("  Email conectado!\n")
            return config
        else:
            print(f"  Falha na conexao: {body}")
            reconfig = ask("  Deseja reconfigurar? (s/n)", "s").lower()
            if reconfig != "s":
                print("  Mantendo configuracao atual.\n")
                return config
    else:
        print("  Chave Resend nao encontrada.\n")
        print("  Crie sua conta gratuita em https://resend.com")
        print("  Va em API Keys > Create API Key\n")

    # Coletar dados
    while True:
        key = getpass.getpass("  Cole sua Resend API Key (oculto): ").strip()

        if not key:
            print("  A chave nao pode ser vazia.")
            continue

        print("  Testando conexao...")
        ok, body = test_resend(key)
        if ok:
            print("  Email conectado!\n")
            config["resend_api_key"] = key
            return config
        else:
            print(f"  Falha na conexao: {body}")
            retry = ask("  Tentar novamente? (s/n)", "s").lower()
            if retry != "s":
                print("  Pulando configuracao do Email.\n")
                return config


# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------

def install_rate_limiter():
    print("--- Rate Limiter ---\n")

    # Copiar script
    src = ROOT_DIR / "scripts" / "rate_limiter.py"
    if src.exists():
        SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        dest = SCRIPTS_DIR / "rate_limiter.py"
        shutil.copy2(src, dest)
        print(f"  rate_limiter.py copiado para {dest}")
    else:
        print("  [aviso] scripts/rate_limiter.py nao encontrado — pulando copia.")

    # Criar rate_limits.json inicial se nao existir
    RATE_LIMITS_PATH.parent.mkdir(parents=True, exist_ok=True)

    if RATE_LIMITS_PATH.exists():
        print(f"  rate_limits.json ja existe em {RATE_LIMITS_PATH}")
    else:
        today_iso = now_iso()
        rate_limits = {
            "whatsapp": {
                "daily_limit": 30,
                "interval_min": 60,
                "interval_max": 120,
                "sent_today": 0,
                "last_reset": today_iso,
            },
            "email": {
                "daily_limit": 200,
                "interval_min": 15,
                "interval_max": 30,
                "sent_today": 0,
                "last_reset": today_iso,
            },
        }
        RATE_LIMITS_PATH.write_text(
            json.dumps(rate_limits, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  rate_limits.json criado em {RATE_LIMITS_PATH}")

    print("  Limites configurados:")
    print("    WhatsApp : 30 msgs/dia | intervalo 60-120s")
    print("    Email    : 200 msgs/dia | intervalo 15-30s\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    progress_bar()

    ensure_structure()

    # Carregar config existente
    try:
        config = load_config()
    except FileNotFoundError:
        config = {}

    # Configurar canais
    config = setup_whatsapp(config)
    config = setup_email(config)

    # Salvar config atualizado
    save_config(config)
    print("  config.json atualizado.\n")

    # Instalar rate limiter
    install_rate_limiter()

    # Checkpoint
    has_wpp = bool(config.get("evolution_api_url") and config.get("evolution_api_key"))
    has_email = bool(config.get("resend_api_key"))
    detail = f"whatsapp={'ok' if has_wpp else 'skip'} email={'ok' if has_email else 'skip'}"
    mark_checkpoint("step_3_channels", "done", detail)

    print("[OK] Etapa 3 concluida — Canais de disparo configurados!\n")


if __name__ == "__main__":
    main()

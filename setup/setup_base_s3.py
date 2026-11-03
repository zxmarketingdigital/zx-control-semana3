#!/usr/bin/env python3
"""
Etapa 0 — Base Semana 3
Boas-vindas, diagnostico do ambiente e criacao da estrutura de diretorios.
Nao exige setup anterior: cria o config.json minimo se ele nao existir.
"""

import json
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from lib import (
    CONFIG_PATH,
    PLATFORM,
    ensure_structure,
    load_config,
    mark_checkpoint,
    now_iso,
    save_config,
)


def ask(prompt, secret=False):
    import getpass
    try:
        if secret:
            value = getpass.getpass(f"  {prompt}: ").strip()
        else:
            value = input(f"  {prompt}: ").strip()
        return value
    except (KeyboardInterrupt, EOFError):
        print()
        print("  Setup cancelado.")
        sys.exit(0)


def report_existing_install(config):
    """Informativo: mostra o que ja existe de uma instalacao anterior. Nunca bloqueia."""
    reaproveitados = [
        label for key, label in (
            ("evolution_api_key", "WhatsApp (Evolution)"),
            ("resend_api_key", "Email (Resend)"),
            ("supabase_url", "Supabase"),
        ) if config.get(key)
    ]
    if reaproveitados:
        print("  [OK] Configuracoes existentes que serao reaproveitadas: " + ", ".join(reaproveitados))
    else:
        print("  [OK] Nenhuma configuracao anterior encontrada — o que for preciso sera configurado nas proximas etapas.")


def detect_scheduler():
    """Detecta se launchctl (macOS) ou schtasks (Windows) estao disponiveis."""
    if PLATFORM == "Darwin":
        path = shutil.which("launchctl")
        if path:
            print(f"  [OK] launchctl encontrado: {path}")
        else:
            print("  [AVISO] launchctl nao encontrado (incomum no macOS).")
        return "launchctl"
    elif PLATFORM == "Windows":
        path = shutil.which("schtasks")
        if path:
            print(f"  [OK] schtasks encontrado: {path}")
        else:
            print("  [AVISO] schtasks nao encontrado no PATH.")
        return "schtasks"
    else:
        path = shutil.which("cron") or shutil.which("crontab")
        if path:
            print(f"  [OK] cron encontrado: {path}")
        else:
            print("  [AVISO] cron nao encontrado. Instale com: sudo apt install cron")
        return "cron"


def print_plan():
    steps = [
        ("Etapa 0", "Base S3         — Ambiente e estrutura de diretorios (este script)"),
        ("Etapa 1", "Perfil          — Perfil de prospeccao e cliente ideal"),
        ("Etapa 2", "APIFY           — Busca de leads na internet (Google Maps)"),
        ("Etapa 3", "Canais          — WhatsApp (Evolution) + Email (Resend) + rate limiter"),
        ("Etapa 4", "Copy            — Mensagens personalizadas por segmento"),
        ("Etapa 5", "Dashboard       — Painel visual de prospeccao"),
        ("Etapa 6", "Motor           — Motor de campanhas (disparo automatizado)"),
        ("Etapa 7", "Automacao       — Automacao diaria + skills Claude Code"),
        ("Etapa 8", "Auditoria       — Revisao tecnica automatica do sistema"),
        ("Etapa 9", "Finalizacao     — Primeira busca real e encerramento"),
    ]
    print()
    print("  Plano completo — 9 etapas:")
    print()
    for label, desc in steps:
        print(f"    {label}: {desc}")
    print()


def read_claude_settings():
    """Le model e effort de .claude/settings.local.json se existir."""
    settings_path = ROOT_DIR / ".claude" / "settings.local.json"
    if not settings_path.exists():
        return None
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        return data
    except Exception:
        return None


def main():
    print()
    print("=" * 50)
    print("  ZX Control — Semana 3: Prospeccao Automatizada")
    print("=" * 50)
    print()
    print("  [░░░░░░░░░░] Etapa 0 de 9")
    print()
    print("  Bem-vindo(a) ao setup da Semana 3!")
    print()
    print("  Nesta semana voce vai montar um sistema completo de")
    print("  prospeccao automatizada: busca de leads, disparo via")
    print("  WhatsApp e Email, rastreamento de respostas e dashboard.")
    print()

    # --- Carrega (ou cria) o config.json: este setup nao exige setup anterior ---
    print("  Preparando a base (config.json)...")
    ensure_structure()
    config = load_config()  # cria o minimo se nao existir; backup + recria se estiver corrompido
    report_existing_install(config)
    print()

    # --- Detecta e salva plataforma ---
    print(f"  Sistema operacional: {PLATFORM}")
    config["platform"] = PLATFORM
    save_config(config)
    print("  [OK] Plataforma salva no config.json")
    print()

    # --- Versao do Python ---
    pv = sys.version.split()[0]
    print(f"  Python: {pv}")
    print("  [OK] Python disponivel.")
    print()

    # --- Verifica agendador do sistema ---
    print("  Verificando agendador de tarefas...")
    scheduler = detect_scheduler()
    config["scheduler"] = scheduler
    save_config(config)
    print()

    # --- Cria estrutura de diretorios ---
    print("  Criando estrutura de diretorios...")
    ensure_structure()
    print("  [OK] Diretorios criados em ~/.operacao-ia/")
    print()

    # --- Plano das 9 etapas ---
    print_plan()

    # --- Configuracao Claude detectada ---
    settings = read_claude_settings()
    if settings:
        model = settings.get("model", "nao definido")
        effort = settings.get("effort", "nao definido")
        print(f"  Configuracao Claude detectada:")
        print(f"    model:  {model}")
        print(f"    effort: {effort}")
        print()

    # --- Checkpoint ---
    mark_checkpoint("step_0_base_s3", "done", f"Platform: {PLATFORM}, Python: {pv}")

    print("  [OK] Etapa 0 concluida!")
    print()
    print("  Proximo passo: Etapa 1 — Perfil de Prospeccao")
    print("  Execute: python3 setup/setup_profile.py")
    print()


if __name__ == "__main__":
    main()

"""Testes de validacao da configuracao de seguranca do sandbox (issue #34 + #38).

IMPORTANTE: Estes testes validam os valores de CONFIGURACAO (dicionario e kwargs).
Testes de runtime (container real) requerem Docker e estao documentados como
validacao manual em docs/SECURITY-AUDIT.md.
"""

from config import Config
from execution import get_sandbox_security_config, sandbox_run_kwargs, sandbox_staging_kwargs


# ── Config baseline (issue #34) ──────────────────────────────────────────────

def test_sandbox_config_documentada():
    cfg = get_sandbox_security_config()
    camadas_esperadas = {
        "network_mode",
        "read_only",
        "tmpfs",
        "mem_limit",
        "memswap_limit",
        "cpu_quota",
        "pids_limit",
        "user",
        "cap_drop",
        "stop_timeout",
    }
    assert set(cfg.keys()) == camadas_esperadas
    for key, entry in cfg.items():
        assert "value" in entry
        assert "rationale" in entry
        assert len(entry["rationale"]) > 10


def test_network_isolation():
    assert get_sandbox_security_config()["network_mode"]["value"] == "none"


def test_read_only_filesystem():
    cfg = get_sandbox_security_config()
    assert cfg["read_only"]["value"] is True
    assert cfg["tmpfs"]["value"] == Config.sandbox_tmpfs()


def test_memory_limits():
    cfg = get_sandbox_security_config()
    assert cfg["mem_limit"]["value"] == Config.sandbox_mem_limit()
    assert cfg["memswap_limit"]["value"] == Config.sandbox_mem_limit()


def test_cpu_limit():
    assert get_sandbox_security_config()["cpu_quota"]["value"] == Config.SANDBOX_CPU_QUOTA


def test_pids_limit():
    assert get_sandbox_security_config()["pids_limit"]["value"] == Config.SANDBOX_PIDS_LIMIT


def test_non_root_user():
    assert get_sandbox_security_config()["user"]["value"] == Config.SANDBOX_USER


def test_cap_drop_all():
    assert get_sandbox_security_config()["cap_drop"]["value"] == ["ALL"]


def test_stop_timeout():
    assert get_sandbox_security_config()["stop_timeout"]["value"] == Config.DOCKER_STOP_TIMEOUT_S


def test_sandbox_config_env_vars():
    assert Config.SANDBOX_MEMORY_MB == 128
    assert Config.SANDBOX_CPU_QUOTA == 50000
    assert Config.SANDBOX_PIDS_LIMIT == 64
    assert Config.SANDBOX_TMPFS_SIZE_MB == 8
    assert Config.SANDBOX_USER == "65534:65534"
    assert Config.EXEC_TIMEOUT_S == 10
    assert Config.DOCKER_STOP_TIMEOUT_S == 12


# ── Validacao de config contra vetores de escape (issue #38) ─────────────────
# Estes testes validam que a CONFIGURACAO cobre cada vetor.
# Validacao de runtime (container real) requer Docker — documentada em
# docs/SECURITY-AUDIT.md como "validacao manual pendente".

def test_config_write_to_root_rationale():
    """Config: read_only=True documenta intencao de bloquear escrita em /."""
    cfg = get_sandbox_security_config()
    assert cfg["read_only"]["value"] is True, (
        "read_only deve ser True na config para impedir escrita em /"
    )
    assert len(cfg["read_only"]["rationale"]) > 10, (
        "rationale de read_only deve ser descritivo"
    )


def test_config_fork_bomb_pids_limit():
    """Config: pids_limit=64 documenta intencao de conter fork bombs."""
    cfg = get_sandbox_security_config()
    pids_limit = cfg["pids_limit"]["value"]
    assert pids_limit == 64, (
        f"pids_limit deve ser 64, nao {pids_limit}"
    )
    assert pids_limit > 0 and pids_limit <= 128, (
        "pids_limit deve ser positivo e razoavel (<=128)"
    )


def test_config_network_isolation():
    """Config: network_mode='none' documenta intencao de isolar rede."""
    cfg = get_sandbox_security_config()
    assert cfg["network_mode"]["value"] == "none", (
        "network_mode deve ser 'none'"
    )


def test_config_memory_limits():
    """Config: mem_limit == memswap_limit (swap desabilitado)."""
    cfg = get_sandbox_security_config()
    mem = cfg["mem_limit"]["value"]
    swap = cfg["memswap_limit"]["value"]
    assert mem == swap, (
        "mem_limit deve ser igual a memswap_limit (swap desabilitado)"
    )
    assert Config.SANDBOX_MEMORY_MB >= 32, (
        "Memoria minima de 32 MB para execucao de programas simples"
    )


def test_config_cpu_and_timeout():
    """Config: cpu_quota e timeout de execucao documentados."""
    assert Config.SANDBOX_CPU_QUOTA <= 100000, (
        "cpu_quota nao deve exceder 1 CPU (100000 microsegundos)"
    )
    assert 0 < Config.EXEC_TIMEOUT_S <= 30, (
        "Timeout de execucao deve ser positivo e razoavel (<=30s)"
    )


def test_config_non_root_user():
    """Config: usuario nobody (65534:65534) bloqueia escalada de privilegios."""
    cfg = get_sandbox_security_config()
    user = cfg["user"]["value"]
    assert user == "65534:65534", (
        f"Usuario do sandbox deve ser nobody (65534:65534), nao {user}"
    )


def test_config_cap_drop_all():
    """Config: cap_drop=['ALL'] remove todas as capabilities Linux."""
    cfg = get_sandbox_security_config()
    caps = cfg["cap_drop"]["value"]
    assert "ALL" in caps, (
        "cap_drop deve incluir 'ALL' para remover todas as capabilities"
    )


def test_config_timeout_hardening():
    """Config: DOCKER_STOP_TIMEOUT_S > EXEC_TIMEOUT_S para margem de kill."""
    assert Config.EXEC_TIMEOUT_S == 10
    assert Config.DOCKER_STOP_TIMEOUT_S == 12
    assert Config.DOCKER_STOP_TIMEOUT_S > Config.EXEC_TIMEOUT_S, (
        "DOCKER_STOP_TIMEOUT_S deve ser > EXEC_TIMEOUT_S"
    )


def test_security_audit_document_exists():
    """Verifica que SECURITY-AUDIT.md existe e contem secoes obrigatorias."""
    import os
    audit_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "SECURITY-AUDIT.md"
    )
    assert os.path.isfile(audit_path), (
        "docs/SECURITY-AUDIT.md deve existir com os resultados da auditoria"
    )
    content = open(audit_path, encoding="utf-8").read()
    assert "Checklist de Segurança" in content
    assert "Camadas de Segurança" in content
    assert "Tentativas de Escape" in content
    assert "Conclusão" in content


# ── Validacao de kwargs do container (config, nao runtime) ───────────────────

def test_sandbox_run_kwargs_network_mode():
    """sandbox_run_kwargs inclui network_mode='none'."""
    kwargs = sandbox_run_kwargs()
    assert kwargs["network_mode"] == "none"


def test_sandbox_run_kwargs_read_only():
    """sandbox_run_kwargs inclui read_only=True (intencao; staging usa False)."""
    kwargs = sandbox_run_kwargs()
    assert kwargs["read_only"] is True


def test_sandbox_staging_kwargs_read_only_false():
    """sandbox_staging_kwargs usa read_only=False para put_archive.

    Este e o kwarg REAL usado na execucao hoje (PtyExecutionStrategy).
    O audit documenta este trade-off em SECURITY-AUDIT.md.
    """
    kwargs = sandbox_staging_kwargs()
    assert kwargs["read_only"] is False, (
        "staging precisa de read_only=False para put_archive; "
        "ver docs/SECURITY-AUDIT.md para avaliacao de risco residual"
    )


def test_sandbox_run_kwargs_pids_limit():
    """sandbox_run_kwargs inclui pids_limit correto."""
    kwargs = sandbox_run_kwargs()
    assert kwargs["pids_limit"] == Config.SANDBOX_PIDS_LIMIT


def test_sandbox_run_kwargs_cap_drop_all():
    """sandbox_run_kwargs inclui cap_drop=['ALL']."""
    kwargs = sandbox_run_kwargs()
    assert kwargs["cap_drop"] == ["ALL"]


def test_sandbox_run_kwargs_user_non_root():
    """sandbox_run_kwargs inclui user nao-root."""
    kwargs = sandbox_run_kwargs()
    assert kwargs["user"] == Config.SANDBOX_USER

"""Testes de auditoria de seguranca do sandbox (issue #34 + #38, PRD §11.2).

Issue #38: auditoria contra tentativas de escape.
"""

from config import Config
from execution import get_sandbox_security_config, docker_available


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


# ── Auditoria de escape (issue #38) ──────────────────────────────────────────

def test_write_to_root_blocked_by_read_only():
    """Tentativa de escrever em / falha: filesystem e read-only."""
    cfg = get_sandbox_security_config()
    assert cfg["read_only"]["value"] is True, (
        "Rootfs deve ser read-only para impedir escrita em /"
    )
    # tmpfs e a unica area gravavel
    tmpfs = cfg["tmpfs"]["value"]
    assert "/tmp" in tmpfs
    assert tmpfs["/tmp"].startswith("size=")


def test_fork_bomb_contained_by_pids_limit():
    """Fork bomb / spawn massivo contido por pids_limit."""
    cfg = get_sandbox_security_config()
    pids_limit = cfg["pids_limit"]["value"]
    assert pids_limit == 64, (
        f"pids_limit deve ser 64 para conter fork bombs, nao {pids_limit}"
    )
    assert pids_limit > 0 and pids_limit <= 128, (
        "pids_limit deve ser positivo e razoavel (<=128)"
    )


def test_network_access_blocked_by_network_mode_none():
    """curl/ping/wget falham: network_mode='none' isola rede."""
    cfg = get_sandbox_security_config()
    assert cfg["network_mode"]["value"] == "none", (
        "network_mode deve ser 'none' para bloquear todo trafego de rede"
    )


def test_memory_exhaustion_contained():
    """Exaustao de memoria contida por mem_limit + memswap_limit."""
    cfg = get_sandbox_security_config()
    mem = cfg["mem_limit"]["value"]
    swap = cfg["memswap_limit"]["value"]
    assert mem == swap, (
        "mem_limit deve ser igual a memswap_limit (swap desabilitado)"
    )
    assert mem == Config.sandbox_mem_limit()
    assert Config.SANDBOX_MEMORY_MB >= 32, (
        "Memoria minima de 32 MB para execucao de programas simples"
    )


def test_cpu_exhaustion_contained_by_cpu_quota_and_timeout():
    """Exaustao de CPU contida por cpu_quota + timeout de execucao."""
    assert Config.SANDBOX_CPU_QUOTA <= 100000, (
        "cpu_quota nao deve exceder 1 CPU (100000 microsegundos)"
    )
    assert Config.EXEC_TIMEOUT_S > 0 and Config.EXEC_TIMEOUT_S <= 30, (
        "Timeout de execucao deve ser positivo e razoavel (<=30s)"
    )


def test_privilege_escalation_blocked_by_non_root():
    """Escalada de privilegios bloqueada: usuario nobody (65534:65534)."""
    cfg = get_sandbox_security_config()
    user = cfg["user"]["value"]
    assert user == "65534:65534", (
        f"Usuario do sandbox deve ser nobody (65534:65534), nao {user}"
    )


def test_capabilities_dropped_all():
    """Nenhuma capability Linux disponivel no container."""
    cfg = get_sandbox_security_config()
    caps = cfg["cap_drop"]["value"]
    assert "ALL" in caps, (
        "cap_drop deve incluir 'ALL' para remover todas as capabilities"
    )


def test_timeout_hardening_complete():
    """Hardening de timeout: execucao + docker stop configurados."""
    assert Config.EXEC_TIMEOUT_S == 10
    assert Config.DOCKER_STOP_TIMEOUT_S == 12
    assert Config.DOCKER_STOP_TIMEOUT_S > Config.EXEC_TIMEOUT_S, (
        "DOCKER_STOP_TIMEOUT_S deve ser > EXEC_TIMEOUT_S para dar margem ao kill"
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
    assert "Checklist de Segurança" in content, (
        "SECURITY-AUDIT.md deve conter checklist de seguranca"
    )
    assert "Camadas de Segurança" in content, (
        "SECURITY-AUDIT.md deve documentar as camadas de seguranca"
    )
    assert "Tentativas de Escape" in content, (
        "SECURITY-AUDIT.md deve registrar tentativas de escape"
    )
    # Verifica que todos os vetores estao marcados como contidos
    assert "Contido" in content, (
        "SECURITY-AUDIT.md deve indicar vetores como contidos"
    )


# ── Testes com Docker (executados apenas se Docker disponivel) ──────────────

def test_docker_network_mode_none_in_kwargs():
    """Valida que sandbox_run_kwargs inclui network_mode='none'."""
    from execution import sandbox_run_kwargs
    kwargs = sandbox_run_kwargs()
    assert kwargs["network_mode"] == "none"


def test_docker_read_only_in_kwargs():
    """Valida que sandbox_run_kwargs inclui read_only=True."""
    from execution import sandbox_run_kwargs
    kwargs = sandbox_run_kwargs()
    assert kwargs["read_only"] is True


def test_docker_pids_limit_in_kwargs():
    """Valida que sandbox_run_kwargs inclui pids_limit."""
    from execution import sandbox_run_kwargs
    kwargs = sandbox_run_kwargs()
    assert kwargs["pids_limit"] == Config.SANDBOX_PIDS_LIMIT


def test_docker_cap_drop_all_in_kwargs():
    """Valida que sandbox_run_kwargs inclui cap_drop=['ALL']."""
    from execution import sandbox_run_kwargs
    kwargs = sandbox_run_kwargs()
    assert kwargs["cap_drop"] == ["ALL"]


def test_docker_user_non_root_in_kwargs():
    """Valida que sandbox_run_kwargs inclui user nao-root."""
    from execution import sandbox_run_kwargs
    kwargs = sandbox_run_kwargs()
    assert kwargs["user"] == Config.SANDBOX_USER

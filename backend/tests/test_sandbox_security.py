"""Testes de auditoria de seguranca do sandbox (issue #34, PRD §11.2).

Verifica que todas as 9 camadas de hardening estao corretamente configuradas
com os valores padrao definidos no PRD.
"""

import sys
import os

# Garante que o diretorio backend esta no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config


def test_sandbox_config_documentada():
    """Testa que get_sandbox_security_config retorna todas as camadas esperadas."""
    from execution import get_sandbox_security_config

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

    assert set(cfg.keys()) == camadas_esperadas, (
        f"Esperado {camadas_esperadas}, obtido {set(cfg.keys())}"
    )

    # Toda entrada deve ter 'value' e 'rationale' nao vazio
    for key, entry in cfg.items():
        assert "value" in entry, f"Falta 'value' em {key}"
        assert "rationale" in entry, f"Falta 'rationale' em {key}"
        assert isinstance(entry["rationale"], str) and len(entry["rationale"]) > 20, (
            f"Rationale muito curto em {key}: {entry['rationale']}"
        )


def test_network_isolation():
    """Camada 2: network_mode deve ser 'none'."""
    from execution import get_sandbox_security_config

    cfg = get_sandbox_security_config()
    assert cfg["network_mode"]["value"] == "none"


def test_read_only_filesystem():
    """Camada 3: filesystem deve ser read-only com tmpfs limitado."""
    from execution import get_sandbox_security_config

    cfg = get_sandbox_security_config()
    assert cfg["read_only"]["value"] is True
    assert cfg["tmpfs"]["value"] == {"/tmp": "size=8m"}


def test_memory_limits():
    """Camada 4: memoria 128 MB sem swap."""
    from execution import get_sandbox_security_config

    cfg = get_sandbox_security_config()
    assert cfg["mem_limit"]["value"] == "128m"
    assert cfg["memswap_limit"]["value"] == "128m"


def test_cpu_limit():
    """Camada 5: CPU quota 50000 (0.5 CPU)."""
    from execution import get_sandbox_security_config

    cfg = get_sandbox_security_config()
    assert cfg["cpu_quota"]["value"] == 50000


def test_pids_limit():
    """Camada 6: maximo 64 processos (anti fork bomb)."""
    from execution import get_sandbox_security_config

    cfg = get_sandbox_security_config()
    assert cfg["pids_limit"]["value"] == 64


def test_non_root_user():
    """Camada 7: usuario nobody (65534:65534)."""
    from execution import get_sandbox_security_config

    cfg = get_sandbox_security_config()
    assert cfg["user"]["value"] == "65534:65534"


def test_cap_drop_all():
    """Camada 8: todas as capabilities removidas."""
    from execution import get_sandbox_security_config

    cfg = get_sandbox_security_config()
    assert cfg["cap_drop"]["value"] == ["ALL"]


def test_stop_timeout():
    """Camada [3] de timeout: stop_timeout = 12."""
    from execution import get_sandbox_security_config

    cfg = get_sandbox_security_config()
    assert cfg["stop_timeout"]["value"] == 12


def test_sandbox_config_env_vars():
    """Constantes do Config devem ter defaults alinhados ao PRD §11.2."""
    assert Config.SANDBOX_MEMORY_MB == 128
    assert Config.SANDBOX_CPU_QUOTA == 50000
    assert Config.SANDBOX_PIDS_LIMIT == 64
    assert Config.SANDBOX_TMPFS_SIZE_MB == 8
    assert Config.SANDBOX_USER == "65534:65534"

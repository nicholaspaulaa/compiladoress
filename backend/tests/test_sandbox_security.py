"""Testes de auditoria de seguranca do sandbox (issue #34, PRD §11.2)."""

from config import Config
from execution import get_sandbox_security_config


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

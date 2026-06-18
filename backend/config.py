import os
from pathlib import Path


def _load_dotenv() -> None:
    """Carrega repo/.env no dev local (nao sobrescreve vars ja definidas)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()


class Config:
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "").strip()
    SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "").strip()
    COMPILE_TIMEOUT_S = int(os.environ.get("COMPILE_TIMEOUT_S", "15"))
    EXEC_TIMEOUT_S = int(os.environ.get("EXEC_TIMEOUT_S", "10"))
    DOCKER_STOP_TIMEOUT_S = int(os.environ.get("DOCKER_STOP_TIMEOUT_S", "12"))
    DOCKER_API_TIMEOUT_S = int(os.environ.get("DOCKER_API_TIMEOUT_S", "120"))
    MAX_CODE_KB = int(os.environ.get("MAX_CODE_KB", "64"))

    SANDBOX_IMAGE = os.environ.get("SANDBOX_IMAGE", "simples-runner:latest")
    SANDBOX_MEMORY_MB = int(os.environ.get("SANDBOX_MEMORY_MB", "128"))
    SANDBOX_CPU_QUOTA = int(os.environ.get("SANDBOX_CPU_QUOTA", "50000"))
    SANDBOX_PIDS_LIMIT = int(os.environ.get("SANDBOX_PIDS_LIMIT", "64"))
    SANDBOX_TMPFS_SIZE_MB = int(os.environ.get("SANDBOX_TMPFS_SIZE_MB", "8"))
    SANDBOX_USER = os.environ.get("SANDBOX_USER", "65534:65534")
    SANDBOX_WORK_DIR = os.environ.get("SANDBOX_WORK_DIR", "").strip()

    @classmethod
    def supabase_configured(cls) -> bool:
        return bool(cls.SUPABASE_URL and cls.SUPABASE_ANON_KEY and cls.SUPABASE_JWT_SECRET)

    @classmethod
    def max_code_bytes(cls) -> int:
        return cls.MAX_CODE_KB * 1024

    @classmethod
    def sandbox_mem_limit(cls) -> str:
        return f"{cls.SANDBOX_MEMORY_MB}m"

    @classmethod
    def sandbox_tmpfs(cls) -> dict[str, str]:
        size = f"size={cls.SANDBOX_TMPFS_SIZE_MB}m"
        return {"/tmp": size}

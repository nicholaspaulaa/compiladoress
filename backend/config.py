import os


class Config:
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "").strip()
    SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "").strip()
    COMPILE_TIMEOUT_S = int(os.environ.get("COMPILE_TIMEOUT_S", "15"))
    EXEC_TIMEOUT_S = int(os.environ.get("EXEC_TIMEOUT_S", "10"))
    DOCKER_STOP_TIMEOUT_S = int(os.environ.get("DOCKER_STOP_TIMEOUT_S", "12"))

    SANDBOX_IMAGE = os.environ.get("SANDBOX_IMAGE", "simples-runner:latest")
    SANDBOX_MEMORY_MB = int(os.environ.get("SANDBOX_MEMORY_MB", "128"))
    SANDBOX_CPU_QUOTA = int(os.environ.get("SANDBOX_CPU_QUOTA", "50000"))
    SANDBOX_PIDS_LIMIT = int(os.environ.get("SANDBOX_PIDS_LIMIT", "64"))
    SANDBOX_TMPFS_SIZE_MB = int(os.environ.get("SANDBOX_TMPFS_SIZE_MB", "8"))
    SANDBOX_USER = os.environ.get("SANDBOX_USER", "65534:65534")

    @classmethod
    def supabase_configured(cls) -> bool:
        return bool(cls.SUPABASE_URL and cls.SUPABASE_ANON_KEY and cls.SUPABASE_JWT_SECRET)

    @classmethod
    def sandbox_mem_limit(cls) -> str:
        return f"{cls.SANDBOX_MEMORY_MB}m"

    @classmethod
    def sandbox_tmpfs(cls) -> dict[str, str]:
        return {"/tmp": f"size={cls.SANDBOX_TMPFS_SIZE_MB}m"}

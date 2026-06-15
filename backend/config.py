import os


class Config:
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "").strip()
    SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "").strip()
    COMPILE_TIMEOUT_S = int(os.environ.get("COMPILE_TIMEOUT_S", "15"))

    @classmethod
    def supabase_configured(cls) -> bool:
        return bool(cls.SUPABASE_URL and cls.SUPABASE_ANON_KEY and cls.SUPABASE_JWT_SECRET)
